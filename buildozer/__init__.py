'''

Layout directory for buildozer:

    build/
        <targetname>/
            platform/ - all the platform files necessary
            app/ - compiled application


'''

__version__ = '0.3-dev'

import shelve
import zipfile
import sys
import fcntl
import os
from select import select
from sys import stdout, stderr, exit
from urllib import urlretrieve
from re import search
from ConfigParser import SafeConfigParser
from os.path import join, exists, dirname, realpath, splitext, expanduser
from subprocess import Popen, PIPE
from os import environ, unlink, rename, walk, sep, listdir, makedirs
from copy import copy
from shutil import copyfile, rmtree

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;{0}m"
BOLD_SEQ = "\033[1m"
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
USE_COLOR = 'NO_COLOR' not in environ
# error, info, debug
LOG_LEVELS_C = (RED, BLUE, BLACK)
LOG_LEVELS_T = 'EID'

class Buildozer(object):

    standard_cmds = ('clean', 'update', 'debug', 'release', 'deploy', 'run')

    def __init__(self, filename='buildozer.spec', target=None):
        super(Buildozer, self).__init__()
        self.log_level = 1
        self.environ = {}
        self.specfilename = filename
        self.state = None
        self.config = SafeConfigParser()
        self.config.getlist = self._get_config_list
        self.config.getdefault = self._get_config_default
        self.config.read(filename)

        try:
            self.log_level = int(self.config.getdefault(
                'buildozer', 'log_level', '1'))
        except:
            pass

        self.check_configuration_tokens()

        self.targetname = None
        self.target = None
        if target:
            self.set_target(target)

    def set_target(self, target):
        '''Set the target to use (one of buildozer.targets, such as "android")
        '''
        self.targetname = target
        m = __import__('buildozer.targets.%s' % target, fromlist=['buildozer'])
        self.target = m.get_target(self)
        self.check_build_layout()

    def prepare_for_build(self):
        '''Prepare the build.
        '''
        assert(self.target is not None)
        if hasattr(self.target, '_build_prepared'):
            return

        self.info('Preparing build')

        self.info('Check requirements for %s' % self.targetname)
        self.target.check_requirements()

        self.info('Install platform')
        self.target.install_platform()

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

        self.info('Build the application')
        self.build_application()

        self.info('Package the application')
        self.target.build_package()

        # flag to prevent multiple build
        self.target._build_done = True

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

        self.debug('Run %r' % command)

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
        if process.returncode != 0:
            self.error('Command failed: {0}'.format(command))
        if ret_stdout:
            ret_stdout = ''.join(ret_stdout)
        if ret_stderr:
            ret_stderr = ''.join(ret_stderr)
        return (ret_stdout, ret_stderr)

    def check_configuration_tokens(self):
        '''Ensure the spec file is 'correct'.
        '''
        self.info('Check configuration tokens')

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

        # create local dir
        specdir = dirname(self.specfilename)
        self.mkdir(join(specdir, '.buildozer'))
        self.mkdir(join(specdir, 'bin'))
        self.state = shelve.open(join(self.buildozer_dir, 'state.db'))

        if self.targetname:
            target = self.targetname
            self.mkdir(join(self.global_platform_dir, target, 'platform'))
            self.mkdir(join(specdir, '.buildozer', target, 'platform'))
            self.mkdir(join(specdir, '.buildozer', target, 'app'))

    def mkdir(self, dn):
        if exists(dn):
            return
        self.debug('Create directory {0}', dn)
        makedirs(dn)

    def file_exists(self, *args):
        return exists(join(*args))

    def file_rename(self, source, target, cwd=None):
        if cwd:
            source = join(cwd, source)
            target = join(cwd, target)
        self.debug('Rename {0} to {1}'.format(source, target))
        rename(source, target)

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
                        'Unable to found capture version in %r' % fn)
                version = match.groups()[0]
                self.debug('Captured version: {0}'.format(version))
                return version

        raise Exception('Missing version or version.regex + version.filename')

    def build_application(self):
        source_dir = realpath(self.config.getdefault('app', 'source.dir', '.'))
        include_exts = self.config.getlist('app', 'source.include_exts', '')
        exclude_exts = self.config.getlist('app', 'source.exclude_exts', '')
        app_dir = self.app_dir

        for root, dirs, files in walk(source_dir):
            # avoid hidden directory
            if True in [x.startswith('.') for x in root.split(sep)]:
                continue

            for fn in files:
                # avoid hidden files
                if fn.startswith('.'):
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
                rfn = realpath(join(app_dir, root[len(source_dir):], fn))

                # ensure the directory exists
                dfn = dirname(rfn)
                self.mkdir(dfn)

                # copy!
                self.debug('Copy {0}'.format(sfn))
                copyfile(sfn, rfn)

    @property
    def buildozer_dir(self):
        return realpath(join(
            dirname(self.specfilename), '.buildozer'))

    @property
    def platform_dir(self):
        return join(self.buildozer_dir, self.targetname, 'platform')

    @property
    def app_dir(self):
        return join(self.buildozer_dir, self.targetname, 'app')

    @property
    def bin_dir(self):
        return realpath(join(
            dirname(self.specfilename), 'bin'))

    @property
    def global_buildozer_dir(self):
        return join(expanduser('~'), '.buildozer')

    @property
    def global_platform_dir(self):
        return join(self.global_buildozer_dir, self.targetname, 'platform')



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
                m = __import__('buildozer.targets.%s' % target, fromlist=['buildozer'])
                yield target, m
            except:
                pass

    def usage(self):
        print 'Usage: buildozer [--verbose] [target] [command1] [command2]'
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
        print '  clean              Clean the target environment'
        print '  update             Update the target dependencies'
        print '  debug              Build the application in debug mode'
        print '  release            Build the application in release mode'
        print '  deploy             Deploy the application on the device'
        print '  run                Run the application on the device'

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

            if arg in ('-h', '--help'):
                self.usage()
                exit(0)

            if args == '--version':
                print 'Buildozer {0}'.format(__version__)
                exit(0)

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
            print 'Unknow command/target', command
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

    #
    # Private
    #

    def _get_config_list(self, section, token, default=None):
        # monkey-patch method for ConfigParser
        # get a key as a list of string, seperated from the comma
        values = self.config.getdefault(section, token, default).split(',')
        return [x.strip() for x in values]

    def _get_config_default(self, section, token, default=None):
        # monkey-patch method for ConfigParser
        # get a key in a section, or the default
        if not self.config.has_section(section):
            return default
        if not self.config.has_option(section, token):
            return default
        return self.config.get(section, token)


def run():
    Buildozer().run_command(sys.argv[1:])

