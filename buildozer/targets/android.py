'''
Android target, based on python-for-android project
'''
#
# Android target
# Thanks for Renpy (again) for its install_sdk.py and plat.py in the PGS4A
# project!
# 


ANDROID_API = '14'
ANDROID_MINAPI = '8'
ANDROID_SDK_VERSION = '21'
ANDROID_NDK_VERSION = '8e'
APACHE_ANT_VERSION = '1.8.4'


import traceback
import os
from pipes import quote
from sys import platform, executable
from buildozer.target import Target
from os import environ
from os.path import join, realpath, expanduser
from shutil import copyfile
from glob import glob


class TargetAndroid(Target):

    @property
    def android_sdk_version(self):
        return self.buildozer.config.getdefault(
                'app', 'android.sdk', ANDROID_SDK_VERSION)

    @property
    def android_ndk_version(self):
        return self.buildozer.config.getdefault(
                'app', 'android.ndk', ANDROID_NDK_VERSION)

    @property
    def android_api(self):
        return self.buildozer.config.getdefault(
                'app', 'android.api', ANDROID_API)

    @property
    def android_minapi(self):
        return self.buildozer.config.getdefault(
                'app', 'android.minapi', ANDROID_MINAPI)

    @property
    def android_sdk_dir(self):
        directory = expanduser(self.buildozer.config.getdefault(
            'app', 'android.sdk_path', ''))
        if directory:
            return realpath(directory)
        version = self.buildozer.config.getdefault(
                'app', 'android.sdk', self.android_sdk_version)
        return join(self.buildozer.global_platform_dir,
                'android-sdk-{0}'.format(version))

    @property
    def android_ndk_dir(self):
        directory = expanduser(self.buildozer.config.getdefault(
            'app', 'android.ndk_path', ''))
        if directory:
            return realpath(directory)
        version = self.buildozer.config.getdefault(
                'app', 'android.ndk', self.android_ndk_version)
        return join(self.buildozer.global_platform_dir,
                'android-ndk-{0}'.format(version))

    @property
    def apache_ant_dir(self):
        directory = expanduser(self.buildozer.config.getdefault(
            'app', 'android.ant_path', ''))
        if directory:
            return realpath(directory)
        version = self.buildozer.config.getdefault(
                'app', 'android.ant', APACHE_ANT_VERSION)
        return join(self.buildozer.global_platform_dir,
                'apache-ant-{0}'.format(version))

    def check_requirements(self):
        if platform in ('win32', 'cygwin'):
            try:
                self._set_win32_java_home()
            except:
                traceback.print_exc()
            self.android_cmd = join(self.android_sdk_dir, 'tools', 'android.bat')
            self.adb_cmd = join(self.android_sdk_dir, 'platform-tools', 'adb.exe')
            self.javac_cmd = self._locate_java('javac.exe')
            self.keytool_cmd = self._locate_java('keytool.exe')
        elif platform in ('darwin', ):
            self.android_cmd = join(self.android_sdk_dir, 'tools', 'android')
            self.adb_cmd = join(self.android_sdk_dir, 'platform-tools', 'adb')
            self.javac_cmd = self._locate_java('javac')
            self.keytool_cmd = self._locate_java('keytool')
        else:
            self.android_cmd = join(self.android_sdk_dir, 'tools', 'android')
            self.adb_cmd = join(self.android_sdk_dir, 'platform-tools', 'adb')
            self.javac_cmd = self._locate_java('javac')
            self.keytool_cmd = self._locate_java('keytool')

        # Need to add internally installed ant to path for external tools
        # like adb to use
        path = [join(self.apache_ant_dir, 'bin')]
        if 'PATH' in self.buildozer.environ:
            path.append(self.buildozer.environ['PATH'])
        else:
            path.append(os.environ['PATH'])
        self.buildozer.environ['PATH'] = ':'.join(path)
        checkbin = self.buildozer.checkbin
        checkbin('Git git', 'git')
        checkbin('Cython cython', 'cython')
        checkbin('Java compiler', self.javac_cmd)
        checkbin('Java keytool', self.keytool_cmd)

    def check_configuration_tokens(self):
        errors = []

        # check the permission
        available_permissions = self._get_available_permissions()
        if available_permissions:
            permissions = self.buildozer.config.getlist(
                'app', 'android.permissions', [])
            for permission in permissions:
                if permission not in available_permissions:
                    errors.append(
                        '[app] "android.permission" contain an unknown'
                        ' permission {0}'.format(permission))

        super(TargetAndroid, self).check_configuration_tokens(errors)

    def _get_available_permissions(self):
        key = 'android:available_permissions'
        key_sdk = 'android:available_permissions_sdk'

        refresh_permissions = False
        sdk = self.buildozer.state.get(key_sdk, None)
        if not sdk or sdk != self.android_sdk_version:
            refresh_permissions = True
        if key not in self.buildozer.state:
            refresh_permissions = True
        if not refresh_permissions:
            return self.buildozer.state[key]

        try:
            self.buildozer.debug('Read available permissions from api-versions.xml')
            import xml.etree.ElementTree as ET
            fn = join(self.android_sdk_dir, 'platform-tools',
                    'api', 'api-versions.xml')
            with open(fn) as fd:
                doc = ET.fromstring(fd.read())
            fields = doc.findall('.//class[@name="android/Manifest$permission"]/field[@name]')
            available_permissions = [x.attrib['name'] for x in fields]

            self.buildozer.state[key] = available_permissions
            self.buildozer.state[key_sdk] = self.android_sdk_version
            return available_permissions
        except:
            return None

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
        ant_dir = self.apache_ant_dir
        if self.buildozer.file_exists(ant_dir):
            self.buildozer.info('Apache ANT found at {0}'.format(ant_dir))
            return ant_dir

        self.buildozer.info('Android ANT is missing, downloading')
        archive = 'apache-ant-{0}-bin.tar.gz'.format(APACHE_ANT_VERSION)
        url = 'http://archive.apache.org/dist/ant/binaries/'
        self.buildozer.download(url, archive,
                cwd=self.buildozer.global_platform_dir)
        self.buildozer.file_extract(archive,
                cwd=self.buildozer.global_platform_dir)
        self.buildozer.info('Apache ANT installation done.')
        return ant_dir

    def _install_android_sdk(self):
        sdk_dir = self.android_sdk_dir
        if self.buildozer.file_exists(sdk_dir):
            self.buildozer.info('Android SDK found at {0}'.format(sdk_dir))
            return sdk_dir

        self.buildozer.info('Android SDK is missing, downloading')
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

        archive = archive.format(self.android_sdk_version)
        url = 'http://dl.google.com/android/'
        self.buildozer.download(url, archive,
                cwd=self.buildozer.global_platform_dir)

        self.buildozer.info('Unpacking Android SDK')
        self.buildozer.file_extract(archive,
                cwd=self.buildozer.global_platform_dir)
        self.buildozer.file_rename(unpacked, sdk_dir,
                cwd=self.buildozer.global_platform_dir)
        self.buildozer.info('Android SDK installation done.')
        return sdk_dir

    def _install_android_ndk(self):
        ndk_dir = self.android_ndk_dir
        if self.buildozer.file_exists(ndk_dir):
            self.buildozer.info('Android NDK found at {0}'.format(ndk_dir))
            return ndk_dir

        self.buildozer.info('Android NDK is missing, downloading')
        if platform in ('win32', 'cygwin'):
            architecture = None
            archive = 'android-ndk-r{0}-windows.zip'
        elif platform in ('darwin', ):
            architecture = os.uname()[4]
            archive = 'android-ndk-r{0}-darwin-{1}.tar.bz2'
        elif platform in ('linux2', 'linux3'):
            architecture = os.uname()[4]
            archive = 'android-ndk-r{0}-linux-{1}.tar.bz2'
        else:
            raise SystemError('Unsupported platform: {0}'.format(platform))

        unpacked = 'android-ndk-r{0}'
        archive = archive.format(self.android_ndk_version, architecture)
        unpacked = unpacked.format(self.android_ndk_version)
        url = 'http://dl.google.com/android/ndk/'
        self.buildozer.download(url, archive,
                cwd=self.buildozer.global_platform_dir)

        self.buildozer.info('Unpacking Android NDK')
        self.buildozer.file_extract(archive,
                cwd=self.buildozer.global_platform_dir)
        self.buildozer.file_rename(unpacked, ndk_dir,
                cwd=self.buildozer.global_platform_dir)
        self.buildozer.info('Android NDK installation done.')
        return ndk_dir

    def _install_android_packages(self):
        packages = []
        android_platform = join(self.android_sdk_dir, 'platforms',
                'android-{0}'.format(self.android_api))
        if not self.buildozer.file_exists(android_platform):
            packages.append('android-{0}'.format(self.android_api))
        if not self.buildozer.file_exists(self.android_sdk_dir, 'platform-tools'):
            packages.append('platform-tools')
        if not packages:
            self.buildozer.info('Android packages already installed.')
            return
        self.buildozer.cmd('chmod +x {}/tools/*'.format(self.android_sdk_dir))
        self.buildozer.cmd('{0} update sdk -u -a -t {1}'.format(
            self.android_cmd, ','.join(packages)),
            cwd=self.buildozer.global_platform_dir)
        self.buildozer.info('Android packages installation done.')

    def install_platform(self):
        cmd = self.buildozer.cmd
        self.pa_dir = pa_dir = join(self.buildozer.platform_dir, 'python-for-android')
        if not self.buildozer.file_exists(pa_dir):
            cmd('git clone git://github.com/kivy/python-for-android',
                    cwd=self.buildozer.platform_dir)
        elif self.platform_update:
            cmd('git clean -dxf', cwd=pa_dir)
            cmd('git pull origin master', cwd=pa_dir)

            source = self.buildozer.config.getdefault('app', 'android.branch')
            if source:
                cmd('git checkout --track -b %s origin/%s' % (source, source),
                    cwd=pa_dir)

        self._install_apache_ant()
        self._install_android_sdk()
        self._install_android_ndk()
        self._install_android_packages()

        # ultimate configuration check.
        # some of our configuration cannot be check without platform.
        self.check_configuration_tokens()

        self.buildozer.environ.update({
            'ANDROIDSDK': self.android_sdk_dir,
            'ANDROIDNDK': self.android_ndk_dir,
            'ANDROIDAPI': ANDROID_API,
            'ANDROIDNDKVER': self.android_ndk_version})

    def get_available_packages(self):
        available_modules = self.buildozer.cmd(
                './distribute.sh -l', cwd=self.pa_dir, get_stdout=True)[0]
        if not available_modules.startswith('Available modules:'):
            self.buildozer.error('Python-for-android invalid output for -l')
        return available_modules[19:].splitlines()[0].split()

    def compile_platform(self):
        # for android, the compilation depends really on the app requirements.
        # compile the distribution only if the requirements changed.
        last_requirements = self.buildozer.state.get('android.requirements', '')
        app_requirements = self.buildozer.config.getlist('app',
                'requirements', '')

        # we need to extract the requirements that python-for-android knows
        # about
        available_modules = self.get_available_packages()
        android_requirements = [x for x in app_requirements if x in
                available_modules]

        need_compile = 0
        if last_requirements != android_requirements:
            need_compile = 1
        if not self.buildozer.file_exists(self.pa_dir, 'dist', 'default'):
            need_compile = 1

        if not need_compile:
            self.buildozer.info('Distribution already compiled, pass.')
            return

        modules_str = ' '.join(android_requirements)
        cmd = self.buildozer.cmd
        cmd('git clean -dxf', cwd=self.pa_dir)
        cmd('./distribute.sh -m "{0}"'.format(modules_str), cwd=self.pa_dir)
        self.buildozer.info('Distribution compiled.')

        # ensure we will not compile again
        self.buildozer.state['android.requirements'] = android_requirements
        self.buildozer.state.sync()

    def _get_package(self):
        config = self.buildozer.config
        package_domain = config.getdefault('app', 'package.domain', '')
        package = config.get('app', 'package.name')
        if package_domain:
            package = package_domain + '.' + package
        return package.lower()

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

        # add extra Java jar files
        add_jars = config.getdefault('app', 'android.add_jars', '')
        if add_jars:
            for pattern in add_jars.split(';'):
                pattern = expanduser(pattern.strip())
                matches = glob(pattern)
                if matches:
                    for jar in matches:
                        build_cmd += ' --add-jar "{}"'.format(jar)
                else:
                    raise SystemError("Failed to find jar file: {}".format(pattern))

        # add presplash
        presplash = config.getdefault('app', 'presplash.filename', '')
        if presplash:
            build_cmd += ' --presplash {}'.format(join(self.buildozer.root_dir,
                presplash))

        # add icon
        icon = config.getdefault('app', 'icon.filename', '')
        if icon:
            build_cmd += ' --icon {}'.format(join(self.buildozer.root_dir, icon))

        # OUYA Console support
        ouya_category = config.getdefault('app', 'android.ouya.category', '').upper()
        if ouya_category:
            if ouya_category not in ('GAME', 'APP'):
                raise SystemError('Invalid android.ouya.category: "{}" must be one of GAME or APP'.format(ouya_category))
            # add icon
            build_cmd += ' --ouya-category {}'.format(ouya_category)
            ouya_icon = config.getdefault('app', 'android.ouya.icon.filename', '')
            build_cmd += ' --ouya-icon {}'.format(join(self.buildozer.root_dir, ouya_icon))

        # add orientation
        orientation = config.getdefault('app', 'orientation', 'landscape')
        if orientation == 'all':
            orientation = 'sensor'
        build_cmd += ' --orientation {}'.format(orientation)

        # fullscreen ?
        fullscreen = config.getbooldefault('app', 'fullscreen', True)
        if not fullscreen:
            build_cmd += ' --window'

        # intent filters
        intent_filters = config.getdefault('app',
            'android.manifest.intent_filters', '')
        if intent_filters:
            build_cmd += ' --intent-filters {}'.format(
                    join(self.buildozer.root_dir, intent_filters))

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

        self.buildozer.info('Android packaging done!')
        self.buildozer.info('APK {0} available in the bin directory'.format(apk))
        self.buildozer.state['android:latestapk'] = apk
        self.buildozer.state['android:latestmode'] = self.build_mode

    @property
    def serials(self):
        if hasattr(self, '_serials'):
            return self._serials
        serial = environ.get('ANDROID_SERIAL')
        if serial:
            return serial.split(',')
        l = self.buildozer.cmd('adb devices',
                get_stdout=True)[0].splitlines()[1:-1]
        serials = []
        for serial in l:
            serials.append(serial.split()[0])
        self._serials = serials
        return serials

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
        for serial in self.serials:
            self.buildozer.environ['ANDROID_SERIAL'] = serial
            self.buildozer.info('Deploy on {}'.format(serial))
            self.buildozer.cmd('{0} install -r {1}'.format(
                self.adb_cmd, full_apk), cwd=self.buildozer.global_platform_dir)
        self.buildozer.environ.pop('ANDROID_SERIAL', None)

        self.buildozer.info('Application pushed.')

    def cmd_run(self, *args):
        super(TargetAndroid, self).cmd_run(*args)

        entrypoint = self.buildozer.config.getdefault(
            'app', 'android.entrypoint', 'org.renpy.android.PythonActivity')
        package = self._get_package()

        # push on the device
        for serial in self.serials:
            self.buildozer.environ['ANDROID_SERIAL'] = serial
            self.buildozer.info('Run on {}'.format(serial))
            self.buildozer.cmd(
                '{adb} shell am start -n {package}/{entry} -a {entry}'.format(
                adb=self.adb_cmd, package=package, entry=entrypoint),
                cwd=self.buildozer.global_platform_dir)
        self.buildozer.environ.pop('ANDROID_SERIAL', None)

        self.buildozer.info('Application started.')

    def cmd_logcat(self, *args):
        '''Show the log from the device
        '''
        self.check_requirements()
        serial = self.serials[0:]
        if not serial:
            return
        self.buildozer.environ['ANDROID_SERIAL'] = serial[0]
        self.buildozer.cmd('{adb} logcat'.format(adb=self.adb_cmd),
                cwd=self.buildozer.global_platform_dir,
                show_output=True)
        self.buildozer.environ.pop('ANDROID_SERIAL', None)



def get_target(buildozer):
    return TargetAndroid(buildozer)
