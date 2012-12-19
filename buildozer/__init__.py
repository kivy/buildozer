'''

Layout directory for buildozer:

    build/
        <targetname>/
            platform/ - all the platform files necessary
            app/ - compiled application


'''

import shelve
from sys import stdout, exit
from urllib import urlretrieve
from re import search
from ConfigParser import SafeConfigParser
from os.path import join, exists, dirname, realpath
from subprocess import Popen, PIPE
from os import environ, mkdir, unlink, rename
from copy import copy

class Buildozer(object):

    def __init__(self, filename, target):
        super(Buildozer, self).__init__()
        self.environ = copy(environ)
        self.targetname = target
        self.specfilename = filename
        self.state = None
        self.config = SafeConfigParser()
        self.config.read(filename)

        # resolve target
        m = __import__('buildozer.targets.%s' % target, fromlist=['buildozer'])
        self.target = m.get_target(self)

    def log(self, msg):
        print '-', msg

    def error(self, msg):
        print 'E', msg
        exit(-1)

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
        kwargs.setdefault('env', self.environ)
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

    def run(self):
        self.log('Build started')

        self.log('check configuration tokens')
        self.do_config_requirements()

        self.log('check requirements for %s' % self.targetname)
        self.target.check_requirements()

        self.log('ensure build layout')
        self.ensure_build_layout()

        self.log('install platform')
        self.target.install_platform()

        self.log('compile platform')
        self.target.compile_platform()

    def do_config_requirements(self):
        pass

    def ensure_build_layout(self):
        specdir = dirname(self.specfilename)
        self.mkdir(join(specdir, self.targetname))
        self.mkdir(join(specdir, self.targetname, 'platform'))
        self.mkdir(join(specdir, self.targetname, 'app'))
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

            fn = c.get('app', 'filename')
            with fn as fd:
                data = fd.read()
                regex = c.get('app', 'version.regex')
                match = search(regex, data)
                if not match:
                    raise Exception(
                        'Unable to found capture version in %r' % fn)
                return match[0]

        raise Exception('Missing version or version.regex + version.filename')

    @property
    def platform_dir(self):
        return join(dirname(self.specfilename), self.targetname, 'platform')

    @property
    def app_dir(self):
        return join(dirname(self.specfilename), self.targetname, 'app')

def run():
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-t', '--target', dest='target',
        help='target to build (android, ios, windows, linux, osx)')

    (options, args) = parser.parse_args()

    if options.target is None:
        raise Exception('Missing -t TARGET')
    Buildozer('buildozer.spec', options.target).run()
