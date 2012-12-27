'''
iOS target, based on kivy-ios project. (not working yet.)
'''

from buildozer.target import Target
from os.path import join

class TargetIos(Target):

    def check_requirements(self):
        checkbin = self.buildozer.checkbin
        cmd = self.buildozer.cmd

        checkbin('Xcode xcodebuild', 'xcodebuild')
        checkbin('Xcode xcode-select', 'xcode-select')
        checkbin('Git git', 'git')

        self.buildozer.debug('Check availability of a iPhone SDK')
        sdk = cmd('xcodebuild -showsdks | fgrep "iphoneos" | tail -n 1 | awk \'{print $2}\'')[0]
        if not sdk:
            raise Exception(
                'No iPhone SDK found. Please install at least one iOS SDK.')
        else:
            print ' -> found %r' % sdk

        self.buildozer.debug('Check Xcode path')
        xcode = cmd('xcode-select -print-path')[0]
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

    def compile_platform(self):
        self.buildozer.cmd('tools/build-all.sh', cwd=self.ios_dir)

    def build_package(self):
        # create the project
        app_name = self.buildozer.namify(self.config.get('app', 'title'))

        self.app_project_dir = join(self.ios_dir, 'app-{0}'.format(app_name))
        self.buildozer.cmd('tools/create-xcode-project.sh {0} {1}'.format(
            app_name, self.buildozer.app_dir),
            cwd=self.ios_dir)


def get_target(buildozer):
    return TargetIos(buildozer)
