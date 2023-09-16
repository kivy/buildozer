from os import environ, unlink
from pathlib import Path
import tarfile
from queue import Queue
from sys import executable, platform
import time
from tempfile import TemporaryDirectory
from unittest import TestCase, mock, skipIf
from zipfile import ZipFile

from buildozer.exceptions import BuildozerCommandException
import buildozer.buildops as buildops


class MockStream:
    """Mock a stream instance, similar to stdout.

    Optionally support a `read1()` method (not all streams do).

    Anything written to the instance becomes available to the
    iterator (and read1() if present).
    """

    def __init__(self, support_read1=True):
        self.queue = Queue()
        self.closed = False
        self.buffer = []
        if support_read1:
            self.read1 = self._read1

    def __iter__(self):
        while True:
            data = self._read1()
            if self.closed:
                break
            yield data

    def _read1(self):
        data = self.queue.get()
        if data == "HALT":
            self.closed = True
            return None
        else:
            return data

    def write(self, data):
        assert data != "HALT"
        self.queue.put(str(data))

    def close(self):
        self.queue.put("HALT")


class TestBuildOps(TestCase):
    def test_file_exists(self):
        with TemporaryDirectory() as base_dir:

            nonexistent_path = Path(base_dir) / "newpath"

            # Accepts paths, strings, parts.
            assert not buildops.file_exists(nonexistent_path)
            assert not buildops.file_exists(str(nonexistent_path))

            assert buildops.file_exists(base_dir)

    def test_mkdir_rmdir(self):
        with mock.patch(
            "buildozer.buildops.LOGGER"
        ) as m_logger, TemporaryDirectory() as base_dir:
            new_path = Path(base_dir) / "newpath"

            # No action if path doesn't exist.
            buildops.rmdir(new_path)
            m_logger.debug.assert_not_called()
            m_logger.error.assert_not_called()

            # Create dirs and subdirs.
            buildops.mkdir(new_path / "subpath")
            assert buildops.file_exists(new_path)
            assert buildops.file_exists(new_path / "subpath")
            m_logger.debug.assert_called()
            m_logger.error.assert_not_called()
            m_logger.reset_mock()

            # No action if target exists.
            buildops.mkdir(new_path)
            m_logger.debug.assert_not_called()
            m_logger.error.assert_not_called()
            m_logger.reset_mock()

            # Deletes dirs and subdirs.
            buildops.rmdir(new_path)
            assert not buildops.file_exists(new_path)
            m_logger.debug.assert_called()
            m_logger.error.assert_not_called()
            m_logger.reset_mock()

    def test_file_remove(self):
        with mock.patch(
            "buildozer.buildops.LOGGER"
        ) as m_logger, TemporaryDirectory() as base_dir:
            new_path = Path(base_dir) / "newpath"

            # No action if path doesn't exist.
            buildops.file_remove(new_path)
            m_logger.debug.assert_not_called()
            m_logger.error.assert_not_called()

            with open(new_path, "w") as outfile:
                outfile.write("Temporary content")

            assert buildops.file_exists(new_path)

            # Deletes file
            buildops.file_remove(new_path)
            m_logger.debug.assert_called()
            m_logger.error.assert_not_called()

            assert not buildops.file_exists(new_path)

    def test_rename(self):
        with mock.patch(
            "buildozer.buildops.LOGGER"
        ) as m_logger, TemporaryDirectory() as base_dir:

            old_path = Path(base_dir) / "old"
            new_path = Path(base_dir) / "new"

            with open(old_path, "w") as outfile:
                outfile.write("Temporary content")

            assert buildops.file_exists(old_path)
            assert not buildops.file_exists(new_path)

            # Behaviour of this is dependent on OS. Don't test.
            # buildops.rename(old_path, existing_path)

            with self.assertRaises(FileNotFoundError):
                buildops.rename(new_path, new_path)
            m_logger.debug.assert_called()
            m_logger.error.assert_not_called()
            m_logger.reset_mock()
            assert buildops.file_exists(old_path)
            assert not buildops.file_exists(new_path)

            buildops.rename(old_path, new_path)
            assert not buildops.file_exists(old_path)
            assert buildops.file_exists(new_path)
            m_logger.debug.assert_called()
            m_logger.error.assert_not_called()
            m_logger.reset_mock()

    def test_file_copy(self):
        with mock.patch(
            "buildozer.buildops.LOGGER"
        ) as m_logger, TemporaryDirectory() as base_dir:

            old_path = Path(base_dir) / "old"
            new_path = Path(base_dir) / "new"

            with open(old_path, "w") as outfile:
                outfile.write("Temporary content")

            assert buildops.file_exists(old_path)
            assert not buildops.file_exists(new_path)

            with self.assertRaises(FileNotFoundError):
                buildops.file_copy(new_path, new_path)
            m_logger.debug.assert_called()
            m_logger.error.assert_not_called()
            m_logger.reset_mock()

            buildops.file_copy(old_path, new_path)
            assert buildops.file_exists(old_path)
            assert buildops.file_exists(new_path)
            m_logger.debug.assert_called()
            m_logger.error.assert_not_called()
            m_logger.reset_mock()

            # Do it again, with the file already there...
            buildops.file_copy(old_path, new_path)
            assert buildops.file_exists(old_path)
            assert buildops.file_exists(new_path)
            m_logger.debug.assert_called()
            m_logger.error.assert_not_called()
            m_logger.reset_mock()

    def test_file_copytree(self):
        with mock.patch(
            "buildozer.buildops.LOGGER"
        ) as m_logger, TemporaryDirectory() as base_dir:

            old_path = Path(base_dir) / "old"
            new_path = Path(base_dir) / "new"

            nonexistent_path = Path(base_dir) / "nonexistent"
            with self.assertRaises(FileNotFoundError):
                buildops.file_copytree(nonexistent_path, nonexistent_path)
            m_logger.debug.assert_called()
            m_logger.error.assert_not_called()

            buildops.mkdir(old_path / "subdir" / "subsubdir")

            buildops.file_copytree(old_path, new_path)
            assert buildops.file_exists(new_path / "subdir" / "subsubdir")
            m_logger.debug.assert_called()
            m_logger.error.assert_not_called()
            m_logger.reset_mock()

            single_file = Path(base_dir) / "singlefile.txt"
            with open(single_file, "w") as outfile:
                outfile.write("Temporary content")

            buildops.file_copytree(single_file, new_path / "singlefile2.txt")
            assert buildops.file_exists(new_path / "singlefile2.txt")
            m_logger.debug.assert_called()
            m_logger.error.assert_not_called()
            m_logger.reset_mock()

    def test_extract_file(self):

        with mock.patch(
            "buildozer.buildops.LOGGER"
        ) as m_logger, TemporaryDirectory() as base_dir:
            m_logger.log_level = 2
            m_logger.INFO = 1

            # Test behaviour when the source doesn't exist
            nonexistent_path = Path(base_dir) / "wrongfiletype.txt"
            with self.assertRaises(ValueError):
                buildops.file_extract(nonexistent_path, environ)
            m_logger.debug.assert_not_called()
            m_logger.error.assert_not_called()
            m_logger.reset_mock()

            nonexistent_path = Path(base_dir) / "nonexistent.tar.gz"
            with self.assertRaises(FileNotFoundError):
                buildops.file_extract(nonexistent_path, environ)
            m_logger.debug.assert_called()
            m_logger.error.assert_not_called()
            m_logger.reset_mock()

            nonexistent_path = Path(base_dir) / "nonexistent.zip"
            try:
                buildops.file_extract(nonexistent_path, environ)
                self.fail("No exception raised")
            except FileNotFoundError:
                pass  # This is raised by zipfile on Windows.
            except BuildozerCommandException:
                pass  # This is raised by cmd when not on Windows.

            m_logger.reset_mock()

            # Create a zip file and unzip it.
            text_file_path = Path(base_dir) / "text_to_zip.txt"
            with open(text_file_path, "w") as outfile:
                outfile.write("Text to zip")
            zipfile_path = Path(base_dir) / "zipped.zip"
            with ZipFile(zipfile_path, "w") as outfile:
                outfile.write(text_file_path, arcname=text_file_path.name)
            unlink(text_file_path)
            buildops.file_extract(zipfile_path, environ, cwd=base_dir)
            m_logger.debug.assert_called()
            m_logger.error.assert_not_called()
            with open(text_file_path, "r") as uncompressed_file:
                assert uncompressed_file.read() == "Text to zip"
            m_logger.reset_mock()

            # Todo: Create a multi-file zip file with permissions.
            # Show it unpacks.

            # Create a tgz file and untgz it.
            text_file_path = Path(base_dir) / "text_to_tgz.txt"
            with open(text_file_path, "w") as outfile:
                outfile.write("Text to tgz")
            tarfile_path = Path(base_dir) / "targzipped.tgz"
            with tarfile.open(tarfile_path, "x:gz") as outfile:
                outfile.add(text_file_path, arcname=text_file_path.name)
            unlink(text_file_path)
            buildops.file_extract(tarfile_path, environ, cwd=base_dir)
            m_logger.debug.assert_called()
            m_logger.error.assert_not_called()
            with open(text_file_path, "r") as uncompressed_file:
                assert uncompressed_file.read() == "Text to tgz"
            m_logger.reset_mock()

    def test_cmd_unicode_decode(self):
        """
        Verifies cmd() can properly handle non-unicode outputs.
        """
        command = "command_to_pretend_to_run"
        kwargs = {
            "show_output": True,
            "get_stdout": True,
            "get_stderr": True,
            "env": environ,
        }
        command_output = b"\x80 cannot decode \x80"

        # Confirm that we can't decode it
        with self.assertRaises(UnicodeDecodeError):
            command_output.decode("utf-8")

        with mock.patch("buildozer.buildops.Popen") as m_popen, mock.patch(
            "buildozer.buildops.stdout"
        ):

            m_popen().stdout = [command_output]
            m_popen().returncode = 0

            cmd_result = buildops.cmd(command, **kwargs)

        # when get_stdout is True, the command output also gets returned
        assert cmd_result.stdout == command_output.decode("utf-8", "ignore")
        assert cmd_result.stderr is None
        assert cmd_result.return_code == 0

    def test_stream_reader(self):
        # StreamReader supports two sorts of stream. Use one of each.
        stream1 = MockStream()
        stream2 = MockStream(support_read1=False)

        streamreader = buildops._StreamReader(stream1, stream2)

        stream1.write("Text 1")
        assert streamreader.read() == ("Text 1", None)

        stream2.write("Text 2")
        assert streamreader.read() == (None, "Text 2")

        stream1.close()
        stream2.write("Final piece of text")
        stream2.close()
        assert streamreader.read() == (None, "Final piece of text")
        assert streamreader.read() is None

    def test_cmd(self):
        # Simple case: Run python, get version number
        cmd_result = buildops.cmd([executable, "-V"], environ, get_stdout=True)
        assert cmd_result.stdout.startswith("Python")
        assert cmd_result.stderr is None
        assert cmd_result.return_code == 0

        # What if env is None?
        cmd_result = buildops.cmd([executable, "-V"], env=None, get_stdout=True)
        assert cmd_result.stdout.startswith("Python")
        assert cmd_result.stderr is None
        assert cmd_result.return_code == 0

        # What if a path is passed?
        cmd_result = buildops.cmd(
            [Path(executable), "-V"], environ, get_stdout=True
        )
        assert cmd_result.stdout.startswith("Python")
        assert cmd_result.stderr is None
        assert cmd_result.return_code == 0

        # This time, don't collect stdout, just display it
        cmd_result = buildops.cmd([executable, "-V"], environ, show_output=True)
        assert tuple(cmd_result) == (None, None, 0)

        with self.assertRaises(FileNotFoundError):
            # This command isn't even found to return an error code.
            _ = buildops.cmd(["__thisdoesntexist__"], environ)

        with mock.patch(
            "buildozer.buildops.LOGGER", log_level=2, INFO=1
        ) as m_logger:
            with self.assertRaises(BuildozerCommandException):
                # This command gives an error code, and aborts.
                _ = buildops.cmd([executable, "__thisdoesntexist__"], environ)
            # Long warning is sent to the log.
            m_logger.error.assert_called()

        # This command gives an error code, but we don't care
        cmd_result = buildops.cmd(
            [executable, "__thisdoesntexist__"], environ, break_on_error=False
        )
        assert tuple(cmd_result) == (None, None, 2)

        # This command gives an error code, and we want the error output
        print("This tests expects a 'can't open file' error to be displayed...")
        cmd_result = buildops.cmd(
            [executable, "__thisdoesntexist__"],
            environ,
            get_stdout=True,
            get_stderr=True,
            break_on_error=False,
        )
        assert cmd_result.stdout is None
        assert "can't open file" in cmd_result.stderr
        assert cmd_result.return_code == 2

        # This command takes 10 seconds. Abort after 2.
        start_time = time.time()

        cmd_result = buildops.cmd(
            [
                executable,
                "-c",
                "import time; print('Starting', flush=True); "
                "time.sleep(0.5); print('0.5 second elapsed', flush=True); "
                "time.sleep(2.5); print('3 seconds elapsed', flush=True); "
                "time.sleep(7.0); print('Stopping', flush=True)",
            ],
            environ,
            get_stdout=True,
            get_stderr=True,
            run_condition=lambda: (time.time() - start_time) <= 2,
            break_on_error=False,
        )
        assert cmd_result.stdout, "Should have some output: " + str(cmd_result)
        assert cmd_result.stdout.splitlines() == [
            "Starting",
            "0.5 second elapsed",
        ]
        assert cmd_result.return_code != 0

    @skipIf(platform != "win32", "Windows only test to confirm failure")
    def test_cmd_expect_win(self):
        with self.assertRaises(AssertionError):
            # This command won't run on Windows.
            buildops.cmd_expect([executable, "-V"], environ)

    @skipIf(platform == "win32", "cmd_expect doesn't run on Windows")
    def test_cmd_expect(self):
        p = buildops.cmd_expect([executable, "-V"], environ, show_output=True)
        p.expect(".*Python.*")

    def test_download(self):
        with TemporaryDirectory() as download_dir:
            ico_path = Path(download_dir) / "favicon.ico"
            buildops.download(
                "https://github.com/", "favicon.ico", cwd=download_dir
            )
            assert ico_path.exists()

    def test_checkbin(self):

        with mock.patch("buildozer.buildops.exit") as m_exit, mock.patch(
            "buildozer.buildops.LOGGER"
        ) as m_logger:

            assert buildops.checkbin("Python", "python")
            # Probably ^ == executable, but not always in the CI environment.
            m_logger.debug.assert_called()
            m_exit.assert_not_called()
            m_logger.error.assert_not_called()

            m_logger.reset_mock()

            buildops.checkbin("Noneexistent", "__nonexistent__")
            m_logger.debug.assert_called()
            m_exit.assert_called()
            m_logger.error.assert_called()
