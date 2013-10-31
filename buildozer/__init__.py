'''

Layout directory for buildozer:

    build/
        <targetname>/
            platform/ - all the platform files necessary
            app/ - compiled application


'''

__version__ = '0.9'

import fcntl
import os
import re
import shelve
import SimpleHTTPServer
import socket
import SocketServer
import sys
import zipfile
from select import select
from sys import stdout, stderr, stdin, exit
from urllib import FancyURLopener
from re import search
from ConfigParser import SafeConfigParser
from os.path import join, exists, dirname, realpath, splitext, expanduser
from subprocess import Popen, PIPE
from os import environ, unlink, rename, walk, sep, listdir, makedirs
from copy import copy
from shutil import copyfile, rmtree, copytree
from fnmatch import fnmatch

# windows does not have termios...
try:
    import termios
    import tty
    has_termios = True
except ImportError:
    has_termios = False

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;{0}m"
BOLD_SEQ = "\033[1m"
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
USE_COLOR = 'NO_COLOR' not in environ
# error, info, debug
LOG_LEVELS_C = (RED, BLUE, BLACK)
LOG_LEVELS_T = 'EID'
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


class Buildozer(object):

    standard_cmds = ('clean', 'update', 'debug', 'release', 
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
        self.config.getlist = self._get_config_list
        self.config.getdefault = self._get_config_default
        self.config.getbooldefault = self._get_config_bool

        if exists(filename):
            self.config.read(filename)
            self.check_configuration_tokens()

        try:
            self.log_level = int(self.config.getdefault(
                'buildozer', 'log_level', '1'))
        except:
            pass

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
        # FIXME WHY the hell we need to close/reopen the state to sync the build
        # id ???
        self.state.close()
        self.state = shelve.open(join(self.buildozer_dir, 'state.db'))

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
            color = COLOR_SEQ.format(30 + LOG_LEVELS_C[level])
            print ''.join((RESET_SEQ, color, '# ', msg, RESET_SEQ))
        else:
            print LOG_LEVELS_T[level], msg

    def debug(self, msg):
        self.log(2, msg)

    def info(self, msg):
        self.log(1, msg)

    def error(self, msg):
        self.log(0, msg)

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
        raise Exception(msg + 'not found')

    def cmd(self, command, **kwargs):
        #print ' '.join(['{0}={1}'.format(*args) for args in
        #    self.environ.iteritems()])

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

        # open the process
        process = Popen(command, **kwargs)

        # prepare fds
        fd_stdout = process.stdout.fileno()
        fd_stderr = process.stderr.fileno()
        fcntl.fcntl(
            fd_stdout, fcntl.F_SETFL,
            fcntl.fcntl(fd_stdout, fcntl.F_GETFL) | os.O_NONBLOCK)
        fcntl.fcntl(
            fd_stderr, fcntl.F_SETFL,
            fcntl.fcntl(fd_stderr, fcntl.F_GETFL) | os.O_NONBLOCK)

        ret_stdout = [] if get_stdout else None
        ret_stderr = [] if get_stderr else None
        while True:
            readx = select([fd_stdout, fd_stderr], [], [])[0]
            if fd_stdout in readx:
                chunk = process.stdout.read()
                if chunk == '':
                    break
                if get_stdout:
                    ret_stdout.append(chunk)
                if show_output:
                    stdout.write(chunk)
            if fd_stderr in readx:
                chunk = process.stderr.read()
                if chunk == '':
                    break
                if get_stderr:
                    ret_stderr.append(chunk)
                if show_output:
                    stderr.write(chunk)

        stdout.flush()
        stderr.flush()

        process.communicate()
        if process.returncode != 0 and break_on_error:
            self.error('Command failed: {0}'.format(command))
            raise BuildozerCommandException()
        if ret_stdout:
            ret_stdout = ''.join(ret_stdout)
        if ret_stderr:
            ret_stderr = ''.join(ret_stderr)
        return (ret_stdout, ret_stderr, process.returncode)

    def check_configuration_tokens(self):
        '''Ensure the spec file is 'correct'.
        '''
        self.info('Check configuration tokens')
        get = self.config.getdefault
        errors = []
        adderror = errors.append
        if not get('app', 'title', ''):
            adderror('[app] "title" is missing')
        if not get('app', 'package.name', ''):
            adderror('[app] "package.name" is missing')
        if not get('app', 'source.dir', ''):
            adderror('[app] "source.dir" is missing')

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
        if orientation not in ('landscape', 'portrait', 'all'):
            adderror('[app] "orientation" have an invalid value')

        if errors:
            self.error('{0} error(s) found in the buildozer.spec'.format(
                len(errors)))
            for error in errors:
                print error
            exit(1)


    def check_build_layout(self):
        '''Ensure the build (local and global) directory layout and files are
        ready.
        '''
        self.info('Ensure build layout')

        if not exists(self.specfilename):
            print 'No {0} found in the current directory. Abandon.'.format(
                    self.specfilename)
            exit(1)

        # create global dir
        self.mkdir(self.global_buildozer_dir)
        self.mkdir(self.global_cache_dir)

        # create local dir
        specdir = dirname(self.specfilename)
        self.mkdir(join(specdir, '.buildozer'))
        self.mkdir(join(specdir, 'bin'))
        self.mkdir(self.applibs_dir)
        self.state = shelve.open(join(self.buildozer_dir, 'state.db'))

        if self.targetname:
            target = self.targetname
            self.mkdir(join(self.global_platform_dir, target, 'platform'))
            self.mkdir(join(specdir, '.buildozer', target, 'platform'))
            self.mkdir(join(specdir, '.buildozer', target, 'app'))

    def check_application_requirements(self):
        '''Ensure the application requirements are all available and ready to be
        packaged as well.
        '''
        requirements = self.config.getlist('app', 'requirements', '')
        target_available_packages = self.target.get_available_packages()

        # remove all the requirements that the target can compile
        requirements = [x for x in requirements if x not in
                target_available_packages]

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
        # resetup distribute, just in case
        self.debug('Install distribute')
        self.cmd('curl http://python-distribute.org/distribute_setup.py | venv/bin/python', get_stdout=True, cwd=self.buildozer_dir)

        self.debug('Install requirement {} in virtualenv'.format(module))
        self.cmd('pip-2.7 install --download-cache={} --target={} {}'.format(
                self.global_cache_dir, self.applibs_dir, module),
                env=self.env_venv,
                cwd=self.buildozer_dir)

    def _ensure_virtualenv(self):
        if hasattr(self, 'venv'):
            return
        self.venv = join(self.buildozer_dir, 'venv')
        if not self.file_exists(self.venv):
            self.cmd('virtualenv-2.7 --python=python2.7 ./venv',
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

    def file_exists(self, *args):
        return exists(join(*args))

    def file_rename(self, source, target, cwd=None):
        if cwd:
            source = join(cwd, source)
            target = join(cwd, target)
        self.debug('Rename {0} to {1}'.format(source, target))
        rename(source, target)

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

        if archive.endswith('.zip'):
            archive = join(cwd, archive)
            zf = zipfile.ZipFile(archive)
            zf.extractall(path=cwd)
            zf.close()
            return

        raise Exception('Unhandled extraction for type {0}'.format(archive))

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
            print '- Download', progression, '\r',
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
        self._add_sitecustomize()

    def _copy_application_sources(self):
        # XXX clean the inclusion/exclusion algo.
        source_dir = realpath(self.config.getdefault('app', 'source.dir', '.'))
        include_exts = self.config.getlist('app', 'source.include_exts', '')
        exclude_exts = self.config.getlist('app', 'source.exclude_exts', '')
        exclude_dirs = self.config.getlist('app', 'source.exclude_dirs', '')
        exclude_patterns = self.config.getlist('app', 'source.exclude_patterns', '')
        app_dir = self.app_dir

        self.debug('Copy application source from {}'.format(source_dir))

        rmtree(self.app_dir)

        for root, dirs, files in walk(source_dir):
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
                if is_excluded:
                    continue

                # pattern matching
                for pattern in exclude_patterns:
                    if fnmatch(filtered_root, pattern):
                        is_excluded = True
                        break
                if is_excluded:
                    continue

            for fn in files:
                # avoid hidden files
                if fn.startswith('.'):
                    continue

                # exclusion by pattern matching
                is_excluded = False
                dfn = fn.lower()
                if filtered_root:
                    dfn = join(filtered_root, fn)
                for pattern in exclude_patterns:
                    if fnmatch(dfn, pattern):
                        is_excluded = True
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

    def _add_sitecustomize(self):
        copyfile(join(dirname(__file__), 'sitecustomize.py'),
                join(self.app_dir, 'sitecustomize.py'))

        main_py = join(self.app_dir, 'service', 'main.py')
        if not self.file_exists(main_py):
            #self.error('Unable to patch main_py to add applibs directory.')
            return

        header = ('import sys, os; '
                  'sys.path = [os.path.join(os.getcwd(),'
                  '"..", "_applibs")] + sys.path\n')
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
        return realpath(join(dirname(self.specfilename)))

    @property
    def buildozer_dir(self):
        return join(self.root_dir, '.buildozer')

    @property
    def bin_dir(self):
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
            except:
                raise
                pass

    def usage(self):
        print 'Usage:'
        print '    buildozer [--profile <name>] [--verbose] [target] <command>...'
        print '    buildozer --version'
        print
        print 'Available targets:'
        targets = list(self.targets())
        for target, m in targets:
            doc = m.__doc__.strip().splitlines()[0].strip()
            print '  {0:<18} {1}'.format(target, doc)

        print
        print 'Global commands (without target):'
        cmds = [x for x in dir(self) if x.startswith('cmd_')]
        for cmd in cmds:
            name = cmd[4:]
            meth = getattr(self, cmd)

            doc = [x for x in
                    meth.__doc__.strip().splitlines()][0].strip()
            print '  {0:<18} {1}'.format(name, doc)

        print
        print 'Target commands:'
        print '  clean      Clean the target environment'
        print '  update     Update the target dependencies'
        print '  debug      Build the application in debug mode'
        print '  release    Build the application in release mode'
        print '  deploy     Deploy the application on the device'
        print '  run        Run the application on the device'
        print '  serve      Serve the bin directory via SimpleHTTPServer'

        for target, m in targets:
            mt = m.get_target(self)
            commands = mt.get_custom_commands()
            if not commands:
                continue
            print
            print 'Target "{0}" commands:'.format(target)
            for command, doc in commands:
                doc = doc.strip().splitlines()[0].strip()
                print '  {0:<18} {1}'.format(command, doc)

        print


    def run_default(self):
        self.check_build_layout()
        if 'buildozer:defaultcommand' not in self.state:
            print 'No default command set.'
            print 'Use "buildozer setdefault <command args...>"'
            print 'Use "buildozer help" for a list of all commands"'
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
                print 'Buildozer {0}'.format(__version__)
                exit(0)

        self._merge_config_profile()

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
            print 'Unknown command/target', command
            exit(1)

        self.set_target(command)
        self.target.run_commands(args)

    def cmd_init(self, *args):
        '''Create a initial buildozer.spec in the current directory
        '''
        if exists('buildozer.spec'):
            print 'ERROR: You already have a buildozer.spec file.'
            exit(1)
        copyfile(join(dirname(__file__), 'default.spec'), 'buildozer.spec')
        print 'File buildozer.spec created, ready to customize!'

    def cmd_clean(self, *args):
        '''Clean the whole Buildozer environment.
        '''
        pass

    def cmd_help(self, *args):
        '''Show the Buildozer help.
        '''
        self.usage()

    def cmd_setdefault(self, *args):
        '''Set the default command to do when to arguments are given
        '''
        self.check_build_layout()
        self.state['buildozer:defaultcommand'] = args

    def cmd_version(self, *args):
        '''Show the Buildozer version
        '''
        print 'Buildozer {0}'.format(__version__)

    def cmd_serve(self, *args):
        '''Serve the bin directory via SimpleHTTPServer
        '''
        os.chdir(self.bin_dir)
        handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        httpd = SocketServer.TCPServer(("", SIMPLE_HTTP_SERVER_PORT), handler)
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
                print 'merged ({}, {}) into {} (profile is {})'.format(name,
                        value, section_base, profile)
                self.config.set(section_base, name, value)




    def _get_config_list(self, section, token, default=None):
        # monkey-patch method for ConfigParser
        # get a key as a list of string, seperated from the comma

        # if a section:token is defined, let's use the content as a list.
        l_section = '{}:{}'.format(section, token)
        if self.config.has_section(l_section):
            values = self.config.options(l_section)
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
        # get a key in a section, or the default
        if not self.config.has_section(section):
            return default
        if not self.config.has_option(section, token):
            return default
        return self.config.get(section, token)

    def _get_config_bool(self, section, token, default=False):
        # monkey-patch method for ConfigParser
        # get a key in a section, or the default
        if not self.config.has_section(section):
            return default
        if not self.config.has_option(section, token):
            return default
        return self.config.getboolean(section, token)


class BuildozerRemote(Buildozer):
    def run_command(self, args):
        while args:
            if not args[0].startswith('-'):
                break
            arg = args.pop(0)

            if arg in ('-v', '--verbose'):
                self.log_level = 2

            elif arg in ('-p', '--profile'):
                self.config_profile = args.pop(0)

            elif arg in ('-h', '--help'):
                self.usage()
                exit(0)

            elif arg == '--version':
                print 'Buildozer (remote) {0}'.format(__version__)
                exit(0)

        self._merge_config_profile()

        if len(args) < 2:
            self.usage()
            return

        remote_name = args[0]
        remote_section = 'remote:{}'.format(remote_name)
        if not self.config.has_section(remote_section):
            self.error('Unknown remote "{}", must be configured first.'.format(
                remote_name))
            return

        self.remote_host = remote_host = self.config.get(
                remote_section, 'host', '')
        self.remote_port = self.config.get(
                remote_section, 'port', '22')
        self.remote_user = remote_user = self.config.get(
                remote_section, 'user', '')
        self.remote_build_dir = remote_build_dir = self.config.get(
                remote_section, 'build_directory', '')
        self.remote_identity = self.config.get(
                remote_section, 'identity', '')
        if not remote_host:
            self.error('Missing "host = " for {}'.format(remote_section))
            return
        if not remote_user:
            self.error('Missing "user = " for {}'.format(remote_section))
            return
        if not remote_build_dir:
            self.error('Missing "build_directory = " for {}'.format(remote_section))
            return

        # fake the target
        self.targetname = 'remote'
        self.check_build_layout()

        # prepare our source code
        self.info('Prepare source code to sync')
        self._copy_application_sources()
        self._ssh_connect()
        try:
            self._ensure_buildozer()
            self._sync_application_sources()
            self._do_remote_commands(args[1:])
            self._ssh_sync(os.getcwd(), mode='get')
        finally:
            self._ssh_close()

    def _ssh_connect(self):
        self.info('Connecting to {}'.format(self.remote_host))
        import paramiko
        self._ssh_client = client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.load_system_host_keys()
        kwargs = {}
        if self.remote_identity:
            kwargs['key_filename'] = expanduser(self.remote_identity)
        client.connect(self.remote_host, username=self.remote_user,
                port=int(self.remote_port), **kwargs)
        self._sftp_client = client.open_sftp()

    def _ssh_close(self):
        self.debug('Closing remote connection')
        self._sftp_client.close()
        self._ssh_client.close()

    def _ensure_buildozer(self):
        s = self._sftp_client
        root_dir = s.normalize('.')
        self.remote_build_dir = join(root_dir, self.remote_build_dir,
                self.package_full_name)
        self.debug('Remote build directory: {}'.format(self.remote_build_dir))
        self._ssh_mkdir(self.remote_build_dir)
        self._ssh_sync(__path__[0])

    def _sync_application_sources(self):
        self.info('Synchronize application sources')
        self._ssh_sync(self.app_dir)

        # create custom buildozer.spec
        self.info('Create custom buildozer.spec')
        config = SafeConfigParser()
        config.read('buildozer.spec')
        config.set('app', 'source.dir', 'app')

        fn = join(self.remote_build_dir, 'buildozer.spec')
        fd = self._sftp_client.open(fn, 'wb')
        config.write(fd)
        fd.close()

    def _do_remote_commands(self, args):
        self.info('Execute remote buildozer')
        cmd = (
            'source ~/.profile;'
            'cd {0};'
            'env PYTHONPATH={0}:$PYTHONPATH '
            'python -c "import buildozer, sys;'
            'buildozer.Buildozer().run_command(sys.argv[1:])" {1} {2} 2>&1').format(
            self.remote_build_dir,
            '--verbose' if self.log_level == 2 else '',
            ' '.join(args),
            )
        self._ssh_command(cmd)

    def _ssh_mkdir(self, *args):
        directory = join(*args)
        self.debug('Create remote directory {}'.format(directory))
        try:
            self._sftp_client.mkdir(directory)
        except IOError:
            # already created?
            try:
                self._sftp_client.stat(directory)
            except IOError:
                self.error('Unable to create remote directory {}'.format(directory))
                raise

    def _ssh_sync(self, directory, mode='put'):
        self.debug('Syncing {} directory'.format(directory))
        directory = realpath(directory)
        base_strip = directory.rfind('/')
        if mode == 'get':
            local_dir = join(directory,'bin')
            remote_dir = join(self.remote_build_dir, 'bin')
            if not os.path.exists(local_dir):
                os.path.makedirs(local_dir)
            for _file in self._sftp_client.listdir(path=remote_dir):
                self._sftp_client.get(join(remote_dir, _file),
                                      join(local_dir, _file))
            return
        for root, dirs, files in walk(directory):
            self._ssh_mkdir(self.remote_build_dir, root[base_strip + 1:])
            for fn in files:
                if splitext(fn)[1] in ('.pyo', '.pyc', '.swp'):
                    continue
                local_file = join(root, fn)
                remote_file = join(self.remote_build_dir, root[base_strip + 1:], fn)
                self.debug('Sync {} -> {}'.format(local_file, remote_file))
                self._sftp_client.put(local_file, remote_file)

    def _ssh_command(self, command):
        self.debug('Execute remote command {}'.format(command))
        #shell = self._ssh_client.invoke_shell()
        #shell.sendall(command)
        #shell.sendall('\nexit\n')
        transport = self._ssh_client.get_transport()
        channel = transport.open_session()
        try:
            channel.exec_command(command)
            self._interactive_shell(channel)
        finally:
            channel.close()

    def _interactive_shell(self, chan):
        if has_termios:
            self._posix_shell(chan)
        else:
            self._windows_shell(chan)

    def _posix_shell(self, chan):
        oldtty = termios.tcgetattr(stdin)
        try:
            #tty.setraw(stdin.fileno())
            #tty.setcbreak(stdin.fileno())
            chan.settimeout(0.0)

            while True:
                r, w, e = select([chan, stdin], [], [])
                if chan in r:
                    try:
                        x = chan.recv(128)
                        if len(x) == 0:
                            print '\r\n*** EOF\r\n',
                            break
                        stdout.write(x)
                        stdout.flush()
                        #print len(x), repr(x)
                    except socket.timeout:
                        pass
                if stdin in r:
                    x = stdin.read(1)
                    if len(x) == 0:
                        break
                    chan.sendall(x)
        finally:
            termios.tcsetattr(stdin, termios.TCSADRAIN, oldtty)

    # thanks to Mike Looijmans for this code
    def _windows_shell(self,chan):
        import threading

        stdout.write("Line-buffered terminal emulation. Press F6 or ^Z to send EOF.\r\n\r\n")

        def writeall(sock):
            while True:
                data = sock.recv(256)
                if not data:
                    stdout.write('\r\n*** EOF ***\r\n\r\n')
                    stdout.flush()
                    break
                stdout.write(data)
                stdout.flush()

        writer = threading.Thread(target=writeall, args=(chan,))
        writer.start()

        try:
            while True:
                d = stdin.read(1)
                if not d:
                    break
                chan.send(d)
        except EOFError:
            # user hit ^Z or F6
            pass

def run():
    try:
        Buildozer().run_command(sys.argv[1:])
    except BuildozerCommandException:
        # don't show the exception in the command line. The log already show the
        # command failed.
        pass
    except BuildozerException as error:
        Buildozer().error('%s' % error)

def run_remote():
    try:
        BuildozerRemote().run_command(sys.argv[1:])
    except BuildozerCommandException:
        pass
    except BuildozerException as error:
        Buildozer().error('%s' % error)
