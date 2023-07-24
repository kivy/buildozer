'''
Buildozer
=========

Generic Python packager for Android / iOS. Desktop later.

'''

__version__ = '1.5.1.dev0'

import os
import re
import sys
import select
import codecs
import textwrap
import warnings
from sys import stdout, stderr, exit
from re import search
from os.path import join, exists, dirname, realpath, splitext, expanduser
from subprocess import Popen, PIPE, TimeoutExpired
from os import environ, unlink, walk, sep, listdir, makedirs
from copy import copy
from shutil import copyfile, rmtree, copytree, move, which
from fnmatch import fnmatch

import shlex
import pexpect

from urllib.request import FancyURLopener
try:
    import fcntl
except ImportError:
    # on windows, no fcntl
    fcntl = None

from buildozer.jsonstore import JsonStore
from buildozer.logger import Logger
from buildozer.specparser import SpecParser

SIMPLE_HTTP_SERVER_PORT = 8000


class ChromeDownloader(FancyURLopener):
    version = (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36')


urlretrieve = ChromeDownloader().retrieve


class BuildozerException(Exception):
    '''
    Exception raised for general situations buildozer cannot process.
    '''
    pass


class BuildozerCommandException(BuildozerException):
    '''
    Exception raised when an external command failed.

    See: `Buildozer.cmd()`.
    '''
    pass


class Buildozer:

    standard_cmds = ('distclean', 'update', 'debug', 'release',
                     'deploy', 'run', 'serve')

    def __init__(self, filename='buildozer.spec', target=None):
        self.environ = {}
        self.specfilename = filename
        self.state = None
        self.build_id = None
        self.config = SpecParser()

        self.logger = Logger()

        if exists(filename):
            self.config.read(filename, "utf-8")
            self.check_configuration_tokens()

        try:
            self.logger.set_level(
                int(self.config.getdefault(
                    'buildozer', 'log_level', '2')))
        except Exception:
            pass

        self.user_bin_dir = self.config.getdefault('buildozer', 'bin_dir', None)
        if self.user_bin_dir:
            self.user_bin_dir = realpath(join(self.root_dir, self.user_bin_dir))

        self.targetname = None
        self.target = None
        if target:
            self.set_target(target)

    def set_target(self, target):
        '''Set the target to use (one of buildozer.targets, such as "android")
        '''
        self.targetname = target
        m = __import__('buildozer.targets.{0}'.format(target),
                       fromlist=['buildozer'])
        self.target = m.get_target(self)
        self.check_build_layout()
        self.check_configuration_tokens()

    def prepare_for_build(self):
        '''Prepare the build.
        '''
        assert self.target is not None
        if hasattr(self.target, '_build_prepared'):
            return

        self.logger.info('Preparing build')

        self.logger.info('Check requirements for {0}'.format(self.targetname))
        self.target.check_requirements()

        self.logger.info('Install platform')
        self.target.install_platform()

        self.logger.info('Check application requirements')
        self.check_application_requirements()

        self.check_garden_requirements()

        self.logger.info('Compile platform')
        self.target.compile_platform()

        # flag to prevent multiple build
        self.target._build_prepared = True

    def build(self):
        '''Do the build.

        The target can set build_mode to 'release' or 'debug' before calling
        this method.

        (:meth:`prepare_for_build` must have been call before.)
        '''
        assert self.target is not None
        assert hasattr(self.target, '_build_prepared')

        if hasattr(self.target, '_build_done'):
            return

        # increment the build number
        self.build_id = int(self.state.get('cache.build_id', '0')) + 1
        self.state['cache.build_id'] = str(self.build_id)

        self.logger.info('Build the application #{}'.format(self.build_id))
        self.build_application()

        self.logger.info('Package the application')
        self.target.build_package()

        # flag to prevent multiple build
        self.target._build_done = True

    #
    # Internal check methods
    #

    def checkbin(self, msg, fn):
        self.logger.debug('Search for {0}'.format(msg))
        executable_location = which(fn)
        if executable_location:
            self.logger.debug(' -> found at {0}'.format(executable_location))
            return realpath(executable_location)
        self.logger.error('{} not found, please install it.'.format(msg))
        exit(1)

    def cmd(self, command, **kwargs):
        # prepare the environ, based on the system + our own env
        env = environ.copy()
        env.update(self.environ)

        # prepare the process
        kwargs.setdefault('env', env)
        kwargs.setdefault('stdout', PIPE)
        kwargs.setdefault('stderr', PIPE)
        kwargs.setdefault('close_fds', True)
        kwargs.setdefault('show_output', self.logger.log_level > 1)

        show_output = kwargs.pop('show_output')
        get_stdout = kwargs.pop('get_stdout', False)
        get_stderr = kwargs.pop('get_stderr', False)
        break_on_error = kwargs.pop('break_on_error', True)
        sensible = kwargs.pop('sensible', False)
        run_condition = kwargs.pop('run_condition', None)
        quiet = kwargs.pop('quiet', False)

        if not quiet:
            if not sensible:
                self.logger.debug('Run {0!r}'.format(command))
            else:
                if isinstance(command, (list, tuple)):
                    self.logger.debug('Run {0!r} ...'.format(command[0]))
                else:
                    self.logger.debug('Run {0!r} ...'.format(command.split()[0]))
            self.logger.debug('Cwd {}'.format(kwargs.get('cwd')))

        # open the process
        if sys.platform == 'win32':
            kwargs.pop('close_fds', None)
        process = Popen(command, **kwargs)

        # prepare fds
        fd_stdout = process.stdout.fileno()
        fd_stderr = process.stderr.fileno()
        if fcntl:
            fcntl.fcntl(
                fd_stdout, fcntl.F_SETFL,
                fcntl.fcntl(fd_stdout, fcntl.F_GETFL) | os.O_NONBLOCK)
            fcntl.fcntl(
                fd_stderr, fcntl.F_SETFL,
                fcntl.fcntl(fd_stderr, fcntl.F_GETFL) | os.O_NONBLOCK)

        ret_stdout = [] if get_stdout else None
        ret_stderr = [] if get_stderr else None
        while not run_condition or run_condition():
            try:
                readx = select.select([fd_stdout, fd_stderr], [], [], 1)[0]
            except select.error:
                break
            if fd_stdout in readx:
                chunk = process.stdout.read()
                if not chunk:
                    break
                if get_stdout:
                    ret_stdout.append(chunk)
                if show_output:
                    stdout.write(chunk.decode('utf-8', 'replace'))
            if fd_stderr in readx:
                chunk = process.stderr.read()
                if not chunk:
                    break
                if get_stderr:
                    ret_stderr.append(chunk)
                if show_output:
                    stderr.write(chunk.decode('utf-8', 'replace'))

            stdout.flush()
            stderr.flush()

        try:
            process.communicate(
                timeout=(1 if run_condition and not run_condition() else None)
            )
        except TimeoutExpired:
            pass

        if process.returncode != 0 and break_on_error:
            self.logger.error('Command failed: {0}'.format(command))
            self.logger.log_env(self.logger.ERROR, kwargs['env'])
            self.logger.error('')
            self.logger.error('Buildozer failed to execute the last command')
            if self.logger.log_level <= self.logger.INFO:
                self.logger.error('If the error is not obvious, please raise the log_level to 2')
                self.logger.error('and retry the latest command.')
            else:
                self.logger.error('The error might be hidden in the log above this error')
                self.logger.error('Please read the full log, and search for it before')
                self.logger.error('raising an issue with buildozer itself.')
            self.logger.error('In case of a bug report, please add a full log with log_level = 2')
            raise BuildozerCommandException()

        if ret_stdout:
            ret_stdout = b''.join(ret_stdout)
        if ret_stderr:
            ret_stderr = b''.join(ret_stderr)

        return (ret_stdout.decode('utf-8', 'ignore') if ret_stdout else None,
                ret_stderr.decode('utf-8') if ret_stderr else None,
                process.returncode)

    def cmd_expect(self, command, **kwargs):

        # prepare the environ, based on the system + our own env
        env = environ.copy()
        env.update(self.environ)

        # prepare the process
        kwargs.setdefault('env', env)
        kwargs.setdefault('show_output', self.logger.log_level > 1)
        sensible = kwargs.pop('sensible', False)
        show_output = kwargs.pop('show_output')

        if show_output:
            kwargs['logfile'] = codecs.getwriter('utf8')(stdout.buffer)

        if not sensible:
            self.logger.debug('Run (expect) {0!r}'.format(command))
        else:
            self.logger.debug('Run (expect) {0!r} ...'.format(command.split()[0]))

        self.logger.debug('Cwd {}'.format(kwargs.get('cwd')))
        return pexpect.spawnu(shlex.join(command), **kwargs)

    def check_configuration_tokens(self):
        '''Ensure the spec file is 'correct'.
        '''
        self.logger.info('Check configuration tokens')
        self.migrate_configuration_tokens()
        get = self.config.getdefault
        errors = []
        adderror = errors.append
        if not get('app', 'title', ''):
            adderror('[app] "title" is missing')
        if not get('app', 'source.dir', ''):
            adderror('[app] "source.dir" is missing')

        package_name = get('app', 'package.name', '')
        if not package_name:
            adderror('[app] "package.name" is missing')
        elif package_name[0] in map(str, range(10)):
            adderror('[app] "package.name" may not start with a number.')

        version = get('app', 'version', '')
        version_regex = get('app', 'version.regex', '')
        if not version and not version_regex:
            adderror('[app] One of "version" or "version.regex" must be set')
        if version and version_regex:
            adderror('[app] Conflict between "version" and "version.regex"'
                     ', only one can be used.')
        if version_regex and not get('app', 'version.filename', ''):
            adderror('[app] "version.filename" is missing'
                     ', required by "version.regex"')

        orientation = self.config.getlist("app", "orientation", ["landscape"])
        for o in orientation:
            if o not in ("landscape", "portrait", "landscape-reverse", "portrait-reverse"):
                adderror(f'[app] "{o}" is not a valid  value for "orientation"')
        if errors:
            self.logger.error('{0} error(s) found in the buildozer.spec'.format(
                len(errors)))
            for error in errors:
                print(error)
            exit(1)

    def migrate_configuration_tokens(self):
        config = self.config
        if config.has_section("app"):
            migration = (
                ("android.p4a_dir", "p4a.source_dir"),
                ("android.p4a_whitelist", "android.whitelist"),
                ("android.bootstrap", "p4a.bootstrap"),
                ("android.branch", "p4a.branch"),
                ("android.p4a_whitelist_src", "android.whitelist_src"),
                ("android.p4a_blacklist_src", "android.blacklist_src")
            )
            for entry_old, entry_new in migration:
                if not config.has_option("app", entry_old):
                    continue
                value = config.get("app", entry_old)
                config.set("app", entry_new, value)
                config.remove_option("app", entry_old)
                self.logger.error("In section [app]: {} is deprecated, rename to {}!".format(
                    entry_old, entry_new))

    def check_build_layout(self):
        '''Ensure the build (local and global) directory layout and files are
        ready.
        '''
        self.logger.info('Ensure build layout')

        if not exists(self.specfilename):
            print('No {0} found in the current directory. Abandon.'.format(
                self.specfilename))
            exit(1)

        # create global dir
        self.mkdir(self.global_buildozer_dir)
        self.mkdir(self.global_cache_dir)

        # create local .buildozer/ dir
        self.mkdir(self.buildozer_dir)
        # create local bin/ dir
        self.mkdir(self.bin_dir)

        self.mkdir(self.applibs_dir)
        self.state = JsonStore(join(self.buildozer_dir, 'state.db'))

        target = self.targetname
        if target:
            self.mkdir(join(self.global_platform_dir, target, 'platform'))
            self.mkdir(join(self.buildozer_dir, target, 'platform'))
            self.mkdir(join(self.buildozer_dir, target, 'app'))

    def check_application_requirements(self):
        '''Ensure the application requirements are all available and ready to be
        packaged as well.
        '''
        requirements = self.config.getlist('app', 'requirements', '')
        target_available_packages = self.target.get_available_packages()
        if target_available_packages is True:
            # target handles all packages!
            return

        # remove all the requirements that the target can compile
        onlyname = lambda x: x.split('==')[0]  # noqa: E731
        requirements = [x for x in requirements if onlyname(x) not in
                        target_available_packages]

        if requirements and hasattr(sys, 'real_prefix'):
            e = self.logger.error
            e('virtualenv is needed to install pure-Python modules, but')
            e('virtualenv does not support nesting, and you are running')
            e('buildozer in one. Please run buildozer outside of a')
            e('virtualenv instead.')
            exit(1)

        # did we already installed the libs ?
        if (
            exists(self.applibs_dir) and
            self.state.get('cache.applibs', '') == requirements
        ):
            self.logger.debug('Application requirements already installed, pass')
            return

        # recreate applibs
        self.rmdir(self.applibs_dir)
        self.mkdir(self.applibs_dir)

        # ok now check the availability of all requirements
        for requirement in requirements:
            self._install_application_requirement(requirement)

        # everything goes as expected, save this state!
        self.state['cache.applibs'] = requirements

    def _install_application_requirement(self, module):
        self._ensure_virtualenv()
        self.logger.debug('Install requirement {} in virtualenv'.format(module))
        self.cmd(
            ["pip", "install", f"--target={self.applibs_dir}", module],
            env=self.env_venv,
            cwd=self.buildozer_dir,
        )

    def check_garden_requirements(self):
        garden_requirements = self.config.getlist('app',
            'garden_requirements', '')
        if garden_requirements:
            warnings.warn("`garden_requirements` settings is deprecated, use `requirements` instead", DeprecationWarning)

    def _ensure_virtualenv(self):
        if hasattr(self, 'venv'):
            return
        self.venv = join(self.buildozer_dir, 'venv')
        if not self.file_exists(self.venv):
            self.cmd(["python3", "-m", "venv", "./venv"],
                    cwd=self.buildozer_dir)

        # read virtualenv output and parse it
        output = self.cmd(
            ["bash", "-c", "source venv/bin/activate && env"],
            get_stdout=True,
            cwd=self.buildozer_dir,
        )
        self.env_venv = copy(self.environ)
        for line in output[0].splitlines():
            args = line.split('=', 1)
            if len(args) != 2:
                continue
            key, value = args
            if key in ('VIRTUAL_ENV', 'PATH'):
                self.env_venv[key] = value
        if 'PYTHONHOME' in self.env_venv:
            del self.env_venv['PYTHONHOME']

        # ensure any sort of compilation will fail
        self.env_venv['CC'] = '/bin/false'
        self.env_venv['CXX'] = '/bin/false'

    def mkdir(self, dn):
        if exists(dn):
            return
        self.logger.debug('Create directory {0}'.format(dn))
        makedirs(dn)

    def rmdir(self, dn):
        if not exists(dn):
            return
        self.logger.debug('Remove directory and subdirectory {}'.format(dn))
        rmtree(dn)

    def file_matches(self, patterns):
        from glob import glob
        result = []
        for pattern in patterns:
            matches = glob(expanduser(pattern.strip()))
            result.extend(matches)
        return result

    def file_exists(self, *args):
        return exists(join(*args))

    def file_rename(self, source, target, cwd=None):
        if cwd:
            source = join(cwd, source)
            target = join(cwd, target)
        self.logger.debug('Rename {0} to {1}'.format(source, target))
        if not os.path.isdir(os.path.dirname(target)):
            self.logger.error(('Rename {0} to {1} fails because {2} is not a '
                        'directory').format(source, target, target))
        move(source, target)

    def file_copy(self, source, target, cwd=None):
        if cwd:
            source = join(cwd, source)
            target = join(cwd, target)
        self.logger.debug('Copy {0} to {1}'.format(source, target))
        copyfile(source, target)

    def file_extract(self, archive, cwd=None):
        if archive.endswith('.tgz') or archive.endswith('.tar.gz'):
            self.cmd(["tar", "xzf", archive], cwd=cwd)
            return

        if archive.endswith('.tbz2') or archive.endswith('.tar.bz2'):
            # XXX same as before
            self.cmd(["tar", "xjf", archive], cwd=cwd)
            return

        if archive.endswith('.bin'):
            # To process the bin files for linux and darwin systems
            self.cmd(["chmod", "a+x", archive], cwd=cwd)
            self.cmd([f"./{archive}"], cwd=cwd)
            return

        if archive.endswith('.zip'):
            self.cmd(["unzip", "-q", join(cwd, archive)], cwd=cwd)
            return

        raise Exception('Unhandled extraction for type {0}'.format(archive))

    def file_copytree(self, src, dest):
        print('copy {} to {}'.format(src, dest))
        if os.path.isdir(src):
            if not os.path.isdir(dest):
                os.makedirs(dest)
            files = os.listdir(src)
            for f in files:
                self.file_copytree(
                    os.path.join(src, f),
                    os.path.join(dest, f))
        else:
            copyfile(src, dest)

    def clean_platform(self):
        self.logger.info('Clean the platform build directory')
        if not exists(self.platform_dir):
            return
        rmtree(self.platform_dir)

    def download(self, url, filename, cwd=None):
        def report_hook(index, blksize, size):
            if size <= 0:
                progression = '{0} bytes'.format(index * blksize)
            else:
                progression = '{0:.2f}%'.format(
                        index * blksize * 100. / float(size))
            if "CI" not in environ:
                stdout.write('- Download {}\r'.format(progression))
                stdout.flush()

        url = url + filename
        if cwd:
            filename = join(cwd, filename)
        if self.file_exists(filename):
            unlink(filename)

        self.logger.debug('Downloading {0}'.format(url))
        urlretrieve(url, filename, report_hook)
        return filename

    def get_version(self):
        c = self.config
        has_version = c.has_option('app', 'version')
        has_regex = c.has_option('app', 'version.regex')
        has_filename = c.has_option('app', 'version.filename')

        # version number specified
        if has_version:
            if has_regex or has_filename:
                raise Exception(
                    'version.regex and version.filename conflict with version')
            return c.get('app', 'version')

        # search by regex
        if has_regex or has_filename:
            if has_regex and not has_filename:
                raise Exception('version.filename is missing')
            if has_filename and not has_regex:
                raise Exception('version.regex is missing')

            fn = c.get('app', 'version.filename')
            with open(fn) as fd:
                data = fd.read()
                regex = c.get('app', 'version.regex')
                match = search(regex, data)
                if not match:
                    raise Exception(
                        'Unable to find capture version in {0}\n'
                        ' (looking for `{1}`)'.format(fn, regex))
                version = match.groups()[0]
                self.logger.debug('Captured version: {0}'.format(version))
                return version

        raise Exception('Missing version or version.regex + version.filename')

    def build_application(self):
        self._copy_application_sources()
        self._copy_application_libs()
        self._add_sitecustomize()

    def _copy_application_sources(self):
        # XXX clean the inclusion/exclusion algo.
        source_dir = realpath(expanduser(self.config.getdefault('app', 'source.dir', '.')))
        include_exts = self.config.getlist('app', 'source.include_exts', '')
        exclude_exts = self.config.getlist('app', 'source.exclude_exts', '')
        exclude_dirs = self.config.getlist('app', 'source.exclude_dirs', '')
        exclude_patterns = self.config.getlist('app', 'source.exclude_patterns', '')
        include_patterns = self.config.getlist('app',
                                               'source.include_patterns',
                                               '')
        app_dir = self.app_dir

        include_exts = [ext.lower() for ext in include_exts]
        exclude_exts = [ext.lower() for ext in exclude_exts]
        exclude_dirs = [dir.lower() for dir in exclude_dirs]
        exclude_patterns = [pat.lower() for pat in exclude_patterns]
        include_patterns = [pat.lower() for pat in include_patterns]

        self.logger.debug('Copy application source from {}'.format(source_dir))

        rmtree(self.app_dir)

        for root, dirs, files in walk(source_dir, followlinks=True):
            # avoid hidden directory
            if True in [x.startswith('.') for x in root.split(sep)]:
                continue

            # need to have sort-of normalization. Let's say you want to exclude
            # image directory but not images, the filtered_root must have a / at
            # the end, same for the exclude_dir. And then we can safely compare
            filtered_root = root[len(source_dir) + 1:].lower()
            if filtered_root:
                filtered_root += '/'

                # manual exclude_dirs approach
                is_excluded = False
                for exclude_dir in exclude_dirs:
                    if exclude_dir[-1] != '/':
                        exclude_dir += '/'
                    if filtered_root.startswith(exclude_dir):
                        is_excluded = True
                        break

                # pattern matching
                if not is_excluded:
                    # match pattern if not ruled out by exclude_dirs
                    for pattern in exclude_patterns:
                        if fnmatch(filtered_root, pattern):
                            is_excluded = True
                            break
                for pattern in include_patterns:
                    if fnmatch(filtered_root, pattern):
                        is_excluded = False
                        break

                if is_excluded:
                    continue

            for fn in files:
                # avoid hidden files
                if fn.startswith('.'):
                    continue

                # pattern matching
                is_excluded = False
                dfn = fn.lower()
                if filtered_root:
                    dfn = join(filtered_root, fn)
                for pattern in exclude_patterns:
                    if fnmatch(dfn, pattern):
                        is_excluded = True
                        break
                for pattern in include_patterns:
                    if fnmatch(dfn, pattern):
                        is_excluded = False
                        break
                if is_excluded:
                    continue

                # filter based on the extension
                # TODO more filters
                basename, ext = splitext(fn)
                if ext:
                    ext = ext[1:].lower()
                    if include_exts and ext not in include_exts:
                        continue
                    if exclude_exts and ext in exclude_exts:
                        continue

                sfn = join(root, fn)
                rfn = realpath(join(app_dir, root[len(source_dir) + 1:], fn))

                # ensure the directory exists
                dfn = dirname(rfn)
                self.mkdir(dfn)

                # copy!
                self.logger.debug('Copy {0}'.format(sfn))
                copyfile(sfn, rfn)

    def _copy_application_libs(self):
        # copy also the libs
        copytree(self.applibs_dir, join(self.app_dir, '_applibs'))

    def _add_sitecustomize(self):
        copyfile(join(dirname(__file__), 'sitecustomize.py'),
                join(self.app_dir, 'sitecustomize.py'))

        main_py = join(self.app_dir, 'service', 'main.py')
        if not self.file_exists(main_py):
            return

        header = (b'import sys, os; '
                   b'sys.path = [os.path.join(os.getcwd(),'
                   b'"..", "_applibs")] + sys.path\n')
        with open(main_py, 'rb') as fd:
            data = fd.read()
        data = header + data
        with open(main_py, 'wb') as fd:
            fd.write(data)
        self.logger.info('Patched service/main.py to include applibs')

    def namify(self, name):
        '''Return a "valid" name from a name with lot of invalid chars
        (allowed characters: a-z, A-Z, 0-9, -, _)
        '''
        return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)

    @property
    def root_dir(self):
        return realpath(expanduser(dirname(self.specfilename)))

    @property
    def user_build_dir(self):
        """The user-provided build dir, if any."""
        # Check for a user-provided build dir
        # Check the (deprecated) builddir token, for backwards compatibility
        build_dir = self.config.getdefault('buildozer', 'builddir', None)
        if build_dir is not None:
            # for backwards compatibility, append .buildozer to builddir
            build_dir = join(build_dir, '.buildozer')
        build_dir = self.config.getdefault('buildozer', 'build_dir', build_dir)

        if build_dir is not None:
            build_dir = realpath(join(self.root_dir, expanduser(build_dir)))

        return build_dir

    @property
    def buildozer_dir(self):
        '''The directory in which to run the app build.'''
        if self.user_build_dir is not None:
            return self.user_build_dir
        return join(self.root_dir, '.buildozer')

    @property
    def bin_dir(self):
        if self.user_bin_dir:
            return self.user_bin_dir
        return join(self.root_dir, 'bin')

    @property
    def platform_dir(self):
        return join(self.buildozer_dir, self.targetname, 'platform')

    @property
    def app_dir(self):
        return join(self.buildozer_dir, self.targetname, 'app')

    @property
    def applibs_dir(self):
        return join(self.buildozer_dir, 'applibs')

    @property
    def global_buildozer_dir(self):
        return join(expanduser('~'), '.buildozer')

    @property
    def global_platform_dir(self):
        return join(self.global_buildozer_dir, self.targetname, 'platform')

    @property
    def global_packages_dir(self):
        return join(self.global_buildozer_dir, self.targetname, 'packages')

    @property
    def global_cache_dir(self):
        return join(self.global_buildozer_dir, 'cache')

    @property
    def package_full_name(self):
        package_name = self.config.getdefault('app', 'package.name', '')
        package_domain = self.config.getdefault('app', 'package.domain', '')
        if package_domain == '':
            return package_name
        return '{}.{}'.format(package_domain, package_name)

    #
    # command line invocation
    #

    def targets(self):
        for fn in listdir(join(dirname(__file__), 'targets')):
            if fn.startswith('.') or fn.startswith('__'):
                continue
            if not fn.endswith('.py'):
                continue
            target = fn[:-3]
            try:
                m = __import__('buildozer.targets.{0}'.format(target),
                        fromlist=['buildozer'])
                yield target, m
            except NotImplementedError:
                pass

    def usage(self):
        print('Usage:')
        print('    buildozer [--profile <name>] [--verbose] [target] <command>...')
        print('    buildozer --version')
        print('')
        print('Available targets:')
        targets = list(self.targets())
        for target, m in targets:
            try:
                doc = m.__doc__.strip().splitlines()[0].strip()
            except Exception:
                doc = '<no description>'
            print('  {0:<18} {1}'.format(target, doc))

        print('')
        print('Global commands (without target):')
        cmds = [x for x in dir(self) if x.startswith('cmd_')]
        for cmd in cmds:
            name = cmd[4:]
            meth = getattr(self, cmd)

            if not meth.__doc__:
                continue
            doc = list(meth.__doc__.strip().splitlines())[0].strip()
            print('  {0:<18} {1}'.format(name, doc))

        print('')
        print('Target commands:')
        print('  clean      Clean the target environment')
        print('  update     Update the target dependencies')
        print('  debug      Build the application in debug mode')
        print('  release    Build the application in release mode')
        print('  deploy     Deploy the application on the device')
        print('  run        Run the application on the device')
        print('  serve      Serve the bin directory via SimpleHTTPServer')

        for target, m in targets:
            mt = m.get_target(self)
            commands = mt.get_custom_commands()
            if not commands:
                continue
            print('')
            print('Target "{0}" commands:'.format(target))
            for command, doc in commands:
                if not doc:
                    continue
                doc = textwrap.fill(textwrap.dedent(doc).strip(), 59,
                                    subsequent_indent=' ' * 21)
                print('  {0:<18} {1}'.format(command, doc))

        print('')

    def run_default(self):
        self.check_build_layout()
        if 'buildozer:defaultcommand' not in self.state:
            print('No default command set.')
            print('Use "buildozer setdefault <command args...>"')
            print('Use "buildozer help" for a list of all commands"')
            exit(1)
        cmd = self.state['buildozer:defaultcommand']
        self.run_command(cmd)

    def run_command(self, args):
        profile = None

        while args:
            if not args[0].startswith('-'):
                break
            arg = args.pop(0)

            if arg in ('-v', '--verbose'):
                self.logger.set_level(2)

            elif arg in ('-h', '--help'):
                self.usage()
                exit(0)

            elif arg in ('-p', '--profile'):
                profile = args.pop(0)

            elif arg == '--version':
                print('Buildozer {0}'.format(__version__))
                exit(0)

        self.config.apply_profile(profile)

        self.check_root()

        if not args:
            self.run_default()
            return

        command, args = args[0], args[1:]
        cmd = 'cmd_{0}'.format(command)

        # internal commands ?
        if hasattr(self, cmd):
            getattr(self, cmd)(*args)
            return

        # maybe it's a target?
        targets = [x[0] for x in self.targets()]
        if command not in targets:
            print('Unknown command/target {}'.format(command))
            exit(1)

        self.set_target(command)
        self.target.run_commands(args)

    def check_root(self):
        '''If effective user id is 0, display a warning and require
        user input to continue (or to cancel)'''

        warn_on_root = self.config.getdefault('buildozer', 'warn_on_root', '1')
        try:
            euid = os.geteuid() == 0
        except AttributeError:
            if sys.platform == 'win32':
                import ctypes
            euid = ctypes.windll.shell32.IsUserAnAdmin() != 0
        if warn_on_root == '1' and euid:
            print('\033[91m\033[1mBuildozer is running as root!\033[0m')
            print('\033[91mThis is \033[1mnot\033[0m \033[91mrecommended, and may lead to problems later.\033[0m')
            cont = None
            while cont not in ('y', 'n'):
                cont = input('Are you sure you want to continue [y/n]? ')

            if cont == 'n':
                sys.exit()

    def cmd_init(self, *args):
        '''Create a initial buildozer.spec in the current directory
        '''
        if exists('buildozer.spec'):
            print('ERROR: You already have a buildozer.spec file.')
            exit(1)
        copyfile(join(dirname(__file__), 'default.spec'), 'buildozer.spec')
        print('File buildozer.spec created, ready to customize!')

    def cmd_distclean(self, *args):
        '''Clean the whole Buildozer environment.
        '''
        print("Warning: Your ndk, sdk and all other cached packages will be"
              " removed. Continue? (y/n)")
        if sys.stdin.readline().lower()[0] == 'y':
            self.logger.info('Clean the global build directory')
            if not exists(self.global_buildozer_dir):
                return
            rmtree(self.global_buildozer_dir)

    def cmd_appclean(self, *args):
        '''Clean the .buildozer folder in the app directory.

        This command specifically refuses to delete files in a
        user-specified build directory, to avoid accidentally deleting
        more than the user intends.
        '''
        if self.user_build_dir is not None:
            self.logger.error(
                ('Failed: build_dir is specified as {} in the buildozer config. `appclean` will '
                 'not attempt to delete files in a user-specified build directory.').format(self.user_build_dir))
        elif exists(self.buildozer_dir):
            self.logger.info('Deleting {}'.format(self.buildozer_dir))
            rmtree(self.buildozer_dir)
        else:
            self.logger.error('{} already deleted, skipping.'.format(self.buildozer_dir))

    def cmd_help(self, *args):
        '''Show the Buildozer help.
        '''
        self.usage()

    def cmd_setdefault(self, *args):
        '''Set the default command to run when no arguments are given
        '''
        self.check_build_layout()
        self.state['buildozer:defaultcommand'] = args

    def cmd_version(self, *args):
        '''Show the Buildozer version
        '''
        print('Buildozer {0}'.format(__version__))

    def cmd_serve(self, *args):
        '''Serve the bin directory via SimpleHTTPServer
        '''
        try:
            from http.server import SimpleHTTPRequestHandler
            from socketserver import TCPServer
        except ImportError:
            from SimpleHTTPServer import SimpleHTTPRequestHandler
            from SocketServer import TCPServer

        os.chdir(self.bin_dir)
        handler = SimpleHTTPRequestHandler
        httpd = TCPServer(("", SIMPLE_HTTP_SERVER_PORT), handler)
        print("Serving via HTTP at port {}".format(SIMPLE_HTTP_SERVER_PORT))
        print("Press Ctrl+c to quit serving.")
        httpd.serve_forever()
