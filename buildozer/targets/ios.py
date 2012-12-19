from buildozer.target import Target

class TargetIos(Target):

    def check_requirements(self):
        checkbin = self.buildozer.checkbin
        cmd = self.buildozer.cmd

        checkbin('Xcode xcodebuild', 'xcodebuild')
        checkbin('Xcode xcode-select', 'xcode-select')
        checkbin('Git git', 'git')

        print 'Check availability of a iPhone SDK'
        sdk = cmd('xcodebuild -showsdks | fgrep "iphoneos" | tail -n 1 | awk \'{print $2}\'')[0]
        if not sdk:
            raise Exception(
                'No iPhone SDK found. Please install at least one iOS SDK.')
        else:
            print ' -> found %r' % sdk

        print 'Check Xcode path'
        xcode = cmd('xcode-select -print-path')[0]
        if not xcode:
            raise Exception('Unable to get xcode path')
        print ' -> found %r' % xcode

    def install_platform(self):
        cmd = self.buildozer.cmd
        cmd('git clone git://github.com/kivy/kivy-ios',
                cwd=self.buildozer.platform_dir)




def get_target(buildozer):
    return TargetIos(buildozer)
