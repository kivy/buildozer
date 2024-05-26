"""
OSX target, based on kivy-sdk-packager
"""

import sys
if sys.platform != 'darwin':
    raise NotImplementedError('This will only work on osx')

from os.path import exists, join, abspath, dirname
from subprocess import check_call, check_output
import urllib.error

import buildozer.buildops as buildops
from buildozer.target import Target


class TargetOSX(Target):

    targetname = "osx"

    def ensure_sdk(self):
        self.logger.info('Check if kivy-sdk-packager exists')
        if exists(
                join(self.buildozer.platform_dir, 'kivy-sdk-packager-master')):
            self.logger.info(
                    'kivy-sdk-packager found at '
                    '{}'.format(self.buildozer.platform_dir))
            return

        self.logger.info('kivy-sdk-packager does not exist, clone it')
        platdir = self.buildozer.platform_dir
        buildops.download(
            'https://github.com/kivy/kivy-sdk-packager/archive/',
            'master.zip',
            cwd=platdir)
        buildops.file_extract(
            'master.zip', cwd=platdir, env=self.buildozer.environ)
        buildops.file_remove(join(platdir, 'master.zip'))

    def download_kivy(self, cwd):
        current_kivy_vers = self.buildozer.config.get('app', 'osx.kivy_version')

        if exists('/Applications/Kivy.app'):
            self.logger.info('Kivy found in Applications dir...')
            buildops.file_copy('/Applications/Kivy.app', 'Kivy.app', cwd=cwd)
        else:
            if not exists(join(cwd, 'Kivy.dmg')):
                self.logger.info('Downloading kivy...')
                try:
                    buildops.download(
                        f'https://kivy.org/downloads/{current_kivy_vers}/',
                        'Kivy.dmg',
                        cwd=cwd
                    )
                except urllib.error.URLError:
                    self.logger.error(
                        "Unable to download the Kivy App. "
                        "Check osx.kivy_version in your buildozer.spec, and "
                        "verify Kivy servers are accessible. "
                        "https://kivy.org/downloads/")
                    buildops.file_remove(join(cwd, "Kivy.dmg"))
                    sys.exit(1)

            self.logger.info('Extracting and installing Kivy...')
            check_call(('hdiutil', 'attach', cwd + '/Kivy.dmg'))
            buildops.file_copytree(
                '/Volumes/Kivy/Kivy.app', cwd + '/Kivy.app'
            )

    def ensure_kivyapp(self):
        self.logger.info('check if Kivy.app exists in local dir')
        kivy_app_dir = join(self.buildozer.platform_dir, 'kivy-sdk-packager-master', 'osx')

        if exists(join(kivy_app_dir, 'Kivy.app')):
            self.logger.info('Kivy.app found at ' + kivy_app_dir)
        else:
            self.download_kivy(kivy_app_dir)

    def check_requirements(self):
        self.ensure_sdk()
        self.ensure_kivyapp()

    def build_package(self):
        self.logger.info('Building package')

        bc = self.buildozer.config
        bcg = bc.get
        package_name = bcg('app', 'package.name')
        domain = bcg('app', 'package.domain')
        title = bcg('app', 'title')
        app_deps = open('requirements.txt').read()
        icon = bc.getdefault('app', 'icon.filename', '')
        version = self.buildozer.get_version()
        author = bc.getdefault('app', 'author', '')

        self.logger.info('Create {}.app'.format(package_name))
        cwd = join(self.buildozer.platform_dir, 'kivy-sdk-packager-master', 'osx')
        # remove kivy from app_deps
        app_deps = [a for a in app_deps.split('\n') if not a.startswith('#') and a not in ['kivy', '']]

        cmd = [
            'Kivy.app/Contents/Resources/script',
            '-m', 'pip', 'install',
             ]
        cmd.extend(app_deps)
        check_output(cmd, cwd=cwd)

        cmd = [
            sys.executable,
            'package_app.py',
            self.buildozer.app_dir,
            '--appname={}'.format(package_name),
            '--bundlename={}'.format(title),
            '--bundleid={}'.format(domain),
            '--bundleversion={}'.format(version),
            '--displayname={}'.format(title)
              ]
        if icon:
            cmd.append('--icon={}'.format(icon))
        if author:
            cmd.append('--author={}'.format(author))

        check_output(cmd, cwd=cwd)

        self.logger.info('{}.app created.'.format(package_name))
        self.logger.info('Creating {}.dmg'.format(package_name))
        check_output(
            ('sh', '-x', 'create-osx-dmg.sh', package_name + '.app', package_name, '-s', '1'),
            cwd=cwd)
        self.logger.info('{}.dmg created'.format(package_name))
        self.logger.info('moving {}.dmg to bin.'.format(package_name))

        package_name = package_name + '.dmg'
        binpath = join(
            self.buildozer.user_build_dir or
            dirname(abspath(self.buildozer.specfilename)), 'bin') + '/' + package_name
        buildops.file_copy(
            join(cwd, package_name),
            binpath)
        self.logger.info('All Done!')

    def install_platform(self):
        # ultimate configuration check.
        # some of our configuration cannot be checked without platform.
        self.check_configuration_tokens()
        #
        self.buildozer.environ.update({
            'PACKAGES_PATH': self.buildozer.global_packages_dir,
        })

    def get_available_packages(self):
        return ['kivy', 'python3']

    def run_commands(self, args):
        if not args:
            self.logger.error('Missing target command')
            self.buildozer.usage()
            sys.exit(1)

        result = []
        last_command = []
        for arg in args:
            if not arg.startswith('--'):
                if last_command:
                    result.append(last_command)
                    last_command = []
                last_command.append(arg)
            else:
                if not last_command:
                    self.logger.error('Argument passed without a command')
                    self.buildozer.usage()
                    sys.exit(1)
                last_command.append(arg)
        if last_command:
            result.append(last_command)

        config_check = False

        for item in result:
            command, args = item[0], item[1:]
            if not hasattr(self, 'cmd_{0}'.format(command)):
                self.logger.error('Unknown command {0}'.format(command))
                sys.exit(1)

            func = getattr(self, 'cmd_{0}'.format(command))

            need_config_check = not hasattr(func, '__no_config')
            if need_config_check and not config_check:
                config_check = True
                self.check_configuration_tokens()

            func(args)


def get_target(buildozer):
    return TargetOSX(buildozer)
