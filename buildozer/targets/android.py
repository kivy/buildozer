'''
Android target, based on python-for-android project
'''
#
# Android target
# Thanks for Renpy (again) for its install_sdk.py and plat.py in the PGS4A
# project!
# 


ANDROID_API = '14'
ANDROID_SDK_VERSION = '21'
ANDROID_NDK_VERSION = '8c'
APACHE_ANT_VERSION = '1.8.4'


import traceback
from pipes import quote
from sys import platform, executable
from buildozer.target import Target
from os.path import join, realpath
from shutil import copyfile


class TargetAndroid(Target):

    def check_requirements(self):
        if platform in ('win32', 'cygwin'):
            try:
                self._set_win32_java_home()
            except:
                traceback.print_exc()
            self.android_cmd = join('android-sdk', 'tools', 'android.bat')
            self.ant_cmd = join('apache-ant', 'bin', 'ant.bat')
            self.adb_cmd = join('android-sdk', 'platform-tools', 'adb.exe')
            self.javac_cmd = self._locate_java('javac.exe')
            self.keytool_cmd = self._locate_java('keytool.exe')
        elif platform in ('darwin', ):
            self.android_cmd = join('android-sdk', 'tools', 'android')
            self.ant_cmd = join('apache-ant', 'bin', 'ant')
            self.adb_cmd = join('android-sdk', 'platform-tools', 'adb')
            self.javac_cmd = self._locate_java('javac')
            self.keytool_cmd = self._locate_java('keytool')
        else:
            self.android_cmd = join('android-sdk', 'tools', 'android')
            self.ant_cmd = join('apache-ant', 'bin', 'ant')
            self.adb_cmd = join('android-sdk', 'platform-tools', 'adb')
            self.javac_cmd = self._locate_java('javac')
            self.keytool_cmd = self._locate_java('keytool')

        checkbin = self.buildozer.checkbin
        checkbin('Git git', 'git')
        checkbin('Cython cython', 'cython')
        checkbin('Java compiler', self.javac_cmd)
        checkbin('Java keytool', self.keytool_cmd)

    def _set_win32_java_home(self):
        if 'JAVA_HOME' in self.buildozer.environ:
            return
        import _winreg
        with _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\Java Development Kit") as jdk: #@UndefinedVariable
            current_version, _type = _winreg.QueryValueEx(jdk, "CurrentVersion") #@UndefinedVariable
            with _winreg.OpenKey(jdk, current_version) as cv: #@UndefinedVariable
                java_home, _type = _winreg.QueryValueEx(cv, "JavaHome") #@UndefinedVariable
            self.buildozer.environ['JAVA_HOME'] = java_home

    def _locate_java(self, s):
        '''If JAVA_HOME is in the environ, return $JAVA_HOME/bin/s. Otherwise,
        return s.
        '''
        if 'JAVA_HOME' in self.buildozer.environ:
            return join(self.buildozer.environ['JAVA_HOME'], 'bin', s)
        else:
            return s

    def _install_apache_ant(self):
        ant_dir = join(self.buildozer.platform_dir, 'apache-ant')
        if self.buildozer.file_exists(ant_dir):
            self.buildozer.log('Apache ANT found at {0}'.format(ant_dir))
            return ant_dir

        self.buildozer.log('Android ANT is missing, downloading')
        archive = 'apache-ant-{0}-bin.tar.gz'.format(APACHE_ANT_VERSION)
        unpacked = 'apache-ant-{0}'.format(APACHE_ANT_VERSION)
        url = 'http://archive.apache.org/dist/ant/binaries/'
        self.buildozer.download(url, archive,
                cwd=self.buildozer.platform_dir)

        self.buildozer.file_extract(archive, cwd=self.buildozer.platform_dir)
        self.buildozer.file_rename(unpacked, 'apache-ant',
                cwd=self.buildozer.platform_dir)
        self.buildozer.log('Apache ANT installation done.')
        return ant_dir

    def _install_android_sdk(self):
        sdk_dir = join(self.buildozer.platform_dir, 'android-sdk')
        if self.buildozer.file_exists(sdk_dir):
            self.buildozer.log('Android SDK found at {0}'.format(sdk_dir))
            return sdk_dir

        self.buildozer.log('Android SDK is missing, downloading')
        if platform in ('win32', 'cygwin'):
            archive = 'android-sdk_r{0}-windows.zip'
            unpacked = 'android-sdk-windows'
        elif platform in ('darwin', ):
            archive = 'android-sdk_r{0}-macosx.zip'
            unpacked = 'android-sdk-macosx'
        elif platform in ('linux2', 'linux3'):
            archive = 'android-sdk_r{0}-linux.tgz'
            unpacked = 'android-sdk-linux'
        else:
            raise SystemError('Unsupported platform: {0}'.format(platform))

        archive = archive.format(ANDROID_SDK_VERSION)
        url = 'http://dl.google.com/android/'
        self.buildozer.download(url, archive,
                cwd=self.buildozer.platform_dir)

        self.buildozer.log('Unpacking Android SDK')
        self.buildozer.file_extract(archive, cwd=self.buildozer.platform_dir)
        self.buildozer.file_rename(unpacked, 'android-sdk',
                cwd=self.buildozer.platform_dir)
        self.buildozer.log('Android SDK installation done.')
        return sdk_dir

    def _install_android_ndk(self):
        ndk_dir = join(self.buildozer.platform_dir, 'android-ndk')
        if self.buildozer.file_exists(ndk_dir):
            self.buildozer.log('Android NDK found at {0}'.format(ndk_dir))
            return ndk_dir

        self.buildozer.log('Android NDK is missing, downloading')
        if platform in ('win32', 'cygwin'):
            archive = 'android-ndk-r{0}-windows.zip'
        elif platform in ('darwin', ):
            archive = 'android-ndk-r{0}-darwin.tar.bz2'
        elif platform in ('linux2', 'linux3'):
            archive = 'android-ndk-r{0}-linux-x86.tar.bz2'
        else:
            raise SystemError('Unsupported platform: {0}'.format(platform))

        unpacked = 'android-ndk-r{0}'
        archive = archive.format(ANDROID_NDK_VERSION)
        unpacked = unpacked.format(ANDROID_NDK_VERSION)
        url = 'http://dl.google.com/android/ndk/'
        self.buildozer.download(url, archive,
                cwd=self.buildozer.platform_dir)

        self.buildozer.log('Unpacking Android NDK')
        self.buildozer.file_extract(archive, cwd=self.buildozer.platform_dir)
        self.buildozer.file_rename(unpacked, 'android-ndk',
                cwd=self.buildozer.platform_dir)
        self.buildozer.log('Android NDK installation done.')
        return ndk_dir

    def _install_android_packages(self):
        packages = []
        android_platform = join(self.sdk_dir, 'platforms',
                'android-{0}'.format(ANDROID_API))
        if not self.buildozer.file_exists(android_platform):
            packages.append('android-{0}'.format(ANDROID_API))
        if not self.buildozer.file_exists(self.sdk_dir, 'platform-tools'):
            packages.append('platform-tools')
        if not packages:
            self.buildozer.log('Android packages already installed.')
            return
        self.buildozer.cmd('{0} update sdk -u -a -t {1}'.format(
            self.android_cmd, ','.join(packages)),
            cwd=self.buildozer.platform_dir)
        self.buildozer.log('Android packages installation done.')

    def install_platform(self):
        cmd = self.buildozer.cmd
        self.pa_dir = pa_dir = join(self.buildozer.platform_dir, 'python-for-android')
        if not self.buildozer.file_exists(pa_dir):
            cmd('git clone git://github.com/kivy/python-for-android',
                    cwd=self.buildozer.platform_dir)
        elif self.platform_update:
            cmd('git clean -dxf', cwd=pa_dir)
            cmd('git pull origin master', cwd=pa_dir)

        self._install_apache_ant()
        self.sdk_dir = sdk_dir = self._install_android_sdk()
        self.ndk_dir = ndk_dir = self._install_android_ndk()
        self._install_android_packages()
        self.buildozer.environ.update({
            'ANDROIDSDK': realpath(sdk_dir),
            'ANDROIDNDK': realpath(ndk_dir),
            'ANDROIDAPI': ANDROID_API,
            'ANDROIDNDKVER': ANDROID_NDK_VERSION})

    def compile_platform(self):
        # for android, the compilation depends really on the app requirements.
        # compile the distribution only if the requirements changed.
        last_requirements = self.buildozer.state.get('android.requirements', '')
        app_requirements = self.buildozer.config.getlist('app',
                'requirements', '')

        # we need to extract the requirements that python-for-android knows
        # about
        available_modules = self.buildozer.cmd(
                './distribute.sh -l', cwd=self.pa_dir)[0]
        if not available_modules.startswith('Available modules:'):
            self.buildozer.error('Python-for-android invalid output for -l')
        available_modules = available_modules[19:].splitlines()[0].split()

        android_requirements = [x for x in app_requirements if x in
                available_modules]
        missing_requirements = [x for x in app_requirements if x not in
                available_modules]

        if missing_requirements:
            self.buildozer.error(
                'Cannot package the app cause of the missing'
                ' requirements in python-for-android: {0}'.format(
                    missing_requirements))

        need_compile = 0
        if last_requirements != android_requirements:
            need_compile = 1
        if not self.buildozer.file_exists(self.pa_dir, 'dist', 'default'):
            need_compile = 1

        if not need_compile:
            self.buildozer.log('Distribution already compiled, pass.')
            return

        modules_str = ' '.join(android_requirements)
        cmd = self.buildozer.cmd
        cmd('git clean -dxf', cwd=self.pa_dir)
        cmd('./distribute.sh -m "{0}"'.format(modules_str), cwd=self.pa_dir)
        self.buildozer.log('Distribution compiled.')

        # ensure we will not compile again
        self.buildozer.state['android.requirements'] = android_requirements
        self.buildozer.state.sync()

    def _get_package(self):
        config = self.buildozer.config
        package_domain = config.getdefault('app', 'package.domain', '')
        package = config.get('app', 'package.name')
        if package_domain:
            package = package_domain + '.' + package
        return package

    def build_package(self):
        dist_dir = join(self.pa_dir, 'dist', 'default')
        config = self.buildozer.config
        package = self._get_package()
        version = self.buildozer.get_version()

        build_cmd = (
            '{python} build.py --name {name}'
            ' --version {version}'
            ' --package {package}'
            ' --private {appdir}'
            ' --sdk {androidsdk}'
            ' --minsdk {androidminsdk}').format(
            python=executable,
            name=quote(config.get('app', 'title')),
            version=version,
            package=package,
            appdir=self.buildozer.app_dir,
            androidminsdk=config.getdefault(
                'app', 'android.minsdk', 8),
            androidsdk=config.getdefault(
                'app', 'android.sdk', ANDROID_API))

        # add permissions
        permissions = config.getlist('app',
                'android.permissions', [])
        for permission in permissions:
            build_cmd += ' --permission {0}'.format(permission)

        # build only in debug right now.
        if self.build_mode == 'debug':
            build_cmd += ' debug'
            mode = 'debug'
        else:
            build_cmd += ' release'
            mode = 'release-unsigned'
        self.buildozer.cmd(build_cmd, cwd=dist_dir)

        # XXX found how the apk name is really built from the title
        bl = '\'" ,'
        apktitle = ''.join([x for x in config.get('app', 'title') if x not in
            bl])
        apk = '{title}-{version}-{mode}.apk'.format(
            title=apktitle, version=version, mode=mode)

        # copy to our place
        copyfile(join(dist_dir, 'bin', apk),
                join(self.buildozer.bin_dir, apk))

        self.buildozer.log('Android packaging done!')
        self.buildozer.log('APK {0} available in the bin directory'.format(apk))
        self.buildozer.state['android:latestapk'] = apk
        self.buildozer.state['android:latestmode'] = self.build_mode

    def cmd_deploy(self, *args):
        super(TargetAndroid, self).cmd_deploy(*args)
        state = self.buildozer.state
        if 'android:latestapk' not in state:
            self.buildozer.error(
                'No APK built yet. Run "debug" first.')

        if state.get('android:latestmode', '') != 'debug':
            self.buildozer.error(
                'Only debug APK are supported for deploy')

        # search the APK in the bin dir
        apk = state['android:latestapk']
        full_apk = join(self.buildozer.bin_dir, apk)
        if not self.buildozer.file_exists(full_apk):
            self.buildozer.error(
                'Unable to found the latest APK. Please run "debug" again.')

        # push on the device
        self.buildozer.cmd('{0} install -r {1}'.format(
            self.adb_cmd, full_apk), cwd=self.buildozer.platform_dir)

        self.buildozer.log('Application pushed on the device.')

    def cmd_run(self, *args):
        super(TargetAndroid, self).cmd_run(*args)

        entrypoint = self.buildozer.config.getdefault(
            'app', 'android.entrypoint', 'org.renpy.android.PythonActivity')
        package = self._get_package()

        self.buildozer.cmd(
            '{adb} shell am start -n {package}/{entry} -a {entry}'.format(
            adb=self.adb_cmd, package=package, entry=entrypoint),
            cwd=self.buildozer.platform_dir)

        self.buildozer.log('Application started on the device.')





def get_target(buildozer):
    return TargetAndroid(buildozer)
