"""
A set of basic cross-platform OS-level operations that are required to build.

These operations don't require any knowledge of the target being built.

Changes to the system are logged.
"""

import codecs
from collections import namedtuple
from glob import glob
import os
from os.path import join, exists, realpath, expanduser
from pathlib import Path
import pexpect
from queue import Queue, Empty
from sys import exit, stdout, stderr, platform
from subprocess import Popen, PIPE
from shutil import copyfile, rmtree, copytree, move, which
import shlex
import time
import tarfile
from threading import Thread
from urllib.request import Request, urlopen
from zipfile import ZipFile

from buildozer.exceptions import BuildozerCommandException
from buildozer.logger import Logger

LOGGER = Logger()


def checkbin(friendly_name, fn):
    """Find a command on the system path."""
    LOGGER.debug("Search for {0}".format(friendly_name))
    executable_location = which(str(fn))
    if executable_location:
        LOGGER.debug(" -> found at {0}".format(executable_location))
        return realpath(executable_location)
    LOGGER.error("{} not found, please install it.".format(friendly_name))
    exit(1)


def mkdir(dn):
    if exists(dn):
        return
    LOGGER.debug("Create directory {0}".format(dn))
    os.makedirs(dn)


def rmdir(dn):
    if not exists(dn):
        return
    LOGGER.debug("Remove directory and subdirectory {}".format(dn))
    rmtree(dn)


def file_matches(patterns):
    result = []
    for pattern in patterns:
        matches = glob(expanduser(pattern.strip()))
        result.extend(matches)
    return result


def file_exists(path):
    """
    return if file exists.
    Accept a Path instance or path string
    """
    return Path(path).exists()


def file_remove(path):
    """
    Remove target file if present.
    Accept a Path instance or path string.
    """
    path = Path(path)
    if path.exists():
        LOGGER.debug("Removing {0}".format(path))
        path.unlink()


def rename(source, target, cwd="."):
    """Rename a file or directory from source to target.

    If target is an existing directory, move into that directory.

    If target is an existing file, the behaviour is OS-dependent."""

    source = Path(cwd, source)
    target = Path(cwd, target)
    LOGGER.debug("Rename {0} to {1}".format(source, target))
    move(source, target)


def file_copy(source, target, cwd="."):
    """Copy a single file from source to target.

    If target is an existing directory, copy into that directory.

    If target is an existing file, overwrite."""

    source = Path(cwd, source)
    target = Path(cwd, target)
    LOGGER.debug("Copy {0} to {1}".format(source, target))
    copyfile(source, target)


def file_extract(archive, env, cwd="."):
    """
    Extract compressed files.
    Also, run .bin files, in the context of env.

    Accepts path or path strings.
    """
    path = Path(cwd, archive)

    if any(
        str(archive).endswith(extension)
        for extension in (".tgz", ".tar.gz", ".tbz2", ".tar.bz2")
    ):
        LOGGER.debug("Extracting {0} to {1}".format(archive, cwd))
        with tarfile.open(path, "r") as compressed_file:
            compressed_file.extractall(cwd)
        return

    if path.suffix == ".zip":
        LOGGER.debug("Extracting {0} to {1}".format(archive, cwd))
        if platform == "win32":
            # This won't work on Unix/OSX, because Android NDK (for example)
            # relies on non-standard handling of file permissions and symbolic
            # links that Python's zipfile doesn't support.
            # Windows doesn't support them either.
            with ZipFile(path, "r") as compressed_file:
                compressed_file.extractall(cwd)
            return
        else:
            # This won't work on Windows, because there is no unzip command
            # there
            return_code = cmd(
                ["unzip", "-q", join(cwd, archive)], cwd=cwd, env=env
            ).return_code
            if return_code != 0:
                raise BuildozerCommandException(
                    "Unzip gave bad return code: {}".format(return_code))
        return

    if path.suffix == ".bin":
        # To process the bin files for linux and darwin systems
        assert platform in ("darwin", "linux")
        LOGGER.debug("Executing {0}".format(archive))

        cmd(["chmod", "a+x", str(archive)], cwd=cwd, env=env)
        cmd([f"./{archive}"], cwd=cwd, env=env)
        return

    raise ValueError("Unhandled extraction for type {0}".format(archive))


def file_copytree(source, target):
    """
    Move an entire directory tree from source to target.

    If source is a single file, it will copy just the one file, but target
    must be a filename, not directory.
    """
    source = Path(source)
    target = Path(target)

    LOGGER.debug("copy {} to {}".format(source, target))
    if source.is_dir():
        copytree(source, target)
    else:
        copyfile(source, target)


class _StreamReader:
    """
    Allow streams to be read in real-time, with a timeout.

    Works cross-platform, unlike select.
    """

    def __init__(self, stdout_, stderr_):
        self._queue = Queue()
        self._completed_count = 0  # How many streams have been finished.
        for stream, id in [(stdout_, "out"), (stderr_, "err")]:
            t = Thread(target=self._fill_queue, args=(stream, id), daemon=True)
            t.start()

    def _fill_queue(self, stream, id):
        if hasattr(stream, "read1"):
            # Read data straight from buffer so partial lines are sent
            # immediately.
            while not stream.closed:
                data = stream.read1()
                if data:
                    self._queue.put((data, id))
                elif not stream.closed:
                    # Avoid busy looping
                    time.sleep(0.1)
        else:
            # Use line-buffering. Partial lines will not be sent until
            # completed.
            for line in stream:
                self._queue.put((line, id))
        self._queue.put("completed")

    def read(self, timeout=None):
        """
        returns a tuple (stdin_output, stderr_output)
        where one will be None.
        or None if timed out or completed.

        Will block unbounded if timeout is None
        """

        if self._completed_count >= 2:
            return None  # Already completed.

        try:
            while True:  # Repeat if you get a completed.
                item = self._queue.get(block=True, timeout=timeout)
                if item == "completed":
                    self._completed_count += 1
                    if self._completed_count == 2:
                        return None
                    # One stream is complete.
                    # Keep looping until both streams are complete.
                    # Assume if one completes, the other won't block before it
                    # completes, so there is no concern with exceeding the
                    # cumulative timeout when looping.
                else:
                    line, id = item
                    if id == "out":
                        return line, None
                    else:
                        return None, line
        except Empty:
            # Timeout
            return None


CommandResult = namedtuple("CommandResult", "stdout stderr return_code")


def cmd(
    command,
    env,
    cwd=None,
    get_stdout=False,
    get_stderr=False,
    break_on_error=True,
    run_condition=None,
    show_output=None,
    quiet=False,
) -> CommandResult:
    """run a command as a subprocess, with the ability to display progress
    and to abort the process early.

    returns CommandResult which includes stdout text, stderr text,
    and process return code.

    command parameter is a tuple (or iterable collection) of the command and
    then its parameters

    if a run_condition callback is provided, it is polled once per second
    and the subprocess will be terminated if it returns false.

    If show_output is true, stdout and stderr will be echoed.

    If get_stdout or get_stderr are false, they will not be returned.

    If break_on_error is set, an exception will be raised if an error code is
    returned, and details with be logged. Note: On some platforms, a
    termination due to run_condition returning False will result in an
    error code.

    quiet parameter reduces logging; useful to keep passwords in command lines
    out of the log.

    The env parameter is deliberately not optional, to ensure it is considered
    during the migration to use this library. Once completed, it can return
    to having a default of None.

    """

    show_output = LOGGER.log_level > 1 if show_output is None else show_output
    env = os.environ if env is None else env

    # Just in case a path-like is passed as a command or param.
    command = tuple(str(item) for item in command)

    if not quiet:
        LOGGER.debug("Run {0!r} ...".format(" ".join(command)))
        LOGGER.debug("Cwd {}".format(cwd))

    process = Popen(
        command,
        env=env,
        stdout=PIPE,
        stderr=PIPE,
        close_fds=True,
        cwd=cwd,
    )

    reader = _StreamReader(process.stdout, process.stderr)

    ret_stdout = [] if get_stdout else None
    ret_stderr = [] if get_stderr else None
    while True:
        item = reader.read(timeout=1)
        if item:
            stdout_line, stderr_line = item
            if stdout_line:
                if get_stdout:
                    ret_stdout.append(stdout_line)
                if show_output:
                    stdout.write(stdout_line.decode("utf-8", "replace"))
                    stdout.flush()
            if stderr_line:
                if get_stderr:
                    ret_stderr.append(stderr_line)
                if show_output:
                    stderr.write(stderr_line.decode("utf-8", "replace"))
                    stderr.flush()
        elif process.poll() is not None:
            # process has completed.
            break
        elif run_condition and not run_condition():
            # time to terminate the process.
            process.terminate()
            # keep looping to get the rest of the output.

    if process.returncode != 0 and break_on_error:
        _command_fail(command, env, process.returncode)

    ret_stdout = b"".join(ret_stdout).decode("utf-8", "ignore") if ret_stdout else None
    ret_stderr = b"".join(ret_stderr).decode("utf-8", "ignore") if ret_stderr else None

    return CommandResult(ret_stdout, ret_stderr, process.returncode)


def _command_fail(command, env, returncode):
    LOGGER.error("Command failed: {0}".format(command))
    LOGGER.error("Error code: {0}".format(returncode))
    LOGGER.log_env(LOGGER.ERROR, env)
    LOGGER.error("")
    LOGGER.error("Buildozer failed to execute the last command")
    if LOGGER.log_level <= LOGGER.INFO:
        LOGGER.error("If the error is not obvious, please raise the log_level to 2")
        LOGGER.error("and retry the latest command.")
    else:
        LOGGER.error("The error might be hidden in the log above this error")
        LOGGER.error("Please read the full log, and search for it before")
        LOGGER.error("raising an issue with buildozer itself.")
    LOGGER.error("In case of a bug report, please add a full log with log_level = 2")
    raise BuildozerCommandException()


def cmd_expect(command, env, **kwargs):
    """
    Launch a subprocess, returning a Pexpect instance that can be
    interacted with.
    """
    # prepare the process
    kwargs.setdefault("show_output", LOGGER.log_level > 1)
    sensible = kwargs.pop("sensible", False)
    show_output = kwargs.pop("show_output")

    if show_output:
        kwargs["logfile"] = codecs.getwriter("utf8")(stdout.buffer)

    if not sensible:
        LOGGER.debug("Run (expect) {0!r}".format(command))
    else:
        LOGGER.debug("Run (expect) {0!r} ...".format(command.split()[0]))

    LOGGER.debug("Cwd {}".format(kwargs.get("cwd")))

    assert platform != "win32", "pexpect.spawn is not available on Windows."
    return pexpect.spawn(shlex.join(command), env=env, encoding="utf-8", **kwargs)


def _report_download_progress(bytes_read, total_size):
    if total_size <= 0:  # Sometimes we don't get told.
        progression = "{0} bytes".format(bytes_read)
    else:
        progression = "{0:.2f}%".format(100.0 * bytes_read / total_size)
    if "CI" not in os.environ:
        # Write over and over on same line.
        stdout.write("- Download {}\r".format(progression))
        stdout.flush()


def download(url, filename, cwd=None):
    """Download the file at url/filename to filename"""
    url = url + str(filename)

    LOGGER.debug("Downloading {0}".format(url))

    if cwd:
        filename = join(cwd, filename)
    file_remove(filename)

    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36"
        },
    )

    with urlopen(request) as response:
        total_size = int(response.headers.get("Content-Length", 0))
        block_size = 1024 * 1024  # 1 MB
        bytes_read = 0

        with open(filename, "wb") as out_file:
            # Read in blocks, so we can give a progress bar.
            while True:
                block = response.read(block_size)
                if not block:
                    break
                out_file.write(block)
                bytes_read += len(block)

                _report_download_progress(bytes_read, total_size)

    return filename
