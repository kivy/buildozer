'''

Layout directory for buildozer:

    build/
        <targetname>/
            platform/ - all the platform files necessary
            app/ - compiled application


'''

import shelve
import zipfile
import sys
from sys import stdout, exit
from urllib import urlretrieve
from re import search
from ConfigParser import SafeConfigParser
from os.path import join, exists, dirname, realpath, splitext
from subprocess import Popen, PIPE
from os import environ, mkdir, unlink, rename, walk, sep, listdir
from copy import copy
from shutil import copyfile, rmtree


class Buildozer(object):

    def __init__(self, filename='buildozer.spec', target=None):
        super(Buildozer, self).__init__()
        self.environ = {}
        self.specfilename = filename
        self.state = None
        self.config = SafeConfigParser()
        self.config.getlist = self._get_config_list
        self.config.getdefault = self._get_config_default
        self.config.read(filename)

        self.targetname = None
        self.target = None
        if target:
            self.set_target(target)

    def set_target(self, target):
        self.targetname = target
        m = __import__('buildozer.targets.%s' % target, fromlist=['buildozer'])
        self.target = m.get_target(self)

    def _get_config_list(self, section, token, default=None):
        values = self.config.getdefault(section, token, default).split(',')
        return [x.strip() for x in values]

    def _get_config_default(self, section, token, default=None):
        if not self.config.has_section(section):
            return default
        if not self.config.has_option(section, token):
            return default
        return self.config.get(section, token)

    def log(self, msg):
        print '-', msg

    def error(self, msg):
        print 'E', msg
        exit(1)

    def checkbin(self, msg, fn):
        self.log('Search for {0}'.format(msg))
        if exists(fn):
            return realpath(fn)
        for dn in environ['PATH'].split(':'):
            rfn = realpath(join(dn, fn))
            if exists(rfn):
                self.log(' -> found at {0}'.format(rfn))
                return rfn
        raise Exception(msg + 'not found')

    def cmd(self, command, **kwargs):
        #print ' '.join(['{0}={1}'.format(*args) for args in
        #    self.environ.iteritems()])
        env = copy(environ)
        env.update(self.environ)
        kwargs.setdefault('env', env)
        self.log('run %r' % command)
        c = Popen(command, shell=True, stdout=PIPE, stderr=PIPE, **kwargs)
        ret = c.communicate()
        if c.returncode != 0:
            print '--- command failed'
            print '-- stdout output'
            print ret[0]
            print '-- stderr output'
            print ret[1]
            print '--- end commend failed'
        return ret

    def do_config_requirements(self):
        pass

    def ensure_build_layout(self):
        if not exists(self.specfilename):
            print 'No {0} found in the current directory. Abandon.'.format(
                    self.specfilename)
            exit(1)

        specdir = dirname(self.specfilename)
        self.mkdir(join(specdir, '.buildozer', self.targetname))
        self.mkdir(join(specdir, '.buildozer', self.targetname, 'platform'))
        self.mkdir(join(specdir, '.buildozer', self.targetname, 'app'))
        self.mkdir(join(specdir, 'bin'))
        self.state = shelve.open(join(self.platform_dir, 'state.db'))

    def mkdir(self, dn):
        if exists(dn):
            return
        mkdir(dn)

    def file_exists(self, *args):
        return exists(join(*args))

    def file_rename(self, source, target, cwd=None):
        if cwd:
            source = join(cwd, source)
            target = join(cwd, target)
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

        self.log('Downloading {0}'.format(url))
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
                self.log('Captured version: {0}'.format(version))
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
                self.log('Copy {0}'.format(sfn))
                copyfile(sfn, rfn)

    @property
    def platform_dir(self):
        return realpath(
            join(dirname(self.specfilename), '.buildozer',
            self.targetname, 'platform'))

    @property
    def app_dir(self):
        return realpath(join(
            dirname(self.specfilename), '.buildozer',
            self.targetname, 'app'))

    @property
    def bin_dir(self):
        return realpath(join(
            dirname(self.specfilename), 'bin'))

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
        print 'Usage: buildozer [target] [command1] [command2]'
        print
        print 'Available targets:'
        for target, m in self.targets():
            print '  ' + target
            doc = m.__doc__.strip().splitlines()[0]
            print '    ' + doc

        print
        print 'Global commands (without target):'
        cmds = [x for x in dir(self) if x.startswith('cmd_')]
        for cmd in cmds:
            name = cmd[4:]
            meth = getattr(self, cmd)

            print '  ' + name
            doc = '\n'.join(['    ' + x for x in
                meth.__doc__.strip().splitlines()])
            print doc

        print
        print 'Target commands:'
        print '  clean'
        print '    Clean the target environment'
        print '  update'
        print '    Update the target dependencies'
        print '  debug'
        print '    Build the application in debug mode'
        print '  release'
        print '    Build the application in release mode'
        print '  deploy'
        print '    Deploy the application on the device'
        print '  run'
        print '    Run the application on the device'
        print


    def run_default(self):
        self.ensure_build_layout()
        if 'buildozer:defaultcommand' not in self.state:
            print 'No default command set.'
            print 'Use "buildozer setdefault <command args...>"'
            exit(1)
        cmd = self.state['buildozer:defaultcommand']
        self.run_command(*cmd)

    def run_command(self, args):
        if '-h' in args or '--help' in args:
            self.usage()
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

    def prepare_for_build(self):
        self.log('Preparing build')

        self.log('Ensure build layout')
        self.ensure_build_layout()

        self.log('Check configuration tokens')
        self.do_config_requirements()

        self.log('Check requirements for %s' % self.targetname)
        self.target.check_requirements()

        self.log('Install platform')
        self.target.install_platform()

        self.log('Compile platform')
        self.target.compile_platform()

    def build(self):
        self.log('Build the application')
        self.build_application()

        self.log('Package the application')
        self.target.build_package()

    def cmd_init(self, *args):
        '''Create a initial buildozer.spec in the current directory
        '''
        copyfile((dirname(__file__), 'default.spec'), 'buildozer.spec')
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
        self.ensure_build_layout()
        self.state['buildozer:defaultcommand'] = args

def run():
    Buildozer().run_command(sys.argv[1:])
