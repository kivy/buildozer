'''
Android target, based on python-for-android project
'''
#
# Android target
# Thanks for Renpy (again) for its install_sdk.py and plat.py in the PGS4A
# project!
#

import sys
if sys.platform == 'win32':
    raise NotImplementedError('Windows platform not yet working for Android')

ANDROID_API = '19'
ANDROID_MINAPI = '9'
ANDROID_SDK_VERSION = '20'
ANDROID_NDK_VERSION = '9c'
APACHE_ANT_VERSION = '1.9.4'

import traceback
import os
import io
from pipes import quote
from sys import platform, executable
from buildozer import BuildozerException
from buildozer import IS_PY3
from buildozer.target import Target
from os import environ
from os.path import exists, join, realpath, expanduser, basename, relpath
from shutil import copyfile
from glob import glob

from buildozer.libs.version import parse


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
                    'android-ndk-r{0}'.format(version))

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
            self.android_cmd = join(self.android_sdk_dir, 'tools',
                                    'android.bat')
            self.adb_cmd = join(self.android_sdk_dir, 'platform-tools',
                                'adb.exe')
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

            # Check for C header <zlib.h>.
            _, _, returncode_dpkg = self.buildozer.cmd(
                'dpkg --version',
                break_on_error=False)
            is_debian_like = (returncode_dpkg == 0)
            if is_debian_like and \
                not self.buildozer.file_exists('/usr/include/zlib.h'):
                raise BuildozerException(
                    'zlib headers must be installed, '
                    'run: sudo apt-get install zlib1g-dev')

        # Need to add internally installed ant to path for external tools
        # like adb to use
        path = [join(self.apache_ant_dir, 'bin')]
        if 'PATH' in self.buildozer.environ:
            path.append(self.buildozer.environ['PATH'])
        else:
            path.append(os.environ['PATH'])
        self.buildozer.environ['PATH'] = ':'.join(path)
        checkbin = self.buildozer.checkbin
        checkbin('Git (git)', 'git')
        checkbin('Cython (cython)', 'cython')
        checkbin('Java compiler (javac)', self.javac_cmd)
        checkbin('Java keytool (keytool)', self.keytool_cmd)

    def check_configuration_tokens(self):
        errors = []

        # check the permission
        available_permissions = self._get_available_permissions()
        if available_permissions:
            permissions = self.buildozer.config.getlist(
                'app', 'android.permissions', [])
            for permission in permissions:
                # no check on full named permission
                # like com.google.android.providers.gsf.permission.READ_GSERVICES
                if '.' in permission:
                    continue
                permission = permission.upper()
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
            self.buildozer.debug(
                'Read available permissions from api-versions.xml')
            import xml.etree.ElementTree as ET
            fn = join(self.android_sdk_dir, 'platform-tools', 'api',
                      'api-versions.xml')
            with io.open(fn, encoding='utf-8') as fd:
                doc = ET.fromstring(fd.read())
            fields = doc.findall(
                './/class[@name="android/Manifest$permission"]/field[@name]')
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
        with _winreg.OpenKey(
            _winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\JavaSoft\Java Development Kit") as jdk:  #@UndefinedVariable
            current_version, _type = _winreg.QueryValueEx(
                jdk, "CurrentVersion"
            )  #@UndefinedVariable
            with _winreg.OpenKey(jdk,
                                 current_version) as cv:  #@UndefinedVariable
                java_home, _type = _winreg.QueryValueEx(cv, "JavaHome"
                                                        )  #@UndefinedVariable
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
        elif platform.startswith('linux'):
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

        import re
        _version = re.search('(.+?)[a-z]', self.android_ndk_version).group(1)

        self.buildozer.info('Android NDK is missing, downloading')
        if platform in ('win32', 'cygwin'):
            # Checking of 32/64 bits at Windows from: http://stackoverflow.com/a/1405971/798575
            import struct
            archive = 'android-ndk-r{0}-windows-{1}.zip'
            is_64 = (8 * struct.calcsize("P") == 64)

        elif platform in ('darwin', ):
            if int(_version) > 9:
                archive = 'android-ndk-r{0}-darwin-{1}.bin'
            else:
                archive = 'android-ndk-r{0}-darwin-{1}.tar.bz2'
            is_64 = (os.uname()[4] == 'x86_64')

        elif platform.startswith('linux'):
            if int(_version) > 9:  # if greater than 9, take it as .bin file
                archive = 'android-ndk-r{0}-linux-{1}.bin'
            else:
                archive = 'android-ndk-r{0}-linux-{1}.tar.bz2'
            is_64 = (os.uname()[4] == 'x86_64')
        else:
            raise SystemError('Unsupported platform: {0}'.format(platform))

        architecture = 'x86_64' if is_64 else 'x86'
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

    def _android_list_sdk(self, include_all=False):
        cmd = '{} list sdk -u -e'.format(self.android_cmd)
        if include_all:
            cmd += ' -a'
        available_packages = self.buildozer.cmd(
            cmd,
            cwd=self.buildozer.global_platform_dir,
            get_stdout=True)[0]

        # get only the line like -> id: 5 or "build-tools-19.0.1"
        # and extract the name part.
        print(available_packages)
        return [x.split('"')[1] for x in available_packages.splitlines()
                if x.startswith('id: ')]

    def _android_update_sdk(self, packages):
        from pexpect import EOF
        java_tool_options = environ.get('JAVA_TOOL_OPTIONS', '')
        child = self.buildozer.cmd_expect(
            '{} update sdk -u -a -t {}'.format(
                self.android_cmd, packages,
                cwd=self.buildozer.global_platform_dir),
            timeout=None,
            env={
                'JAVA_TOOL_OPTIONS': java_tool_options +
                ' -Dfile.encoding=UTF-8'
            })
        while True:
            index = child.expect([EOF, u'[y/n]: '])
            if index == 0:
                break
            child.sendline('y')

    def _build_package_string(self, package_name, version):
        return '{}-{}'.format(package_name, version)

    def _read_version_subdir(self, *args):
        versions = []
        if not os.path.exists(join(*args)):
            self.buildozer.debug(
                'build-tools folder not found {}'.format(join(*args)))
            return parse("0")
        for v in os.listdir(join(*args)):
            try:
                versions.append(parse(v))
            except:
                pass
        if not versions:
            self.buildozer.error(
                'Unable to find the latest version for {}'.format(join(*args)))
            return parse("0")
        return max(versions)

    def _find_latest_package(self, packages, key):
        package_versions = []
        for p in packages:
            if not p.startswith(key):
                continue
            version_string = p.split(key)[-1]
            version = parse(version_string)
            package_versions.append(version)
        if not package_versions:
            return
        return max(package_versions)

    def _install_android_packages(self):

        # if any of theses value change into the buildozer.spec, retry the
        # update
        cache_key = 'android:sdk_installation'
        cache_value = [
            self.android_api, self.android_minapi, self.android_ndk_version,
            self.android_sdk_dir, self.android_ndk_dir
        ]
        if self.buildozer.state.get(cache_key, None) == cache_value:
            return True

        # 3 pass installation.
        if not os.access(self.android_cmd, os.X_OK):
            self.buildozer.cmd('chmod ug+x {}'.format(self.android_cmd))

        # 1. update the tool and platform-tools if needed
        packages = self._android_list_sdk()
        if 'tools' in packages or 'platform-tools' in packages:
            self._android_update_sdk('tools,platform-tools')

        # 2. install the latest build tool
        v_build_tools = self._read_version_subdir(
            self.android_sdk_dir, 'build-tools')
        packages = self._android_list_sdk(include_all=True)
        ver = self._find_latest_package(packages, 'build-tools-')
        if ver and ver > v_build_tools:
            self._android_update_sdk(self._build_package_string('build-tools',
                                                                ver))
        # 2.bis check aidl can be runned
        self._check_aidl(v_build_tools)

        # 3. finally, install the android for the current api
        android_platform = join(self.android_sdk_dir, 'platforms',
                                'android-{0}'.format(self.android_api))
        if not self.buildozer.file_exists(android_platform):
            packages = self._android_list_sdk()
            android_package = 'android-{}'.format(self.android_api)
            if android_package in packages:
                self._android_update_sdk(android_package)

        self.buildozer.info('Android packages installation done.')

        self.buildozer.state[cache_key] = cache_value
        self.buildozer.state.sync()

    def _check_aidl(self, v_build_tools):
        self.buildozer.debug('Check that aidl can be executed')
        v_build_tools = self._read_version_subdir(
            self.android_sdk_dir, 'build-tools')
        aidl_cmd = join(self.android_sdk_dir, 'build-tools',
                        str(v_build_tools), 'aidl')
        self.buildozer.checkbin('Aidl', aidl_cmd)
        _, _, returncode = self.buildozer.cmd(aidl_cmd,
                                              break_on_error=False,
                                              show_output=False)
        if returncode != 1:
            self.buildozer.error('Aidl cannot be executed')
            if sys.maxint > 2 ** 32:
                self.buildozer.error('')
                self.buildozer.error(
                    'You might have missed to install 32bits libs')
                self.buildozer.error(
                    'Check http://buildozer.readthedocs.org/en/latest/installation.html')
                self.buildozer.error('')
            else:
                self.buildozer.error('')
                self.buildozer.error(
                    'In case of a bug report, please add a full log with log_level = 2')
                self.buildozer.error('')
            raise BuildozerException()

    def install_platform(self):
        cmd = self.buildozer.cmd
        self.pa_dir = pa_dir = join(self.buildozer.platform_dir,
                                    'python-for-android')
        if not self.buildozer.file_exists(pa_dir):
            system_p4a_dir = self.buildozer.config.getdefault(
                'app', 'android.p4a_dir')
            if system_p4a_dir:
                cmd('ln -sf {} ./python-for-android'.format(system_p4a_dir),
                    cwd=self.buildozer.platform_dir)
            else:
                cmd('git clone -b old_toolchain --single-branch '
                    'https://github.com/kivy/python-for-android.git',
                    cwd=self.buildozer.platform_dir)
        elif self.platform_update:
            cmd('git clean -dxf', cwd=pa_dir)
            cmd('git pull origin master', cwd=pa_dir)

        source = self.buildozer.config.getdefault('app', 'android.branch')
        if source:
            cmd('git checkout  %s' % (source), cwd=pa_dir)

        self._install_apache_ant()
        self._install_android_sdk()
        self._install_android_ndk()
        self._install_android_packages()

        # ultimate configuration check.
        # some of our configuration cannot be check without platform.
        self.check_configuration_tokens()

        self.buildozer.environ.update({
            'PACKAGES_PATH': self.buildozer.global_packages_dir,
            'ANDROIDSDK': self.android_sdk_dir,
            'ANDROIDNDK': self.android_ndk_dir,
            'ANDROIDAPI': self.android_api,
            'ANDROIDNDKVER': 'r{}'.format(self.android_ndk_version)
        })

    def get_available_packages(self):
        available_modules = self.buildozer.cmd(
            './distribute.sh -l',
            cwd=self.pa_dir,
            get_stdout=True)[0]
        if not available_modules.startswith('Available modules:'):
            self.buildozer.error('Python-for-android invalid output for -l')
        return available_modules[19:].splitlines()[0].split()

    def compile_platform(self):
        # for android, the compilation depends really on the app requirements.
        # compile the distribution only if the requirements changed.
        last_requirements = self.buildozer.state.get('android.requirements',
                                                     '')
        app_requirements = self.buildozer.config.getlist('app', 'requirements',
                                                         '')

        # we need to extract the requirements that python-for-android knows
        # about
        available_modules = self.get_available_packages()
        onlyname = lambda x: x.split('==')[0]
        android_requirements = [x for x in app_requirements
                                if onlyname(x) in available_modules]

        need_compile = 0
        if last_requirements != android_requirements:
            need_compile = 1

        dist_name = self.buildozer.config.get('app', 'package.name')
        dist_dir = join(self.pa_dir, 'dist', dist_name)
        dist_file = join(dist_dir, 'private', 'include', 'python2.7',
                         'pyconfig.h')
        if not exists(dist_file):
            need_compile = 1

        # len('requirements.source.') == 20, so use name[20:]
        source_dirs = {
            'P4A_{}_DIR'.format(name[20:]): realpath(expanduser(value))
            for name, value in self.buildozer.config.items('app')
            if name.startswith('requirements.source.')
        }
        if source_dirs:
            self.buildozer.environ.update(source_dirs)
            self.buildozer.info('Using custom source dirs:\n    {}'.format(
                '\n    '.join(['{} = {}'.format(k, v)
                               for k, v in source_dirs.items()])))

        last_source_requirements = self.buildozer.state.get(
            'android.requirements.source', {})
        if source_dirs != last_source_requirements:
            need_compile = 1

        if not need_compile:
            self.buildozer.info('Distribution already compiled, pass.')
            return

        modules_str = ' '.join(android_requirements)
        cmd = self.buildozer.cmd
        self.buildozer.debug('Clean and build python-for-android')
        self.buildozer.rmdir(dist_dir)  # Delete existing distribution to stop
        # p4a complaining
        cmd('./distribute.sh -m "{0}" -d "{1}"'.format(modules_str, dist_name),
            cwd=self.pa_dir)
        self.buildozer.debug('Remove temporary build files')
        self.buildozer.rmdir(join(self.pa_dir, 'build'))
        self.buildozer.rmdir(join(self.pa_dir, '.packages'))
        self.buildozer.rmdir(join(self.pa_dir, 'src', 'jni', 'obj', 'local'))
        self.buildozer.info('Distribution compiled.')

        # ensure we will not compile again
        self.buildozer.state['android.requirements'] = android_requirements
        self.buildozer.state['android.requirements.source'] = source_dirs
        self.buildozer.state.sync()

    def _get_package(self):
        config = self.buildozer.config
        package_domain = config.getdefault('app', 'package.domain', '')
        package = config.get('app', 'package.name')
        if package_domain:
            package = package_domain + '.' + package
        return package.lower()

    def _generate_whitelist(self, dist_dir):
        p4a_whitelist = self.buildozer.config.getlist(
            'app', 'android.p4a_whitelist') or []
        whitelist_fn = join(dist_dir, 'whitelist.txt')
        with open(whitelist_fn, 'w') as fd:
            for wl in p4a_whitelist:
                fd.write(wl + '\n')

    def build_package(self):
        dist_name = self.buildozer.config.get('app', 'package.name')
        dist_dir = join(self.pa_dir, 'dist', dist_name)
        config = self.buildozer.config
        package = self._get_package()
        version = self.buildozer.get_version()

        # add extra libs/armeabi files in dist/default/libs/armeabi
        # (same for armeabi-v7a, x86, mips)
        for config_key, lib_dir in (
            ('android.add_libs_armeabi', 'armeabi'),
            ('android.add_libs_armeabi_v7a', 'armeabi-v7a'),
            ('android.add_libs_x86', 'x86'), ('android.add_libs_mips', 'mips')
        ):

            patterns = config.getlist('app', config_key, [])
            if not patterns:
                continue

            self.buildozer.debug('Search and copy libs for {}'.format(lib_dir))
            for fn in self.buildozer.file_matches(patterns):
                self.buildozer.file_copy(
                    join(self.buildozer.root_dir, fn),
                    join(dist_dir, 'libs', lib_dir, basename(fn)))

        # update the project.properties libraries references
        self._update_libraries_references(dist_dir)

        # add src files
        self._add_java_src(dist_dir)

        # generate the whitelist if needed
        self._generate_whitelist(dist_dir)

        # build the app
        build_cmd = (
            '{python} build.py --name {name}'
            ' --version {version}'
            ' --package {package}'
            ' --{storage_type} {appdir}'
            ' --sdk {androidsdk}'
            ' --minsdk {androidminsdk}').format(
                python=executable,
                name=quote(config.get('app', 'title')),
                version=version,
                package=package,
                storage_type='private' if config.getbooldefault(
                    'app', 'android.private_storage', True) else 'dir',
                appdir=self.buildozer.app_dir,
                androidminsdk=config.getdefault(
                    'app', 'android.minsdk', self.android_minapi),
                androidsdk=config.getdefault(
                    'app', 'android.sdk', self.android_api))

        # add permissions
        permissions = config.getlist('app', 'android.permissions', [])
        for permission in permissions:
            # force the latest component to be uppercase
            permission = permission.split('.')
            permission[-1] = permission[-1].upper()
            permission = '.'.join(permission)
            build_cmd += ' --permission {}'.format(permission)

        # meta-data
        meta_datas = config.getlistvalues('app', 'android.meta_data', [])
        for meta in meta_datas:
            key, value = meta.split('=', 1)
            meta = '{}={}'.format(key.strip(), value.strip())
            build_cmd += ' --meta-data "{}"'.format(meta)

        # add extra Java jar files
        add_jars = config.getlist('app', 'android.add_jars', [])
        for pattern in add_jars:
            pattern = join(self.buildozer.root_dir, pattern)
            matches = glob(expanduser(pattern.strip()))
            if matches:
                for jar in matches:
                    build_cmd += ' --add-jar "{}"'.format(jar)
            else:
                raise SystemError(
                    'Failed to find jar file: {}'.format(pattern))

        # add presplash
        presplash = config.getdefault('app', 'presplash.filename', '')
        if presplash:
            build_cmd += ' --presplash {}'.format(join(self.buildozer.root_dir,
                                                       presplash))

        # add icon
        icon = config.getdefault('app', 'icon.filename', '')
        if icon:
            build_cmd += ' --icon {}'.format(join(self.buildozer.root_dir,
                                                  icon))

        # OUYA Console support
        ouya_category = config.getdefault('app', 'android.ouya.category',
                                          '').upper()
        if ouya_category:
            if ouya_category not in ('GAME', 'APP'):
                raise SystemError(
                    'Invalid android.ouya.category: "{}" must be one of GAME or APP'.format(
                        ouya_category))
            # add icon
            build_cmd += ' --ouya-category {}'.format(ouya_category)
            ouya_icon = config.getdefault('app', 'android.ouya.icon.filename',
                                          '')
            build_cmd += ' --ouya-icon {}'.format(join(self.buildozer.root_dir,
                                                       ouya_icon))

        # add orientation
        orientation = config.getdefault('app', 'orientation', 'landscape')
        if orientation == 'all':
            orientation = 'sensor'
        build_cmd += ' --orientation {}'.format(orientation)

        # fullscreen ?
        fullscreen = config.getbooldefault('app', 'fullscreen', True)
        if not fullscreen:
            build_cmd += ' --window'

        # wakelock ?
        wakelock = config.getbooldefault('app', 'android.wakelock', False)
        if wakelock:
            build_cmd += ' --wakelock'

        # intent filters
        intent_filters = config.getdefault('app',
                                           'android.manifest.intent_filters',
                                           '')
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
        apktitle = ''.join([x for x in config.get('app', 'title')
                            if x not in bl])
        apk = '{title}-{version}-{mode}.apk'.format(
            title=apktitle,
            version=version,
            mode=mode)

        # copy to our place
        copyfile(join(dist_dir, 'bin', apk), join(self.buildozer.bin_dir, apk))

        self.buildozer.info('Android packaging done!')
        self.buildozer.info(
            'APK {0} available in the bin directory'.format(apk))
        self.buildozer.state['android:latestapk'] = apk
        self.buildozer.state['android:latestmode'] = self.build_mode

    def _update_libraries_references(self, dist_dir):
        # ensure the project.properties exist
        project_fn = join(dist_dir, 'project.properties')

        if not self.buildozer.file_exists(project_fn):
            content = ['target=android-{}\n'.format(self.android_api)]
        else:
            with io.open(project_fn, encoding='utf-8') as fd:
                content = fd.readlines()

        # extract library reference
        references = []
        for line in content[:]:
            if not line.startswith('android.library.reference.'):
                continue
            content.remove(line)

        # convert our references to relative path
        app_references = self.buildozer.config.getlist(
            'app', 'android.library_references', [])
        source_dir = realpath(
            self.buildozer.config.getdefault('app', 'source.dir', '.'))
        for cref in app_references:
            # get the full path of the current reference
            ref = realpath(join(source_dir, cref))
            if not self.buildozer.file_exists(ref):
                self.buildozer.error(
                    'Invalid library reference (path not found): {}'.format(
                        cref))
                exit(1)
            # get a relative path from the project file
            ref = relpath(ref, realpath(dist_dir))
            # ensure the reference exists
            references.append(ref)

        # recreate the project.properties
        with io.open(project_fn, 'w', encoding='utf-8') as fd:
            for line in content:
                if IS_PY3:
                    fd.write(line)
                else:
                    fd.write(line.decode('utf-8'))
            for index, ref in enumerate(references):
                fd.write(u'android.library.reference.{}={}\n'.format(
                    index + 1, ref))

        self.buildozer.debug('project.properties updated')

    def _add_java_src(self, dist_dir):
        java_src = self.buildozer.config.getlist('app', 'android.add_src', [])
        src_dir = join(dist_dir, 'src')
        for pattern in java_src:
            for fn in glob(expanduser(pattern.strip())):
                last_component = basename(fn)
                self.buildozer.file_copytree(fn, join(src_dir, last_component))

    @property
    def serials(self):
        if hasattr(self, '_serials'):
            return self._serials
        serial = environ.get('ANDROID_SERIAL')
        if serial:
            return serial.split(',')
        l = self.buildozer.cmd('{} devices'.format(self.adb_cmd),
                               get_stdout=True)[0].splitlines()
        serials = []
        for serial in l:
            if not serial:
                continue
            if serial.startswith('*') or serial.startswith('List '):
                continue
            serials.append(serial.split()[0])
        self._serials = serials
        return serials

    def cmd_deploy(self, *args):
        super(TargetAndroid, self).cmd_deploy(*args)
        state = self.buildozer.state
        if 'android:latestapk' not in state:
            self.buildozer.error('No APK built yet. Run "debug" first.')

        if state.get('android:latestmode', '') != 'debug':
            self.buildozer.error('Only debug APK are supported for deploy')

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
                self.adb_cmd, full_apk),
                               cwd=self.buildozer.global_platform_dir)
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
                    adb=self.adb_cmd,
                    package=package,
                    entry=entrypoint),
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
