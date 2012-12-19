'''

Layout directory for buildozer:

    build/
        <targetname>/
            platform/ - all the platform files necessary
            app/ - compiled application


'''

import shelve
import zipfile
from sys import stdout, exit
from urllib import urlretrieve
from re import search
from ConfigParser import SafeConfigParser
from os.path import join, exists, dirname, realpath, splitext
from subprocess import Popen, PIPE
from os import environ, mkdir, unlink, rename, walk, sep
from copy import copy
from shutil import copyfile


class Buildozer(object):

    def __init__(self, filename, target):
        super(Buildozer, self).__init__()
        self.environ = {}
        self.targetname = target
        self.specfilename = filename
        self.state = None
        self.config = SafeConfigParser()
        self.config.getlist = self._get_config_list
        self.config.getdefault = self._get_config_default
        self.config.read(filename)

        # resolve target
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

    def run(self):
        self.log('Build started')

        self.log('Check configuration tokens')
        self.do_config_requirements()

        self.log('Check requirements for %s' % self.targetname)
        self.target.check_requirements()

        self.log('Ensure build layout')
        self.ensure_build_layout()

        self.log('Install platform')
        self.target.install_platform()

        self.log('Compile platform')
        self.target.compile_platform()

        self.log('Prebuild the application')
        self.prebuild_application()

        self.log('Package the application')
        self.target.build_package()

    def do_config_requirements(self):
        pass

    def ensure_build_layout(self):
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

    def prebuild_application(self):
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

def run():
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-t', '--target', dest='target',
        help='target to build (android, ios, windows, linux, osx)')

    (options, args) = parser.parse_args()

    if options.target is None:
        raise Exception('Missing -t TARGET')
    Buildozer('buildozer.spec', options.target).run()
