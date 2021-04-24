'''
OSX target, based on kivy-sdk-packager
'''

import sys
if sys.platform != 'darwin':
    raise NotImplementedError('This will only work on osx')

from buildozer.target import Target
from os.path import exists, join, abspath, dirname
from subprocess import check_call, check_output


class TargetOSX(Target):
    targetname = "osx"

    def ensure_sdk(self):
        self.buildozer.info('Check if kivy-sdk-packager exists')
        if exists(
                join(self.buildozer.platform_dir, 'kivy-sdk-packager-master')):
            self.buildozer.info(
                    'kivy-sdk-packager found at '
                '{}'.format(self.buildozer.platform_dir))
            return

        self.buildozer.info('kivy-sdk-packager does not exist, clone it')
        platdir = self.buildozer.platform_dir
        check_call(
            ('curl', '-O', '-L',
            'https://github.com/kivy/kivy-sdk-packager/archive/master.zip'),
            cwd=platdir)
        check_call(('unzip', 'master.zip'), cwd=platdir)
        check_call(('rm', 'master.zip'), cwd=platdir)

    def download_kivy(self, cwd, py_branch=2):
        current_kivy_vers = self.buildozer.config.get('app', 'osx.kivy_version')

        if exists('/Applications/Kivy{}.app'.format(py_branch)):
            self.buildozer.info('Kivy found in Applications dir...')
            check_call(
                ('cp', '-a', '/Applications/Kivy{}.app'.format(py_branch),
                'Kivy.app'), cwd=cwd)

        else:
            if not exists(join(cwd, 'Kivy{}.dmg'.format(py_branch))):
                self.buildozer.info('Downloading kivy...')
                status_code = check_output(
                    ('curl', '-L', '--write-out', '%{http_code}', '-o', 'Kivy{}.dmg'.format(py_branch),
                    'https://kivy.org/downloads/{}/Kivy-{}-osx-python{}.dmg'
                    .format(current_kivy_vers, current_kivy_vers, py_branch)),
                    cwd=cwd)

                if status_code == "404":
                    self.buildozer.error(
                        "Unable to download the Kivy App. Check osx.kivy_version in your buildozer.spec, and verify "
                        "Kivy servers are accessible. https://kivy.org/downloads/")
                    check_call(("rm", "Kivy{}.dmg".format(py_branch)), cwd=cwd)
                    sys.exit(1)

            self.buildozer.info('Extracting and installing Kivy...')
            check_call(('hdiutil', 'attach', cwd + '/Kivy{}.dmg'.format(py_branch)))
            check_call(('cp', '-a', '/Volumes/Kivy/Kivy.app', './Kivy.app'), cwd=cwd)

    def ensure_kivyapp(self):
        self.buildozer.info('check if Kivy.app exists in local dir')
        kivy_app_dir = join(self.buildozer.platform_dir, 'kivy-sdk-packager-master', 'osx')

        py_branch = self.buildozer.config.get('app', 'osx.python_version')

        if not int(py_branch) in (2, 3):
            self.buildozer.error('incompatible python version... aborting')
            sys.exit(1)

        if exists(join(kivy_app_dir, 'Kivy.app')):
            self.buildozer.info('Kivy.app found at ' + kivy_app_dir)
        else:
            self.download_kivy(kivy_app_dir, py_branch)

    def check_requirements(self):
        self.ensure_sdk()
        self.ensure_kivyapp()

    def check_configuration_tokens(self, errors=None):
        if errors:
            self.buildozer.info('Check target configuration tokens')
            self.buildozer.error(
                '{0} error(s) found in the buildozer.spec'.format(
                len(errors)))
            for error in errors:
                print(error)
            sys.exit(1)
        # check

    def build_package(self):
        self.buildozer.info('Building package')

        bc = self.buildozer.config
        bcg = bc.get
        package_name = bcg('app', 'package.name')
        domain = bcg('app', 'package.domain')
        title = bcg('app', 'title')
        app_deps = open('requirements.txt').read()
        icon = bc.getdefault('app', 'icon.filename', '')
        version = self.buildozer.get_version()
        author = bc.getdefault('app', 'author', '')

        self.buildozer.info('Create {}.app'.format(package_name))
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
            'python', 'package_app.py', self.buildozer.app_dir,
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

        self.buildozer.info('{}.app created.'.format(package_name))
        self.buildozer.info('Creating {}.dmg'.format(package_name))
        check_output(
            ('sh', '-x', 'create-osx-dmg.sh', package_name + '.app'),
            cwd=cwd)
        self.buildozer.info('{}.dmg created'.format(package_name))
        self.buildozer.info('moving {}.dmg to bin.'.format(package_name))
        binpath = join(
            self.buildozer.user_build_dir or
            dirname(abspath(self.buildozer.specfilename)), 'bin')
        check_output(
            ('cp', '-a', package_name + '.dmg', binpath),
            cwd=cwd)
        self.buildozer.info('All Done!')

    def compile_platform(self):
        pass

    def install_platform(self):
        # ultimate configuration check.
        # some of our configuration cannot be check without platform.
        self.check_configuration_tokens()
        #
        self.buildozer.environ.update({
            'PACKAGES_PATH': self.buildozer.global_packages_dir,
        })

    def get_custom_commands(self):
        result = []
        for x in dir(self):
            if not x.startswith('cmd_'):
                continue
            if x[4:] in self.buildozer.standard_cmds:
                continue
            result.append((x[4:], getattr(self, x).__doc__))
        return result

    def get_available_packages(self):
        return ['kivy']

    def run_commands(self, args):
        if not args:
            self.buildozer.error('Missing target command')
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
                    self.buildozer.error('Argument passed without a command')
                    self.buildozer.usage()
                    sys.exit(1)
                last_command.append(arg)
        if last_command:
            result.append(last_command)

        config_check = False

        for item in result:
            command, args = item[0], item[1:]
            if not hasattr(self, 'cmd_{0}'.format(command)):
                self.buildozer.error('Unknown command {0}'.format(command))
                sys.exit(1)

            func = getattr(self, 'cmd_{0}'.format(command))

            need_config_check = not hasattr(func, '__no_config')
            if need_config_check and not config_check:
                config_check = True
                self.check_configuration_tokens()

            func(args)

    def check_build_prepared(self):
        self._build_prepared = False

    def cmd_clean(self, *args):
        self.buildozer.clean_platform()

    def cmd_update(self, *args):
        self.platform_update = True
        self.buildozer.prepare_for_build()

    def cmd_debug(self, *args):
        self.buildozer.prepare_for_build()
        self.build_mode = 'debug'
        self.check_build_prepared()
        self.buildozer.build()

    def cmd_release(self, *args):
        self.buildozer.prepare_for_build()
        self.build_mode = 'release'
        self.buildozer.build()

    def cmd_deploy(self, *args):
        self.buildozer.prepare_for_build()

    def cmd_run(self, *args):
        self.buildozer.prepare_for_build()

    def cmd_serve(self, *args):
        self.buildozer.cmd_serve()


def get_target(buildozer):
    return TargetOSX(buildozer)
