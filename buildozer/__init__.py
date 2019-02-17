'''
Buildozer
=========

Generic Python packager for Android / iOS. Desktop later.

'''

__version__ = '0.40.dev0'

import os
import re
import sys
import select
import codecs
import textwrap
from buildozer.jsonstore import JsonStore
from sys import stdout, stderr, exit
from re import search
from os.path import join, exists, dirname, realpath, splitext, expanduser
from subprocess import Popen, PIPE
from os import environ, unlink, walk, sep, listdir, makedirs
from copy import copy
from shutil import copyfile, rmtree, copytree, move
from fnmatch import fnmatch

from pprint import pformat

try:
    from urllib.request import FancyURLopener
    from configparser import SafeConfigParser
except ImportError:
    from urllib import FancyURLopener
    from ConfigParser import SafeConfigParser
try:
    import fcntl
except ImportError:
    # on windows, no fcntl
    fcntl = None
try:
    # if installed, it can give color to windows as well
    import colorama
    colorama.init()

    RESET_SEQ = colorama.Fore.RESET + colorama.Style.RESET_ALL
    COLOR_SEQ = lambda x: x  # noqa: E731
    BOLD_SEQ = ''
    if sys.platform == 'win32':
        BLACK = colorama.Fore.BLACK + colorama.Style.DIM
    else:
        BLACK = colorama.Fore.BLACK + colorama.Style.BRIGHT
    RED = colorama.Fore.RED
    BLUE = colorama.Fore.CYAN
    USE_COLOR = 'NO_COLOR' not in environ

except ImportError:
    if sys.platform != 'win32':
        RESET_SEQ = "\033[0m"
        COLOR_SEQ = lambda x: "\033[1;{}m".format(30 + x)  # noqa: E731
        BOLD_SEQ = "\033[1m"
        BLACK = 0
        RED = 1
        BLUE = 4
        USE_COLOR = 'NO_COLOR' not in environ
    else:
        RESET_SEQ = ''
        COLOR_SEQ = ''
        BOLD_SEQ = ''
        RED = BLUE = BLACK = 0
        USE_COLOR = False

# error, info, debug
LOG_LEVELS_C = (RED, BLUE, BLACK)
LOG_LEVELS_T = 'EID'
SIMPLE_HTTP_SERVER_PORT = 8000
IS_PY3 = sys.version_info[0] >= 3


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


class Buildozer(object):

    ERROR = 0
    INFO = 1
    DEBUG = 2

    standard_cmds = ('distclean', 'update', 'debug', 'release',
                     'deploy', 'run', 'serve')

    def __init__(self, filename='buildozer.spec', target=None):
        super(Buildozer, self).__init__()
        self.log_level = 1
        self.environ = {}
        self.specfilename = filename
        self.state = None
        self.build_id = None
        self.config_profile = ''
        self.config = SafeConfigParser(allow_no_value=True)
        self.config.optionxform = lambda value: value
        self.config.getlist = self._get_config_list
        self.config.getlistvalues = self._get_config_list_values
        self.config.getdefault = self._get_config_default
        self.config.getbooldefault = self._get_config_bool
        self.config.getrawdefault = self._get_config_raw_default

        if exists(filename):
            try:
                self.config.read(filename, "utf-8")
            except TypeError:  # python 2 has no second arg here
                self.config.read(filename)
            self.check_configuration_tokens()

        # Check all section/tokens for env vars, and replace the
        # config value if a suitable env var exists.
        set_config_from_envs(self.config)

        try:
            self.log_level = int(self.config.getdefault(
                'buildozer', 'log_level', '1'))
        except Exception:
            pass

        build_dir = self.config.getdefault('buildozer', 'builddir', None)
        if build_dir:
            # for backwards compatibility, append .buildozer to builddir
            build_dir = join(build_dir, '.buildozer')
        self.build_dir = self.config.getdefault('buildozer', 'build_dir', build_dir)

        if self.build_dir:
            self.build_dir = realpath(join(self.root_dir, self.build_dir))
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
        assert(self.target is not None)
        if hasattr(self.target, '_build_prepared'):
            return

        self.info('Preparing build')

        self.info('Check requirements for {0}'.format(self.targetname))
        self.target.check_requirements()

        self.info('Install platform')
        self.target.install_platform()

        self.info('Check application requirements')
        self.check_application_requirements()

        self.info('Check garden requirements')
        self.check_garden_requirements()

        self.info('Compile platform')
        self.target.compile_platform()

        # flag to prevent multiple build
        self.target._build_prepared = True

    def build(self):
        '''Do the build.

        The target can set build_mode to 'release' or 'debug' before calling
        this method.

        (:meth:`prepare_for_build` must have been call before.)
        '''
        assert(self.target is not None)
        assert(hasattr(self.target, '_build_prepared'))

        if hasattr(self.target, '_build_done'):
            return

        # increment the build number
        self.build_id = int(self.state.get('cache.build_id', '0')) + 1
        self.state['cache.build_id'] = str(self.build_id)

        self.info('Build the application #{}'.format(self.build_id))
        self.build_application()

        self.info('Package the application')
        self.target.build_package()

        # flag to prevent multiple build
        self.target._build_done = True

    #
    # Log functions
    #

    def log(self, level, msg):
        if level > self.log_level:
            return
        if USE_COLOR:
            color = COLOR_SEQ(LOG_LEVELS_C[level])
            print(''.join((RESET_SEQ, color, '# ', msg, RESET_SEQ)))
        else:
            print('{} {}'.format(LOG_LEVELS_T[level], msg))

    def debug(self, msg):
        self.log(self.DEBUG, msg)

    def log_env(self, level, env):
        """dump env into debug logger in readable format"""
        self.log(level, "ENVIRONMENT:")
        for k, v in env.items():
            self.log(level, "    {} = {}".format(k, pformat(v)))

    def info(self, msg):
        self.log(self.INFO, msg)

    def error(self, msg):
        self.log(self.ERROR, msg)

    #
    # Internal check methods
    #

    def checkbin(self, msg, fn):
        self.debug('Search for {0}'.format(msg))
        if exists(fn):
            return realpath(fn)
        for dn in environ['PATH'].split(':'):
            rfn = realpath(join(dn, fn))
            if exists(rfn):
                self.debug(' -> found at {0}'.format(rfn))
                return rfn
        self.error('{} not found, please install it.'.format(msg))
        exit(1)

    def cmd(self, command, **kwargs):
        # prepare the environ, based on the system + our own env
        env = copy(environ)
        env.update(self.environ)

        # prepare the process
        kwargs.setdefault('env', env)
        kwargs.setdefault('stdout', PIPE)
        kwargs.setdefault('stderr', PIPE)
        kwargs.setdefault('close_fds', True)
        kwargs.setdefault('shell', True)
        kwargs.setdefault('show_output', self.log_level > 1)

        show_output = kwargs.pop('show_output')
        get_stdout = kwargs.pop('get_stdout', False)
        get_stderr = kwargs.pop('get_stderr', False)
        break_on_error = kwargs.pop('break_on_error', True)
        sensible = kwargs.pop('sensible', False)

        if not sensible:
            self.debug('Run {0!r}'.format(command))
        else:
            if type(command) in (list, tuple):
                self.debug('Run {0!r} ...'.format(command[0]))
            else:
                self.debug('Run {0!r} ...'.format(command.split()[0]))
        self.debug('Cwd {}'.format(kwargs.get('cwd')))
        self.log_env(self.DEBUG, kwargs["env"])

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
        while True:
            try:
                readx = select.select([fd_stdout, fd_stderr], [], [])[0]
            except select.error:
                break
            if fd_stdout in readx:
                chunk = process.stdout.read()
                if not chunk:
                    break
                if get_stdout:
                    ret_stdout.append(chunk)
                if show_output:
                    if IS_PY3:
                        stderr.write(chunk.decode('utf-8'))
                    else:
                        stdout.write(chunk)
            if fd_stderr in readx:
                chunk = process.stderr.read()
                if not chunk:
                    break
                if get_stderr:
                    ret_stderr.append(chunk)
                if show_output:
                    if IS_PY3:
                        stderr.write(chunk.decode('utf-8'))
                    else:
                        stderr.write(chunk)

        stdout.flush()
        stderr.flush()

        process.communicate()
        if process.returncode != 0 and break_on_error:
            self.error('Command failed: {0}'.format(command))
            self.log_env(self.ERROR, kwargs['env'])
            self.error('')
            self.error('Buildozer failed to execute the last command')
            if self.log_level <= self.INFO:
                self.error('If the error is not obvious, please raise the log_level to 2')
                self.error('and retry the latest command.')
            else:
                self.error('The error might be hidden in the log above this error')
                self.error('Please read the full log, and search for it before')
                self.error('raising an issue with buildozer itself.')
            self.error('In case of a bug report, please add a full log with log_level = 2')
            raise BuildozerCommandException()
        if ret_stdout:
            ret_stdout = b''.join(ret_stdout)
        if ret_stderr:
            ret_stderr = b''.join(ret_stderr)
        return (ret_stdout.decode('utf-8', 'ignore') if ret_stdout else None,
                ret_stderr.decode('utf-8') if ret_stderr else None,
                process.returncode)

    def cmd_expect(self, command, **kwargs):
        from pexpect import spawnu

        # prepare the environ, based on the system + our own env
        env = copy(environ)
        env.update(self.environ)

        # prepare the process
        kwargs.setdefault('env', env)
        kwargs.setdefault('show_output', self.log_level > 1)
        sensible = kwargs.pop('sensible', False)
        show_output = kwargs.pop('show_output')

        if show_output:
            if IS_PY3:
                kwargs['logfile'] = codecs.getwriter('utf8')(stdout.buffer)
            else:
                kwargs['logfile'] = codecs.getwriter('utf8')(stdout)

        if not sensible:
            self.debug('Run (expect) {0!r}'.format(command))
        else:
            self.debug('Run (expect) {0!r} ...'.format(command.split()[0]))

        self.debug('Cwd {}'.format(kwargs.get('cwd')))
        return spawnu(command, **kwargs)

    def check_configuration_tokens(self):
        '''Ensure the spec file is 'correct'.
        '''
        self.info('Check configuration tokens')
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

        orientation = get('app', 'orientation', 'landscape')
        if orientation not in ('landscape', 'portrait', 'all', 'sensorLandscape'):
            adderror('[app] "orientation" have an invalid value')

        if errors:
            self.error('{0} error(s) found in the buildozer.spec'.format(
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
                self.error("In section [app]: {} is deprecated, rename to {}!".format(
                    entry_old, entry_new))

    def check_build_layout(self):
        '''Ensure the build (local and global) directory layout and files are
        ready.
        '''
        self.info('Ensure build layout')

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
            e = self.error
            e('virtualenv is needed to install pure-Python modules, but')
            e('virtualenv does not support nesting, and you are running')
            e('buildozer in one. Please run buildozer outside of a')
            e('virtualenv instead.')
            exit(1)

        # did we already installed the libs ?
        if exists(self.applibs_dir) and \
           self.state.get('cache.applibs', '') == requirements:
                self.debug('Application requirements already installed, pass')
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
        self.debug('Install requirement {} in virtualenv'.format(module))
        self.cmd('pip install --target={} {}'.format(self.applibs_dir, module),
                 env=self.env_venv,
                 cwd=self.buildozer_dir)

    def check_garden_requirements(self):
        '''Ensure required garden packages are available to be included.
        '''
        garden_requirements = self.config.getlist('app',
                'garden_requirements', '')

        # have we installed the garden packages?
        if exists(self.gardenlibs_dir) and \
                self.state.get('cache.gardenlibs', '') == garden_requirements:
            self.debug('Garden requirements already installed, pass')
            return

        # we're going to reinstall all the garden libs.
        self.rmdir(self.gardenlibs_dir)

        # but if we don't have requirements, or if the user removed everything,
        # don't do anything.
        if not garden_requirements:
            self.state['cache.gardenlibs'] = garden_requirements
            return

        self._ensure_virtualenv()
        self.cmd('pip install Kivy-Garden==0.1.1', env=self.env_venv)

        # recreate gardenlibs
        self.mkdir(self.gardenlibs_dir)

        for requirement in garden_requirements:
            self._install_garden_package(requirement)

        # save gardenlibs state
        self.state['cache.gardenlibs'] = garden_requirements

    def _install_garden_package(self, package):
        self._ensure_virtualenv()
        self.debug('Install garden package {} in buildozer_dir'.format(package))
        self.cmd('garden install --app {}'.format(package),
                env=self.env_venv,
                cwd=self.buildozer_dir)

    def _ensure_virtualenv(self):
        if hasattr(self, 'venv'):
            return
        self.venv = join(self.buildozer_dir, 'venv')
        if not self.file_exists(self.venv):
            self.cmd('virtualenv --python=python2.7 ./venv',
                    cwd=self.buildozer_dir)

        # read virtualenv output and parse it
        output = self.cmd('bash -c "source venv/bin/activate && env"',
                get_stdout=True,
                cwd=self.buildozer_dir)
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
        self.debug('Create directory {0}'.format(dn))
        makedirs(dn)

    def rmdir(self, dn):
        if not exists(dn):
            return
        self.debug('Remove directory and subdirectory {}'.format(dn))
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
        self.debug('Rename {0} to {1}'.format(source, target))
        if not os.path.isdir(os.path.dirname(target)):
            self.error(('Rename {0} to {1} fails because {2} is not a '
                        'directory').format(source, target, target))
        move(source, target)

    def file_copy(self, source, target, cwd=None):
        if cwd:
            source = join(cwd, source)
            target = join(cwd, target)
        self.debug('Copy {0} to {1}'.format(source, target))
        copyfile(source, target)

    def file_extract(self, archive, cwd=None):
        if archive.endswith('.tgz') or archive.endswith('.tar.gz'):
            # XXX tarfile doesn't work for NDK-r8c :(
            #tf = tarfile.open(archive, 'r:*')
            #tf.extractall(path=cwd)
            #tf.close()
            self.cmd('tar xzf {0}'.format(archive), cwd=cwd)
            return

        if archive.endswith('.tbz2') or archive.endswith('.tar.bz2'):
            # XXX same as before
            self.cmd('tar xjf {0}'.format(archive), cwd=cwd)
            return

        if archive.endswith('.bin'):
            # To process the bin files for linux and darwin systems
            self.cmd('chmod a+x {0}'.format(archive),cwd=cwd)
            self.cmd('./{0}'.format(archive),cwd=cwd)
            return

        if archive.endswith('.zip'):
            self.cmd('unzip {}'.format(join(cwd, archive)), cwd=cwd)
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
        self.info('Clean the platform build directory')
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
            stdout.write('- Download {}\r'.format(progression))
            stdout.flush()

        url = url + filename
        if cwd:
            filename = join(cwd, filename)
        if self.file_exists(filename):
            unlink(filename)

        self.debug('Downloading {0}'.format(url))
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
                self.debug('Captured version: {0}'.format(version))
                return version

        raise Exception('Missing version or version.regex + version.filename')

    def build_application(self):
        self._copy_application_sources()
        self._copy_application_libs()
        self._copy_garden_libs()
        self._add_sitecustomize()

    def _copy_application_sources(self):
        # XXX clean the inclusion/exclusion algo.
        source_dir = realpath(self.config.getdefault('app', 'source.dir', '.'))
        include_exts = self.config.getlist('app', 'source.include_exts', '')
        exclude_exts = self.config.getlist('app', 'source.exclude_exts', '')
        exclude_dirs = self.config.getlist('app', 'source.exclude_dirs', '')
        exclude_patterns = self.config.getlist('app', 'source.exclude_patterns', '')
        include_patterns = self.config.getlist('app',
                                               'source.include_patterns',
                                               '')
        app_dir = self.app_dir

        self.debug('Copy application source from {}'.format(source_dir))

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
                    ext = ext[1:]
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
                self.debug('Copy {0}'.format(sfn))
                copyfile(sfn, rfn)

    def _copy_application_libs(self):
        # copy also the libs
        copytree(self.applibs_dir, join(self.app_dir, '_applibs'))

    def _copy_garden_libs(self):
        if exists(self.gardenlibs_dir):
            copytree(self.gardenlibs_dir, join(self.app_dir, 'libs'))

    def _add_sitecustomize(self):
        copyfile(join(dirname(__file__), 'sitecustomize.py'),
                join(self.app_dir, 'sitecustomize.py'))

        main_py = join(self.app_dir, 'service', 'main.py')
        if not self.file_exists(main_py):
            #self.error('Unable to patch main_py to add applibs directory.')
            return

        header = (b'import sys, os; '
                   b'sys.path = [os.path.join(os.getcwd(),'
                   b'"..", "_applibs")] + sys.path\n')
        with open(main_py, 'rb') as fd:
            data = fd.read()
        data = header + data
        with open(main_py, 'wb') as fd:
            fd.write(data)
        self.info('Patched service/main.py to include applibs')

    def namify(self, name):
        '''Return a "valid" name from a name with lot of invalid chars
        (allowed characters: a-z, A-Z, 0-9, -, _)
        '''
        return re.sub('[^a-zA-Z0-9_\-]', '_', name)

    @property
    def root_dir(self):
        return realpath(dirname(self.specfilename))

    @property
    def buildozer_dir(self):
        if self.build_dir:
            return self.build_dir
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
    def gardenlibs_dir(self):
        return join(self.buildozer_dir, 'libs')

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
            except:
                raise
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
            doc = [x for x in
                    meth.__doc__.strip().splitlines()][0].strip()
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
        while args:
            if not args[0].startswith('-'):
                break
            arg = args.pop(0)

            if arg in ('-v', '--verbose'):
                self.log_level = 2

            elif arg in ('-h', '--help'):
                self.usage()
                exit(0)

            elif arg in ('-p', '--profile'):
                self.config_profile = args.pop(0)

            elif arg == '--version':
                print('Buildozer {0}'.format(__version__))
                exit(0)

        self._merge_config_profile()

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
            print('Unknown command/target {}'.format(self.translate_target(command, inverse=True)))
            exit(1)

        self.set_target(command)
        self.target.run_commands(args)

    def check_root(self):
        '''If effective user id is 0, display a warning and require
        user input to continue (or to cancel)'''

        if IS_PY3:
            input_func = input
        else:
            input_func = raw_input

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
                cont = input_func('Are you sure you want to continue [y/n]? ')

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
            self.info('Clean the global build directory')
            if not exists(self.global_buildozer_dir):
                return
            rmtree(self.global_buildozer_dir)

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

    #
    # Private
    #

    def _merge_config_profile(self):
        profile = self.config_profile
        if not profile:
            return
        for section in self.config.sections():

            # extract the profile part from the section name
            # example: [app@default,hd]
            parts = section.split('@', 1)
            if len(parts) < 2:
                continue

            # create a list that contain all the profiles of the current section
            # ['default', 'hd']
            section_base, section_profiles = parts
            section_profiles = section_profiles.split(',')
            if profile not in section_profiles:
                continue

            # the current profile is one available in the section
            # merge with the general section, or make it one.
            if not self.config.has_section(section_base):
                self.config.add_section(section_base)
            for name, value in self.config.items(section):
                print('merged ({}, {}) into {} (profile is {})'.format(name,
                        value, section_base, profile))
                self.config.set(section_base, name, value)



    def _get_config_list_values(self, *args, **kwargs):
        kwargs['with_values'] = True
        return self._get_config_list(*args, **kwargs)

    def _get_config_list(self, section, token, default=None, with_values=False):
        # monkey-patch method for ConfigParser
        # get a key as a list of string, separated from the comma

        # check if an env var exists that should replace the file config
        set_config_token_from_env(section, token, self.config)

        # if a section:token is defined, let's use the content as a list.
        l_section = '{}:{}'.format(section, token)
        if self.config.has_section(l_section):
            values = self.config.options(l_section)
            if with_values:
                return ['{}={}'.format(key, self.config.get(l_section, key)) for
                        key in values]
            else:
                return [x.strip() for x in values]

        values = self.config.getdefault(section, token, '')
        if not values:
            return default
        values = values.split(',')
        if not values:
            return default
        return [x.strip() for x in values]

    def _get_config_default(self, section, token, default=None):
        # monkey-patch method for ConfigParser
        # get an appropriate env var if it exists, else
        # get a key in a section, or the default

        # check if an env var exists that should replace the file config
        set_config_token_from_env(section, token, self.config)

        if not self.config.has_section(section):
            return default
        if not self.config.has_option(section, token):
            return default
        return self.config.get(section, token)

    def _get_config_bool(self, section, token, default=False):
        # monkey-patch method for ConfigParser
        # get a key in a section, or the default

        # check if an env var exists that should replace the file config
        set_config_token_from_env(section, token, self.config)

        if not self.config.has_section(section):
            return default
        if not self.config.has_option(section, token):
            return default
        return self.config.getboolean(section, token)

    def _get_config_raw_default(self, section, token, default=None, section_sep="=", split_char=" "):
        l_section = '{}:{}'.format(section, token)
        if self.config.has_section(l_section):
            return [section_sep.join(item) for item in self.config.items(l_section)]
        if not self.config.has_option(section, token):
            return default.split(split_char)
        return self.config.get(section, token).split(split_char)


def set_config_from_envs(config):
    '''Takes a ConfigParser, and checks every section/token for an
    environment variable of the form SECTION_TOKEN, with any dots
    replaced by underscores. If the variable exists, sets the config
    variable to the env value.
    '''
    for section in config.sections():
        for token in config.options(section):
            set_config_token_from_env(section, token, config)

def set_config_token_from_env(section, token, config):
    '''Given a config section and token, checks for an appropriate
    environment variable. If the variable exists, sets the config entry to
    its value.

    The environment variable checked is of the form SECTION_TOKEN, all
    upper case, with any dots replaced by underscores.

    Returns True if the environment variable exists and was used, or
    False otherwise.

    '''
    env_var_name = ''.join([section.upper(), '_',
                            token.upper().replace('.', '_')])
    env_var = os.environ.get(env_var_name)
    if env_var is None:
        return False
    config.set(section, token, env_var)
    return True
