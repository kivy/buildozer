'''
Android target, based on python-for-android project
'''

import sys
if sys.platform == 'win32':
    raise NotImplementedError('Windows platform not yet working for Android')

from platform import uname
WSL = 'Microsoft' in uname()[2]

ANDROID_API = '27'
ANDROID_MINAPI = '21'
APACHE_ANT_VERSION = '1.9.4'

# This constant should *not* be updated, it is used only in the case
# that python-for-android cannot provide a recommendation, which in
# turn only happens if the python-for-android is old and probably
# doesn't support any newer NDK.
DEFAULT_ANDROID_NDK_VERSION = '17c'

import traceback
import os
import io
import re
import ast
from pipes import quote
from sys import platform, executable
from buildozer import BuildozerException, USE_COLOR
from buildozer.target import Target
from os import environ
from os.path import exists, join, realpath, expanduser, basename, relpath
from platform import architecture
from shutil import copyfile, rmtree
from glob import glob

from buildozer.libs.version import parse
from distutils.version import LooseVersion

# buildozer.spec tokens that used to exist but are now ignored
DEPRECATED_TOKENS = (('app', 'android.sdk'), )

# Default SDK tag to download. This is not a configurable option
# because it doesn't seem to matter much, it is normally correct to
# download once then update all the components as buildozer already
# does.
DEFAULT_SDK_TAG = '6514223'

DEFAULT_ARCH = 'armeabi-v7a'

MSG_P4A_RECOMMENDED_NDK_ERROR = (
    "WARNING: Unable to find recommended Android NDK for current "
    "installation of python-for-android, defaulting to the default "
    "version r{android_ndk}".format(android_ndk=DEFAULT_ANDROID_NDK_VERSION)
)


class TargetAndroid(Target):
    targetname = 'android'
    p4a_directory_name = "python-for-android"
    p4a_fork = 'kivy'
    p4a_branch = 'master'
    p4a_apk_cmd = "apk --debug --bootstrap="
    p4a_recommended_ndk_version = None
    extra_p4a_args = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._arch = self.buildozer.config.getdefault(
            'app', 'android.arch', DEFAULT_ARCH)
        self._build_dir = join(
            self.buildozer.platform_dir, 'build-{}'.format(self._arch))
        executable = sys.executable or 'python'
        self._p4a_cmd = '{} -m pythonforandroid.toolchain '.format(executable)
        self._p4a_bootstrap = self.buildozer.config.getdefault(
            'app', 'p4a.bootstrap', 'sdl2')
        self.p4a_apk_cmd += self._p4a_bootstrap
        color = 'always' if USE_COLOR else 'never'
        self.extra_p4a_args = ' --color={} --storage-dir="{}"'.format(
            color, self._build_dir)

        # minapi should match ndk-api, so can use the same default if
        # nothing is specified
        ndk_api = self.buildozer.config.getdefault(
            'app', 'android.ndk_api', self.android_minapi)
        self.extra_p4a_args += ' --ndk-api={}'.format(ndk_api)

        hook = self.buildozer.config.getdefault("app", "p4a.hook", None)
        if hook is not None:
            self.extra_p4a_args += ' --hook={}'.format(realpath(hook))
        port = self.buildozer.config.getdefault('app', 'p4a.port', None)
        if port is not None:
            self.extra_p4a_args += ' --port={}'.format(port)

        self.warn_on_deprecated_tokens()

    def warn_on_deprecated_tokens(self):
        for section, token in DEPRECATED_TOKENS:
            value = self.buildozer.config.getdefault(section, token, None)
            if value is not None:
                error = ('WARNING: Config token {} {} is deprecated and ignored, '
                         'but you set value {}').format(section, token, value)
                self.buildozer.error(error)

    def _p4a(self, cmd, **kwargs):
        kwargs.setdefault('cwd', self.p4a_dir)
        return self.buildozer.cmd(self._p4a_cmd + cmd + self.extra_p4a_args, **kwargs)

    @property
    def p4a_dir(self):
        """The directory where python-for-android is/will be installed."""

        # Default p4a dir
        p4a_dir = join(self.buildozer.platform_dir, self.p4a_directory_name)

        # Possibly overriden by user setting
        system_p4a_dir = self.buildozer.config.getdefault('app', 'p4a.source_dir')
        if system_p4a_dir:
            p4a_dir = expanduser(system_p4a_dir)

        return p4a_dir

    @property
    def p4a_recommended_android_ndk(self):
        """
        Return the p4a's recommended android's NDK version, depending on the
        p4a version used for our buildozer build. In case that we don't find
        it, we will return the buildozer's recommended one, defined by global
        variable `DEFAULT_ANDROID_NDK_VERSION`.
        """
        # make sure to read p4a version only the first time
        if self.p4a_recommended_ndk_version is not None:
            return self.p4a_recommended_ndk_version

        # check p4a's recommendation file, and in case that exists find the
        # recommended android's NDK version, otherwise return buildozer's one
        ndk_version = DEFAULT_ANDROID_NDK_VERSION
        rec_file = join(self.p4a_dir, "pythonforandroid", "recommendations.py")
        if not os.path.isfile(rec_file):
            self.buildozer.error(MSG_P4A_RECOMMENDED_NDK_ERROR)
            return ndk_version

        for line in open(rec_file, "r"):
            if line.startswith("RECOMMENDED_NDK_VERSION ="):
                ndk_version = line.replace(
                    "RECOMMENDED_NDK_VERSION =", "")
                # clean version of unwanted characters
                for i in {"'", '"', "\n", " "}:
                    ndk_version = ndk_version.replace(i, "")
                self.buildozer.info(
                    "Recommended android's NDK version by p4a is: {}".format(
                        ndk_version
                    )
                )
                self.p4a_recommended_ndk_version = ndk_version
                break
        return ndk_version

    def _sdkmanager(self, *args, **kwargs):
        """Call the sdkmanager in our Android SDK with the given arguments."""
        # Use the android-sdk dir as cwd by default
        android_sdk_dir = self.android_sdk_dir
        kwargs['cwd'] = kwargs.get('cwd', android_sdk_dir)
        sdkmanager_path = self.sdkmanager_path
        sdk_root = f"--sdk_root={android_sdk_dir}"
        command = f"{sdkmanager_path} {sdk_root} " + ' '.join(args)
        return_child = kwargs.pop('return_child', False)
        if return_child:
            return self.buildozer.cmd_expect(command, **kwargs)
        else:
            kwargs['get_stdout'] = kwargs.get('get_stdout', True)
            return self.buildozer.cmd(command, **kwargs)

    @property
    def android_ndk_version(self):
        return self.buildozer.config.getdefault('app', 'android.ndk',
                                                self.p4a_recommended_android_ndk)

    @property
    def android_api(self):
        return self.buildozer.config.getdefault('app', 'android.api',
                                                ANDROID_API)

    @property
    def android_minapi(self):
        return self.buildozer.config.getdefault('app', 'android.minapi',
                                                ANDROID_MINAPI)

    @property
    def android_sdk_dir(self):
        directory = expanduser(self.buildozer.config.getdefault(
            'app', 'android.sdk_path', ''))
        if directory:
            return realpath(directory)
        return join(self.buildozer.global_platform_dir,
                    'android-sdk')

    @property
    def android_ndk_dir(self):
        directory = expanduser(self.buildozer.config.getdefault(
            'app', 'android.ndk_path', ''))
        if directory:
            return realpath(directory)
        version = self.buildozer.config.getdefault('app', 'android.ndk',
                                                   self.android_ndk_version)
        return join(self.buildozer.global_platform_dir,
                    'android-ndk-r{0}'.format(version))

    @property
    def apache_ant_dir(self):
        directory = expanduser(self.buildozer.config.getdefault(
            'app', 'android.ant_path', ''))
        if directory:
            return realpath(directory)
        version = self.buildozer.config.getdefault('app', 'android.ant',
                                                   APACHE_ANT_VERSION)
        return join(self.buildozer.global_platform_dir,
                    'apache-ant-{0}'.format(version))

    @property
    def sdkmanager_path(self):
        sdkmanager_path = join(
            self.android_sdk_dir, 'tools', 'bin', 'sdkmanager')
        if not os.path.isfile(sdkmanager_path):
            raise BuildozerException(
                ('sdkmanager path "{}" does not exist, sdkmanager is not'
                 'installed'.format(sdkmanager_path)))
        return sdkmanager_path

    def check_requirements(self):
        if platform in ('win32', 'cygwin'):
            try:
                self._set_win32_java_home()
            except:
                traceback.print_exc()
            self.adb_cmd = join(self.android_sdk_dir, 'platform-tools',
                                'adb.exe')
            self.javac_cmd = self._locate_java('javac.exe')
            self.keytool_cmd = self._locate_java('keytool.exe')
        elif platform in ('darwin', ):
            self.adb_cmd = join(self.android_sdk_dir, 'platform-tools', 'adb')
            self.javac_cmd = self._locate_java('javac')
            self.keytool_cmd = self._locate_java('keytool')
        else:
            self.adb_cmd = join(self.android_sdk_dir, 'platform-tools', 'adb')
            self.javac_cmd = self._locate_java('javac')
            self.keytool_cmd = self._locate_java('keytool')

            # Check for C header <zlib.h>.
            _, _, returncode_dpkg = self.buildozer.cmd('dpkg --version',
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

        super().check_configuration_tokens(errors)

    def _get_available_permissions(self):
        key = 'android:available_permissions'
        key_sdk = 'android:available_permissions_sdk'

        current_platform_tools = self._android_get_installed_platform_tools_version()

        refresh_permissions = False
        sdk = self.buildozer.state.get(key_sdk, None)
        if not sdk or sdk != current_platform_tools:
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
            self.buildozer.state[key_sdk] = current_platform_tools
            return available_permissions
        except:
            return None

    def _set_win32_java_home(self):
        if 'JAVA_HOME' in self.buildozer.environ:
            return
        import _winreg
        with _winreg.OpenKey(
                _winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\JavaSoft\Java Development Kit") as jdk:  # @UndefinedVariable
            current_version, _type = _winreg.QueryValueEx(
                jdk, "CurrentVersion")  # @UndefinedVariable
            with _winreg.OpenKey(jdk, current_version) as cv:  # @UndefinedVariable
                java_home, _type = _winreg.QueryValueEx(
                    cv, "JavaHome")  # @UndefinedVariable
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

        if not os.path.exists(ant_dir):
            os.makedirs(ant_dir)

        self.buildozer.info('Android ANT is missing, downloading')
        archive = 'apache-ant-{0}-bin.tar.gz'.format(APACHE_ANT_VERSION)
        url = 'http://archive.apache.org/dist/ant/binaries/'
        self.buildozer.download(url,
                                archive,
                                cwd=ant_dir)
        self.buildozer.file_extract(archive,
                                    cwd=ant_dir)
        self.buildozer.info('Apache ANT installation done.')
        return ant_dir

    def _install_android_sdk(self):
        sdk_dir = self.android_sdk_dir
        if self.buildozer.file_exists(sdk_dir):
            self.buildozer.info('Android SDK found at {0}'.format(sdk_dir))
            return sdk_dir

        self.buildozer.info('Android SDK is missing, downloading')
        if platform in ('win32', 'cygwin'):
            archive = 'commandlinetools-win-{}_latest.zip'.format(DEFAULT_SDK_TAG)
        elif platform in ('darwin', ):
            archive = 'commandlinetools-mac-{}_latest.zip'.format(DEFAULT_SDK_TAG)
        elif platform.startswith('linux'):
            archive = 'commandlinetools-linux-{}_latest.zip'.format(DEFAULT_SDK_TAG)
        else:
            raise SystemError('Unsupported platform: {0}'.format(platform))

        if not os.path.exists(sdk_dir):
            os.makedirs(sdk_dir)

        url = 'https://dl.google.com/android/repository/'
        self.buildozer.download(url,
                                archive,
                                cwd=sdk_dir)

        self.buildozer.info('Unpacking Android SDK')
        self.buildozer.file_extract(archive,
                                    cwd=sdk_dir)

        self.buildozer.info('Android SDK tools base installation done.')

        return sdk_dir

    def _install_android_ndk(self):
        ndk_dir = self.android_ndk_dir
        if self.buildozer.file_exists(ndk_dir):
            self.buildozer.info('Android NDK found at {0}'.format(ndk_dir))
            return ndk_dir

        import re
        _version = re.search('(.+?)[a-z]', self.android_ndk_version).group(1)

        self.buildozer.info('Android NDK is missing, downloading')
        # Welcome to the NDK URL hell!
        # a list of all NDK URLs up to level 14 can be found here:
        #  https://gist.github.com/roscopecoltran/43861414fbf341adac3b6fa05e7fad08
        # it seems that from level 11 on the naming schema is consistent
        # from 10e on the URLs can be looked up at
        # https://developer.android.com/ndk/downloads/older_releases

        if platform in ('win32', 'cygwin'):
            # Checking of 32/64 bits at Windows from: http://stackoverflow.com/a/1405971/798575
            import struct
            archive = 'android-ndk-r{0}-windows-{1}.zip'
            is_64 = (8 * struct.calcsize("P") == 64)

        elif platform in ('darwin', ):
            if _version >= '10e':
                archive = 'android-ndk-r{0}-darwin-{1}.zip'
            elif _version >= '10c':
                archive = 'android-ndk-r{0}-darwin-{1}.bin'
            else:
                archive = 'android-ndk-r{0}-darwin-{1}.tar.bz2'
            is_64 = (os.uname()[4] == 'x86_64')

        elif platform.startswith('linux'):
            if _version >= '10e':
                archive = 'android-ndk-r{0}-linux-{1}.zip'
            elif _version >= '10c':
                archive = 'android-ndk-r{0}-linux-{1}.bin'
            else:
                archive = 'android-ndk-r{0}-linux-{1}.tar.bz2'
            is_64 = (os.uname()[4] == 'x86_64')
        else:
            raise SystemError('Unsupported platform: {}'.format(platform))

        architecture = 'x86_64' if is_64 else 'x86'
        unpacked = 'android-ndk-r{0}'
        archive = archive.format(self.android_ndk_version, architecture)
        unpacked = unpacked.format(self.android_ndk_version)

        if _version >= '10e':
            url = 'https://dl.google.com/android/repository/'
        else:
            url = 'http://dl.google.com/android/ndk/'

        self.buildozer.download(url,
                                archive,
                                cwd=self.buildozer.global_platform_dir)

        self.buildozer.info('Unpacking Android NDK')
        self.buildozer.file_extract(archive,
                                    cwd=self.buildozer.global_platform_dir)
        self.buildozer.file_rename(unpacked,
                                   ndk_dir,
                                   cwd=self.buildozer.global_platform_dir)
        self.buildozer.info('Android NDK installation done.')
        return ndk_dir

    def _android_list_build_tools_versions(self):
        available_packages = self._sdkmanager('--list')

        lines = available_packages[0].split('\n')

        build_tools_versions = []

        for line in lines:
            if not line.strip().startswith('build-tools;'):
                continue
            package_name = line.strip().split(' ')[0]
            assert package_name.count(';') == 1, (
                'could not parse package "{}"'.format(package_name))
            version = package_name.split(';')[1]

            build_tools_versions.append(parse(version))

        return build_tools_versions

    def _android_get_installed_platform_tools_version(self):
        """
        Crudely parse out the installed platform-tools version
        """

        platform_tools_dir = os.path.join(
            self.android_sdk_dir,
            'platform-tools')

        if not os.path.exists(platform_tools_dir):
            return None

        data_file = os.path.join(platform_tools_dir, 'source.properties')
        if not os.path.exists(data_file):
            return None

        with open(data_file, 'r') as fileh:
            lines = fileh.readlines()

        for line in lines:
            if line.startswith('Pkg.Revision='):
                break
        else:
            self.buildozer.error('Read {} but found no Pkg.Revision'.format(data_file))
            # Don't actually exit, in case the build env is
            # okay. Something else will fault if it's important.
            return None

        revision = line.split('=')[1].strip()

        return revision

    def _android_update_sdk(self, *sdkmanager_commands):
        """Update the tools and package-tools if possible"""
        auto_accept_license = self.buildozer.config.getbooldefault(
            'app', 'android.accept_sdk_license', False)

        kwargs = {}
        if auto_accept_license:
            # `SIGPIPE` is not being reported somehow, but `EPIPE` is.
            # This leads to a stderr "Broken pipe" message which is harmless,
            # but doesn't look good on terminal, hence redirecting to /dev/null
            yes_command = 'yes 2>/dev/null'
            android_sdk_dir = self.android_sdk_dir
            sdkmanager_path = self.sdkmanager_path
            sdk_root = f"--sdk_root={android_sdk_dir}"
            command = f"{yes_command} | {sdkmanager_path} {sdk_root} --licenses"
            self.buildozer.cmd(command, cwd=self.android_sdk_dir)
        else:
            kwargs['show_output'] = True

        self._sdkmanager(*sdkmanager_commands, **kwargs)

    def _read_version_subdir(self, *args):
        versions = []
        if not os.path.exists(join(*args)):
            self.buildozer.debug('build-tools folder not found {}'.format(join(
                *args)))
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

        # 1. update the platform-tools package if needed

        skip_upd = self.buildozer.config.getbooldefault(
            'app', 'android.skip_update', False)

        if not skip_upd:
            self.buildozer.info('Installing/updating SDK platform tools if necessary')

            # just calling sdkmanager with the items will install them if necessary
            self._android_update_sdk('platform-tools')
            self._android_update_sdk('--update')
        else:
            self.buildozer.info('Skipping Android SDK update due to spec file setting')
            self.buildozer.info('Note: this also prevents installing missing '
                                'SDK components')

        # 2. install the latest build tool
        self.buildozer.info('Updating SDK build tools if necessary')
        installed_v_build_tools = self._read_version_subdir(self.android_sdk_dir,
                                                  'build-tools')
        available_v_build_tools = self._android_list_build_tools_versions()
        if not available_v_build_tools:
            self.buildozer.error('Did not find any build tools available to download')

        latest_v_build_tools = sorted(available_v_build_tools)[-1]
        if latest_v_build_tools > installed_v_build_tools:
            if not skip_upd:
                self._android_update_sdk(
                    '"build-tools;{}"'.format(latest_v_build_tools))
                installed_v_build_tools = latest_v_build_tools
            else:
                self.buildozer.info(
                    'Skipping update to build tools {} due to spec setting'.format(
                        latest_v_build_tools))

        # 2. check aidl can be run
        self._check_aidl(installed_v_build_tools)

        # 3. finally, install the android for the current api
        self.buildozer.info('Downloading platform api target if necessary')
        android_platform = join(self.android_sdk_dir, 'platforms', 'android-{}'.format(self.android_api))
        if not self.buildozer.file_exists(android_platform):
            if not skip_upd:
                self._sdkmanager('"platforms;android-{}"'.format(self.android_api))
            else:
                self.buildozer.info(
                    'Skipping install API {} platform tools due to spec setting'.format(
                        self.android_api))

        self.buildozer.info('Android packages installation done.')

        self.buildozer.state[cache_key] = cache_value
        self.buildozer.state.sync()

    def _check_aidl(self, v_build_tools):
        self.buildozer.debug('Check that aidl can be executed')
        v_build_tools = self._read_version_subdir(self.android_sdk_dir,
                                                  'build-tools')
        aidl_cmd = join(self.android_sdk_dir, 'build-tools',
                        str(v_build_tools), 'aidl')
        self.buildozer.checkbin('Aidl', aidl_cmd)
        _, _, returncode = self.buildozer.cmd(aidl_cmd,
                                              break_on_error=False,
                                              show_output=False)
        if returncode != 1:
            self.buildozer.error('Aidl cannot be executed')
            if architecture()[0] == '64bit':
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
        self._install_p4a()
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
            'ANDROIDMINAPI': self.android_minapi,
        })

    def _install_p4a(self):
        cmd = self.buildozer.cmd
        p4a_fork = self.buildozer.config.getdefault(
            'app', 'p4a.fork', self.p4a_fork
        )
        p4a_branch = self.buildozer.config.getdefault(
            'app', 'p4a.branch', self.p4a_branch
        )

        p4a_dir = self.p4a_dir
        system_p4a_dir = self.buildozer.config.getdefault('app',
                                                          'p4a.source_dir')
        if system_p4a_dir:
            # Don't install anything, just check that the dir does exist
            if not self.buildozer.file_exists(p4a_dir):
                self.buildozer.error(
                    'Path for p4a.source_dir does not exist')
                self.buildozer.error('')
                raise BuildozerException()
        else:
            # check that fork/branch has not been changed
            if self.buildozer.file_exists(p4a_dir):
                cur_fork = cmd(
                    'git config --get remote.origin.url',
                    get_stdout=True,
                    cwd=p4a_dir,
                )[0].split('/')[3]
                cur_branch = cmd(
                    'git branch -vv', get_stdout=True, cwd=p4a_dir
                )[0].split()[1]
                if any([cur_fork != p4a_fork, cur_branch != p4a_branch]):
                    self.buildozer.info(
                        "Detected old fork/branch ({}/{}), deleting...".format(
                            cur_fork, cur_branch
                        )
                    )
                    rmtree(p4a_dir)

            if not self.buildozer.file_exists(p4a_dir):
                cmd(
                    (
                        'git clone -b {p4a_branch} --single-branch '
                        'https://github.com/{p4a_fork}/python-for-android.git '
                        '{p4a_dir}'
                    ).format(
                        p4a_branch=p4a_branch,
                        p4a_fork=p4a_fork,
                        p4a_dir=self.p4a_directory_name,
                    ),
                    cwd=self.buildozer.platform_dir,
                )
            elif self.platform_update:
                cmd('git clean -dxf', cwd=p4a_dir)
                current_branch = cmd('git rev-parse --abbrev-ref HEAD',
                                     get_stdout=True, cwd=p4a_dir)[0].strip()
                if current_branch == p4a_branch:
                    cmd('git pull', cwd=p4a_dir)
                else:
                    cmd('git fetch --tags origin {0}:{0}'.format(p4a_branch),
                        cwd=p4a_dir)
                    cmd('git checkout {}'.format(p4a_branch), cwd=p4a_dir)

        # also install dependencies (currently, only setup.py knows about it)
        # let's extract them.
        try:
            with open(join(self.p4a_dir, "setup.py")) as fd:
                setup = fd.read()
                deps = re.findall(r"^\s*install_reqs = (\[[^\]]*\])", setup, re.DOTALL | re.MULTILINE)[0]
                deps = ast.literal_eval(deps)
        except IOError:
            self.buildozer.error('Failed to read python-for-android setup.py at {}'.format(
                join(self.p4a_dir, 'setup.py')))
            exit(1)
        pip_deps = []
        for dep in deps:
            pip_deps.append("'{}'".format(dep))

        # in virtualenv or conda env
        options = "--user"
        if "VIRTUAL_ENV" in os.environ or "CONDA_PREFIX" in os.environ:
            options = ""
        cmd('{} -m pip install -q {} {}'.format(executable, options, " ".join(pip_deps)))

    def compile_platform(self):
        app_requirements = self.buildozer.config.getlist(
            'app', 'requirements', '')
        dist_name = self.buildozer.config.get('app', 'package.name')
        local_recipes = self.get_local_recipes_dir()
        requirements = ','.join(app_requirements)
        options = []

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

        if self.buildozer.config.getbooldefault('app', 'android.copy_libs', True):
            options.append("--copy-libs")
        # support for recipes in a local directory within the project
        if local_recipes:
            options.append('--local-recipes')
            options.append(local_recipes)
        self._p4a(
            ("create --dist_name={} --bootstrap={} --requirements={} "
             "--arch {} {}").format(
                 dist_name, self._p4a_bootstrap, requirements,
                 self._arch, " ".join(options)),
            get_stdout=True)[0]

    def get_available_packages(self):
        return True

    def get_dist_dir(self, dist_name, arch):
        """Find the dist dir with the given name and target arch, if one
        already exists, otherwise return a new dist_dir name.
        """
        expected_dist_name = generate_dist_folder_name(dist_name, arch_names=[arch])

        # If the expected dist name does exist, simply use that
        expected_dist_dir = join(self._build_dir, 'dists', expected_dist_name)
        if exists(expected_dist_dir):
            return expected_dist_dir

        # For backwards compatibility, check if a directory without
        # the arch exists. If so, this is probably the target dist.
        old_dist_dir = join(self._build_dir, 'dists', dist_name)
        if exists(old_dist_dir):
            return old_dist_dir

        # If no directory has been found yet, our dist probably
        # doesn't exist yet, so use the expected name
        return expected_dist_dir

    def get_local_recipes_dir(self):
        local_recipes = self.buildozer.config.getdefault('app', 'p4a.local_recipes')
        return realpath(expanduser(local_recipes)) if local_recipes else None

    def execute_build_package(self, build_cmd):
        # wrapper from previous old_toolchain to new toolchain
        dist_name = self.buildozer.config.get('app', 'package.name')
        local_recipes = self.get_local_recipes_dir()
        cmd = [self.p4a_apk_cmd, "--dist_name", dist_name]
        for args in build_cmd:
            option, values = args[0], args[1:]
            if option == "debug":
                continue
            elif option == "release":
                cmd.append("--release")
                if self.check_p4a_sign_env(True):
                    cmd.append("--sign")
                continue
            if option == "--window":
                cmd.append("--window")
            elif option == "--sdk":
                cmd.append("--android_api")
                cmd.extend(values)
            else:
                cmd.extend(args)

        # support for presplash background color
        presplash_color = self.buildozer.config.getdefault('app', 'android.presplash_color', None)
        if presplash_color:
            cmd.append('--presplash-color')
            cmd.append("'{}'".format(presplash_color))

        # support for services
        services = self.buildozer.config.getlist('app', 'services', [])
        for service in services:
            cmd.append("--service")
            cmd.append(service)

        # support for copy-libs
        if self.buildozer.config.getbooldefault('app', 'android.copy_libs', True):
            cmd.append("--copy-libs")

        # support for recipes in a local directory within the project
        if local_recipes:
            cmd.append('--local-recipes')
            cmd.append(local_recipes)

        # support for blacklist/whitelist filename
        whitelist_src = self.buildozer.config.getdefault('app', 'android.whitelist_src', None)
        blacklist_src = self.buildozer.config.getdefault('app', 'android.blacklist_src', None)
        if whitelist_src:
            cmd.append('--whitelist')
            cmd.append(realpath(whitelist_src))
        if blacklist_src:
            cmd.append('--blacklist')
            cmd.append(realpath(blacklist_src))

        # support for aars
        aars = self.buildozer.config.getlist('app', 'android.add_aars', [])
        for aar in aars:
            cmd.append('--add-aar')
            cmd.append(realpath(aar))

        # support for uses-lib
        uses_library = self.buildozer.config.getlist(
            'app', 'android.uses_library', '')
        for lib in uses_library:
            cmd.append('--uses-library={}'.format(lib))

        # support for gradle dependencies
        gradle_dependencies = self.buildozer.config.getlist('app', 'android.gradle_dependencies', [])
        for gradle_dependency in gradle_dependencies:
            cmd.append('--depend')
            cmd.append(gradle_dependency)

        cmd.append('--arch')
        cmd.append(self._arch)

        cmd = " ".join(cmd)
        self._p4a(cmd)

    def get_release_mode(self):
        if self.check_p4a_sign_env():
            return "release"
        return "release-unsigned"

    def check_p4a_sign_env(self, error=False):
        keys = ["KEYALIAS", "KEYSTORE_PASSWD", "KEYSTORE", "KEYALIAS_PASSWD"]
        check = True
        for key in keys:
            key = "P4A_RELEASE_{}".format(key)
            if key not in os.environ:
                if error:
                    self.buildozer.error(
                        ("Asking for release but {} is missing"
                         "--sign will not be passed").format(key))
                check = False
        return check

    def cmd_run(self, *args):
        entrypoint = self.buildozer.config.getdefault(
            'app', 'android.entrypoint')
        if not entrypoint:
            self.buildozer.config.set('app', 'android.entrypoint', 'org.kivy.android.PythonActivity')

        super().cmd_run(*args)

        entrypoint = self.buildozer.config.getdefault(
            'app', 'android.entrypoint', 'org.kivy.android.PythonActivity')

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

    def cmd_p4a(self, *args):
        '''
        Run p4a commands. Args must come after --, or
        use --alias to make an alias
        '''
        self.check_requirements()
        self.install_platform()
        args = args[0]
        if args and args[0] == '--alias':
            print('To set up p4a in this shell session, execute:')
            print('    alias p4a=$(buildozer {} p4a --alias 2>&1 >/dev/null)'
                  .format(self.targetname))
            sys.stderr.write('PYTHONPATH={} {}\n'.format(self.p4a_dir, self._p4a_cmd))
        else:
            self._p4a(' '.join(args) if args else '')

    def cmd_clean(self, *args):
        '''
        Clean the build and distribution
        '''
        self._p4a("clean_builds")
        self._p4a("clean_dists")

    def _get_package(self):
        config = self.buildozer.config
        package_domain = config.getdefault('app', 'package.domain', '')
        package = config.get('app', 'package.name')
        if package_domain:
            package = package_domain + '.' + package
        return package.lower()

    def _generate_whitelist(self, dist_dir):
        p4a_whitelist = self.buildozer.config.getlist(
            'app', 'android.whitelist') or []
        whitelist_fn = join(dist_dir, 'whitelist.txt')
        with open(whitelist_fn, 'w') as fd:
            for wl in p4a_whitelist:
                fd.write(wl + '\n')

    def build_package(self):
        dist_name = self.buildozer.config.get('app', 'package.name')
        arch = self.buildozer.config.getdefault('app', 'android.arch', DEFAULT_ARCH)
        dist_dir = self.get_dist_dir(dist_name, arch)
        config = self.buildozer.config
        package = self._get_package()
        version = self.buildozer.get_version()

        # add extra libs/armeabi files in dist/default/libs/armeabi
        # (same for armeabi-v7a, arm64-v8a, x86, mips)
        for config_key, lib_dir in (
                ('android.add_libs_armeabi', 'armeabi'),
                ('android.add_libs_armeabi_v7a', 'armeabi-v7a'),
                ('android.add_libs_arm64_v8a', 'arm64-v8a'),
                ('android.add_libs_x86', 'x86'),
                ('android.add_libs_mips', 'mips')):

            patterns = config.getlist('app', config_key, [])
            if not patterns:
                continue
            if self._arch != lib_dir:
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
        build_cmd = [
            ("--name", quote(config.get('app', 'title'))),
            ("--version", version),
            ("--package", package),
            ("--minsdk", config.getdefault('app', 'android.minapi',
                                           self.android_minapi)),
            ("--ndk-api", config.getdefault('app', 'android.minapi',
                                            self.android_minapi)),
        ]
        is_private_storage = config.getbooldefault(
            'app', 'android.private_storage', True)
        if is_private_storage:
            build_cmd += [("--private", self.buildozer.app_dir)]
        else:
            build_cmd += [("--dir", self.buildozer.app_dir)]

        # add permissions
        permissions = config.getlist('app', 'android.permissions', [])
        for permission in permissions:
            # force the latest component to be uppercase
            permission = permission.split('.')
            permission[-1] = permission[-1].upper()
            permission = '.'.join(permission)
            build_cmd += [("--permission", permission)]

        # android.entrypoint
        entrypoint = config.getdefault('app', 'android.entrypoint', 'org.kivy.android.PythonActivity')
        build_cmd += [('--android-entrypoint', entrypoint)]

        # android.apptheme
        apptheme = config.getdefault('app', 'android.apptheme', '@android:style/Theme.NoTitleBar')
        build_cmd += [('--android-apptheme', apptheme)]

        # android.compile_options
        compile_options = config.getlist('app', 'android.add_compile_options', [])
        for option in compile_options:
            build_cmd += [('--add-compile-option', option)]

        # android.add_gradle_repositories
        repos = config.getlist('app', 'android.add_gradle_repositories', [])
        for repo in repos:
            build_cmd += [('--add-gradle-repository', repo)]

        # android packaging options
        pkgoptions = config.getlist('app', 'android.add_packaging_options', [])
        for pkgoption in pkgoptions:
            build_cmd += [('--add-packaging-option', pkgoption)]

        # meta-data
        meta_datas = config.getlistvalues('app', 'android.meta_data', [])
        for meta in meta_datas:
            key, value = meta.split('=', 1)
            meta = '{}={}'.format(key.strip(), value.strip())
            build_cmd += [("--meta-data", meta)]

        # add extra Java jar files
        add_jars = config.getlist('app', 'android.add_jars', [])
        for pattern in add_jars:
            pattern = join(self.buildozer.root_dir, pattern)
            matches = glob(expanduser(pattern.strip()))
            if matches:
                for jar in matches:
                    build_cmd += [("--add-jar", jar)]
            else:
                raise SystemError('Failed to find jar file: {}'.format(
                    pattern))

        # add Java activity
        add_activities = config.getlist('app', 'android.add_activities', [])
        for activity in add_activities:
            build_cmd += [("--add-activity", activity)]

        # add presplash
        presplash = config.getdefault('app', 'presplash.filename', '')
        if presplash:
            build_cmd += [("--presplash", join(self.buildozer.root_dir,
                                               presplash))]

        # add icon
        icon = config.getdefault('app', 'icon.filename', '')
        if icon:
            build_cmd += [("--icon", join(self.buildozer.root_dir, icon))]

        # OUYA Console support
        ouya_category = config.getdefault('app', 'android.ouya.category',
                                          '').upper()
        if ouya_category:
            if ouya_category not in ('GAME', 'APP'):
                raise SystemError(
                    'Invalid android.ouya.category: "{}" must be one of GAME or APP'.format(
                        ouya_category))
            # add icon
            ouya_icon = config.getdefault('app', 'android.ouya.icon.filename',
                                          '')
            build_cmd += [("--ouya-category", ouya_category)]
            build_cmd += [("--ouya-icon", join(self.buildozer.root_dir,
                                               ouya_icon))]

        if config.getdefault('app', 'p4a.bootstrap', 'sdl2') != 'service_only':
            # add orientation
            orientation = config.getdefault('app', 'orientation', 'landscape')
            if orientation == 'all':
                orientation = 'sensor'
            build_cmd += [("--orientation", orientation)]

            # fullscreen ?
            fullscreen = config.getbooldefault('app', 'fullscreen', True)
            if not fullscreen:
                build_cmd += [("--window", )]

        # wakelock ?
        wakelock = config.getbooldefault('app', 'android.wakelock', False)
        if wakelock:
            build_cmd += [("--wakelock", )]

        # intent filters
        intent_filters = config.getdefault(
            'app', 'android.manifest.intent_filters', '')
        if intent_filters:
            build_cmd += [("--intent-filters", join(self.buildozer.root_dir,
                                                    intent_filters))]

        # activity launch mode
        launch_mode = config.getdefault(
            'app', 'android.manifest.launch_mode', '')
        if launch_mode:
            build_cmd += [("--activity-launch-mode", launch_mode)]

        # numeric version
        numeric_version = config.getdefault('app', 'android.numeric_version')
        if numeric_version:
            build_cmd += [("--numeric-version", numeric_version)]

        # build only in debug right now.
        if self.build_mode == 'debug':
            build_cmd += [("debug", )]
            mode = 'debug'
            mode_sign = mode
        else:
            build_cmd += [("release", )]
            mode_sign = "release"
            mode = self.get_release_mode()

        self.execute_build_package(build_cmd)

        try:
            self.buildozer.hook("android_pre_build_apk")
            self.execute_build_package(build_cmd)
            self.buildozer.hook("android_post_build_apk")
        except:
            # maybe the hook fail because the apk is not
            pass

        build_tools_versions = os.listdir(join(self.android_sdk_dir, "build-tools"))
        build_tools_versions = sorted(build_tools_versions, key=LooseVersion)
        build_tools_version = build_tools_versions[-1]
        gradle_files = ["build.gradle", "gradle", "gradlew"]
        is_gradle_build = build_tools_version >= "25.0" and any(
            (exists(join(dist_dir, x)) for x in gradle_files))
        packagename = config.get('app', 'package.name')

        if is_gradle_build:
            # on gradle build, the apk use the package name, and have no version
            packagename_src = basename(dist_dir)  # gradle specifically uses the folder name
            apk = u'{packagename}-{mode}.apk'.format(
                packagename=packagename_src, mode=mode)
            apk_dir = join(dist_dir, "build", "outputs", "apk", mode_sign)
        else:
            # on ant, the apk use the title, and have version
            bl = u'\'" ,'
            apptitle = config.get('app', 'title')
            if hasattr(apptitle, 'decode'):
                apptitle = apptitle.decode('utf-8')
            apktitle = ''.join([x for x in apptitle if x not in bl])
            apk = u'{title}-{version}-{mode}.apk'.format(
                title=apktitle,
                version=version,
                mode=mode)
            apk_dir = join(dist_dir, "bin")

        apk_dest = u'{packagename}-{version}-{arch}-{mode}.apk'.format(
            packagename=packagename, mode=mode, version=version,
            arch=self._arch)

        # copy to our place
        copyfile(join(apk_dir, apk), join(self.buildozer.bin_dir, apk_dest))

        self.buildozer.info('Android packaging done!')
        self.buildozer.info(
            u'APK {0} available in the bin directory'.format(apk_dest))
        self.buildozer.state['android:latestapk'] = apk_dest
        self.buildozer.state['android:latestmode'] = self.build_mode

    def _update_libraries_references(self, dist_dir):
        # ensure the project.properties exist
        project_fn = join(dist_dir, 'project.properties')

        if not self.buildozer.file_exists(project_fn):
            content = [
                'target=android-{}\n'.format(self.android_api),
                'APP_PLATFORM={}\n'.format(self.android_minapi)]
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
        source_dir = realpath(self.buildozer.config.getdefault(
            'app', 'source.dir', '.'))
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

            try:
                fd.writelines((line.decode('utf-8') for line in content))
            except:
                fd.writelines(content)
            if content and not content[-1].endswith(u'\n'):
                fd.write(u'\n')
            for index, ref in enumerate(references):
                fd.write(u'android.library.reference.{}={}\n'.format(index + 1, ref))

        self.buildozer.debug('project.properties updated')

    def _add_java_src(self, dist_dir):
        java_src = self.buildozer.config.getlist('app', 'android.add_src', [])

        gradle_files = ["build.gradle", "gradle", "gradlew"]
        is_gradle_build = any((
            exists(join(dist_dir, x)) for x in gradle_files))
        if is_gradle_build:
            src_dir = join(dist_dir, "src", "main", "java")
            self.buildozer.info(
                "Gradle project detected, copy files {}".format(src_dir))
        else:
            src_dir = join(dist_dir, 'src')
            self.buildozer.info(
                "Ant project detected, copy files in {}".format(src_dir))

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
        lines = self.buildozer.cmd('{} devices'.format(self.adb_cmd),
                               get_stdout=True)[0].splitlines()
        serials = []
        for serial in lines:
            if not serial:
                continue
            if serial.startswith('*') or serial.startswith('List '):
                continue
            serials.append(serial.split()[0])
        self._serials = serials
        return serials

    def cmd_adb(self, *args):
        '''
        Run adb from the Android SDK.
        Args must come after --, or use
        --alias to make an alias
        '''
        self.check_requirements()
        self.install_platform()
        args = args[0]
        if args and args[0] == '--alias':
            print('To set up ADB in this shell session, execute:')
            print('    alias adb=$(buildozer {} adb --alias 2>&1 >/dev/null)'
                  .format(self.targetname))
            sys.stderr.write(self.adb_cmd + '\n')
        else:
            self.buildozer.cmd(' '.join([self.adb_cmd] + args))

    def cmd_deploy(self, *args):
        super().cmd_deploy(*args)
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
            self.buildozer.cmd('{0} install -r "{1}"'.format(
                               self.adb_cmd, full_apk),
                               cwd=self.buildozer.global_platform_dir)
        self.buildozer.environ.pop('ANDROID_SERIAL', None)

        self.buildozer.info('Application pushed.')

    def cmd_logcat(self, *args):
        '''Show the log from the device
        '''
        self.check_requirements()
        serial = self.serials[0:]
        if not serial:
            return
        filters = self.buildozer.config.getrawdefault(
            "app", "android.logcat_filters", "", section_sep=":", split_char=" ")
        filters = " ".join(filters)
        self.buildozer.environ['ANDROID_SERIAL'] = serial[0]
        self.buildozer.cmd('{adb} logcat {filters}'.format(adb=self.adb_cmd,
                                                           filters=filters),
                           cwd=self.buildozer.global_platform_dir,
                           show_output=True)
        self.buildozer.environ.pop('ANDROID_SERIAL', None)


def get_target(buildozer):
    buildozer.targetname = "android"
    return TargetAndroid(buildozer)


def generate_dist_folder_name(base_dist_name, arch_names=None):
    """Generate the distribution folder name to use, based on a
    combination of the input arguments.

    WARNING: This function is copied from python-for-android. It would
    be preferable to have a proper interface, either importing the p4a
    code or having a p4a dist dir query option.

    Parameters
    ----------
    base_dist_name : str
        The core distribution identifier string
    arch_names : list of str
        The architecture compile targets

    """
    if arch_names is None:
        arch_names = ["no_arch_specified"]

    return '{}__{}'.format(
        base_dist_name,
        '_'.join(arch_names)
    )
