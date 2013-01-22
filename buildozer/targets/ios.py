'''
iOS target, based on kivy-ios project. (not working yet.)
'''

from buildozer.target import Target
from os.path import join, basename

class TargetIos(Target):

    def check_requirements(self):
        checkbin = self.buildozer.checkbin
        cmd = self.buildozer.cmd

        checkbin('Xcode xcodebuild', 'xcodebuild')
        checkbin('Xcode xcode-select', 'xcode-select')
        checkbin('Git git', 'git')

        self.buildozer.debug('Check availability of a iPhone SDK')
        sdk = cmd('xcodebuild -showsdks | fgrep "iphoneos" |'
                'tail -n 1 | awk \'{print $2}\'',
                get_stdout=True)[0]
        if not sdk:
            raise Exception(
                'No iPhone SDK found. Please install at least one iOS SDK.')
        else:
            self.buildozer.debug(' -> found %r' % sdk)

        self.buildozer.debug('Check Xcode path')
        xcode = cmd('xcode-select -print-path', get_stdout=True)[0]
        if not xcode:
            raise Exception('Unable to get xcode path')
        self.buildozer.debug(' -> found {0}'.format(xcode))

    def install_platform(self):
        cmd = self.buildozer.cmd
        self.ios_dir = ios_dir = join(self.buildozer.platform_dir, 'kivy-ios')
        if not self.buildozer.file_exists(ios_dir):
            cmd('git clone git://github.com/kivy/kivy-ios',
                    cwd=self.buildozer.platform_dir)
        elif self.platform_update:
            cmd('git clean -dxf', cwd=ios_dir)
            cmd('git pull origin master', cwd=ios_dir)

        self.fruitstrap_dir = fruitstrap_dir = join(self.buildozer.platform_dir,
                'fruitstrap')
        if not self.buildozer.file_exists(fruitstrap_dir):
            cmd('git clone git://github.com/mpurland/fruitstrap.git',
                    cwd=self.buildozer.platform_dir)

    def compile_platform(self):
        state = self.buildozer.state
        is_compiled = state.get('ios.platform.compiled', '')
        if not is_compiled:
            self.buildozer.cmd('tools/build-all.sh', cwd=self.ios_dir)
        state['ios.platform.compiled'] = '1'

        if not self.buildozer.file_exists(self.fruitstrap_dir, 'fruitstrap'):
            self.buildozer.cmd('make fruitstrap', cwd=self.fruitstrap_dir)

    def build_package(self):
        # create the project
        app_name = self.buildozer.namify(self.buildozer.config.get('app', 'title'))

        self.app_project_dir = join(self.ios_dir, 'app-{0}'.format(app_name.lower()))
        if not self.buildozer.file_exists(self.app_project_dir):
            self.buildozer.cmd('tools/create-xcode-project.sh {0} {1}'.format(
                app_name, self.buildozer.app_dir),
                cwd=self.ios_dir)
        else:
            self.buildozer.cmd('tools/populate-project.sh {0} {1}'.format(
                app_name, self.buildozer.app_dir),
                cwd=self.ios_dir)

        mode = 'Debug' if self.build_mode == 'debug' else 'Release'
        self.buildozer.cmd('xcodebuild -configuration {}'.format(mode),
                cwd=self.app_project_dir)
        ios_app_dir = 'app-{app_lower}/build/{mode}-iphoneos/{app_lower}.app'.format(
                app_lower=app_name.lower(), mode=mode)
        self.buildozer.state['ios:latestappdir'] = ios_app_dir

        key = 'ios.codesign.{}'.format(self.build_mode)
        ioscodesign = self.buildozer.config.getdefault('app', key, '')
        if not ioscodesign:
            self.buildozer.error('Cannot create the IPA package without'
                ' signature. You must fill the "{}" token.'.format(key))
        elif ioscodesign[0] not in ('"', "'"):
            ioscodesign = '"{}"'.format(ioscodesign)

        version = self.buildozer.get_version()
        ipa = join(self.buildozer.bin_dir, '{}-{}.ipa'.format(
            app_name, version))
        self.buildozer.cmd((
            '/usr/bin/xcrun '
            '-sdk iphoneos PackageApplication {ios_app_dir} '
            '-o {ipa} --sign {ioscodesign} --embed '
            '{ios_app_dir}/embedded.mobileprovision').format(
                ioscodesign=ioscodesign, ios_app_dir=ios_app_dir,
                mode=mode, ipa=ipa),
                cwd=self.ios_dir)

        self.buildozer.info('iOS packaging done!')
        self.buildozer.info('IPA {0} available in the bin directory'.format(
            basename(ipa)))
        self.buildozer.state['ios:latestipa'] = ipa
        self.buildozer.state['ios:latestmode'] = self.build_mode

    def cmd_deploy(self, *args):
        super(TargetIos, self).cmd_deploy(*args)
        self._run_fruitstrap(gdb=False)

    def cmd_run(self, *args):
        super(TargetIos, self).cmd_run(*args)
        self._run_fruitstrap(gdb=True)
        
    def _run_fruitstrap(self, gdb=False):
        state = self.buildozer.state
        if 'ios:latestappdir' not in state:
            self.buildozer.error(
                'App not built yet. Run "debug" or "release" first.')
        ios_app_dir = state.get('ios:latestappdir')

        if gdb:
            gdb_mode = '-d'
            self.buildozer.info('Deploy and start the application')
        else:
            gdb_mode = ''
            self.buildozer.info('Deploy the application')

        self.buildozer.cmd('{fruitstrap} {gdb} -b {app_dir}'.format(
            fruitstrap=join(self.fruitstrap_dir, 'fruitstrap'),
            gdb=gdb_mode, app_dir=ios_app_dir),
            cwd=self.ios_dir, show_output=True)

    def check_configuration_tokens(self):
        errors = []
        if not self.buildozer.config.getdefault('app', 'ios.codesign.debug'):
            errors.append('[app] "ios.codesign.debug" key missing, you must give a certificate name to use.')
        super(TargetIos, self).check_configuration_tokens(errors)


def get_target(buildozer):
    return TargetIos(buildozer)
