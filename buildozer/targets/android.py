'''
Android target, based on python-for-android project (old toolchain)
'''
#
# Android target
# Thanks for Renpy (again) for its install_sdk.py and plat.py in the PGS4A
# project!
#

import sys
if sys.platform == 'win32':
    raise NotImplementedError('Windows platform not yet working for Android')

from platform import uname
WSL = 'Microsoft' in uname()[2]

ANDROID_API = '19'
ANDROID_MINAPI = '9'
ANDROID_SDK_VERSION = '20'
ANDROID_NDK_VERSION = '9c'
APACHE_ANT_VERSION = '1.9.4'

import traceback
import os
import io
import re
import ast
import sh
from pipes import quote
from sys import platform, executable
from buildozer import BuildozerException
from buildozer import IS_PY3
from buildozer.target import Target
from os import environ
from os.path import exists, join, realpath, expanduser, basename, relpath
from platform import architecture
from shutil import copyfile
from glob import glob

from buildozer.libs.version import parse
from distutils.version import LooseVersion


class TargetAndroid(Target):
    targetname = 'android_old'
    p4a_directory = "python-for-android"
    p4a_branch = 'old_toolchain'
    p4a_apk_cmd = "python build.py"

    @property
    def android_sdk_version(self):
        return self.buildozer.config.getdefault('app', 'android.sdk',
                                                ANDROID_SDK_VERSION)

    @property
    def android_ndk_version(self):
        return self.buildozer.config.getdefault('app', 'android.ndk',
                                                ANDROID_NDK_VERSION)

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
        version = self.buildozer.config.getdefault('app', 'android.sdk',
                                                   self.android_sdk_version)
        return join(self.buildozer.global_platform_dir,
                    'android-sdk-{0}'.format(version))

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
                jdk, "CurrentVersion")  #@UndefinedVariable
            with _winreg.OpenKey(jdk,
                                 current_version) as cv:  #@UndefinedVariable
                java_home, _type = _winreg.QueryValueEx(
                    cv, "JavaHome")  #@UndefinedVariable
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
        self.buildozer.download(url,
                                archive,
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
        self.buildozer.download(url,
                                archive,
                                cwd=self.buildozer.global_platform_dir)

        self.buildozer.info('Unpacking Android SDK')
        self.buildozer.file_extract(archive,
                                    cwd=self.buildozer.global_platform_dir)
        self.buildozer.file_rename(unpacked,
                                   sdk_dir,
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
            raise SystemError('Unsupported platform: {0}'.format(platform))

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
        return [x.split('"')[1]
                for x in available_packages.splitlines()
                if x.startswith('id: ')]

    def _android_update_sdk(self, packages):
        from pexpect import EOF
        java_tool_options = environ.get('JAVA_TOOL_OPTIONS', '')
        child = self.buildozer.cmd_expect(
            '{} update sdk -u -a -t {}'.format(
                self.android_cmd,
                packages,
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

        # 3 pass installation.
        if not os.access(self.android_cmd, os.X_OK):
            self.buildozer.cmd('chmod ug+x {}'.format(self.android_cmd))

        # 1. update the tool and platform-tools if needed
        packages = self._android_list_sdk()
        skip_upd = self.buildozer.config.getdefault('app',
                                                    'android.skip_update', False)
        if 'tools' in packages or 'platform-tools' in packages:
            if not skip_upd:
                if WSL:
                    # WSL (Windows Subsystem for Linux) allows running
                    # linux from windows 10, but some windows
                    # limitations still apply, namely you can't rename a
                    # directory that a program was started from, which
                    # is what the tools updates cause, and we end up
                    # with an empty dir, so we need to run from a
                    # different place, and the updater is still looking
                    # for things in tools, and specifically renames the
                    # tool dir, hence, moving and making a symlink
                    # works.
                    sh.mv(
                        join(self.android_sdk_dir, 'tools'),
                        join(self.android_sdk_dir, 'tools.save')
                    )
                    sh.ln(
                        '-s',
                        join(self.android_sdk_dir, 'tools.save'),
                        join(self.android_sdk_dir, 'tools')
                    )
                    old_android_cmd = self.android_cmd
                    self.android_cmd = join(
                        self.android_sdk_dir,
                        'tools.save',
                        self.android_cmd.split('/')[-1]
                    )

                self._android_update_sdk('tools,platform-tools')

                if WSL:
                    self.android_cmd = old_android_cmd
                    sh.rm('-rf', join(self.android_sdk_dir, 'tools.save'))
            else:
                self.buildozer.info('Skipping Android SDK update due to spec file setting')

        # 2. install the latest build tool
        v_build_tools = self._read_version_subdir(self.android_sdk_dir,
                                                  'build-tools')
        packages = self._android_list_sdk(include_all=True)
        ver = self._find_latest_package(packages, 'build-tools-')
        if ver and ver > v_build_tools and not skip_upd:
            self._android_update_sdk(self._build_package_string('build-tools', ver))
        # 2. check aidl can be run
        self._check_aidl(v_build_tools)

        # 3. finally, install the android for the current api
        android_platform = join(self.android_sdk_dir, 'platforms', 'android-{0}'.format(self.android_api))
        if not self.buildozer.file_exists(android_platform):
            packages = self._android_list_sdk()
            android_package = 'android-{}'.format(self.android_api)
            if android_package in packages and not skip_upd:
                self._android_update_sdk(android_package)

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
            'ANDROIDNDKVER': 'r{}'.format(self.android_ndk_version)
        })

    def _install_p4a(self):
        cmd = self.buildozer.cmd
        source = self.buildozer.config.getdefault('app', 'p4a.branch',
                                                  self.p4a_branch)
        self.pa_dir = pa_dir = join(self.buildozer.platform_dir,
                                    self.p4a_directory)
        system_p4a_dir = self.buildozer.config.getdefault('app',
                                                          'p4a.source_dir')
        if system_p4a_dir:
            self.pa_dir = pa_dir = expanduser(system_p4a_dir)
            if not self.buildozer.file_exists(pa_dir):
                self.buildozer.error(
                    'Path for p4a.source_dir does not exist')
                self.buildozer.error('')
                raise BuildozerException()
        else:
            if not self.buildozer.file_exists(pa_dir):
                cmd(
                    ('git clone -b {} --single-branch '
                     'https://github.com/kivy/python-for-android.git '
                     '{}').format(source, self.p4a_directory),
                    cwd=self.buildozer.platform_dir)
            elif self.platform_update:
                cmd('git clean -dxf', cwd=pa_dir)
                current_branch = cmd('git rev-parse --abbrev-ref HEAD',
                                     get_stdout=True, cwd=pa_dir)[0].strip()
                if current_branch == source:
                    cmd('git pull', cwd=pa_dir)
                else:
                    cmd('git fetch --tags origin {0}:{0}'.format(source),
                        cwd=pa_dir)
                    cmd('git checkout {}'.format(source), cwd=pa_dir)

        # also install dependencies (currently, only setup.py knows about it)
        # let's extract them.
        try:
            with open(join(self.pa_dir, "setup.py")) as fd:
                setup = fd.read()
                deps = re.findall("^\s*install_reqs = (\[[^\]]*\])", setup, re.DOTALL | re.MULTILINE)[0]
                deps = ast.literal_eval(deps)
        except IOError:
            self.buildozer.error('Failed to read python-for-android setup.py at {}'.format(
                join(self.pa_dir, 'setup.py')))
            exit(1)
        pip_deps = []
        for dep in deps:
            pip_deps.append("'{}'".format(dep))

        # in virtualenv or conda env
        options = "--user"
        if "VIRTUAL_ENV" in os.environ or "CONDA_PREFIX" in os.environ:
            options = ""
        cmd('{} -m pip install -q {} {}'.format(executable, options, " ".join(pip_deps)))

    def get_available_packages(self):
        available_modules = self.buildozer.cmd('./distribute.sh -l',
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
        android_requirements = [x
                                for x in app_requirements
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
            'app', 'android.whitelist') or []
        whitelist_fn = join(dist_dir, 'whitelist.txt')
        with open(whitelist_fn, 'w') as fd:
            for wl in p4a_whitelist:
                fd.write(wl + '\n')

    def get_dist_dir(self, dist_name):
        return join(self.pa_dir, 'dist', dist_name)

    @property
    def dist_dir(self):
        dist_name = self.buildozer.config.get('app', 'package.name')
        return self.get_dist_dir(dist_name)

    def execute_build_package(self, build_cmd):
        dist_name = self.buildozer.config.get('app', 'package.name')
        cmd = [self.p4a_apk_cmd]
        for args in build_cmd:
            cmd.append(" ".join(args))
        cmd = " ".join(cmd)
        self.buildozer.cmd(cmd, cwd=self.get_dist_dir(dist_name))

    def build_package(self):
        dist_name = self.buildozer.config.get('app', 'package.name')
        dist_dir = self.get_dist_dir(dist_name)
        config = self.buildozer.config
        package = self._get_package()
        version = self.buildozer.get_version()

        # add extra libs/armeabi files in dist/default/libs/armeabi
        # (same for armeabi-v7a, x86, mips)
        for config_key, lib_dir in (
            ('android.add_libs_armeabi', 'armeabi'),
            ('android.add_libs_armeabi_v7a', 'armeabi-v7a'),
            ('android.add_libs_x86', 'x86'),
            ('android.add_libs_mips', 'mips')):

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
        build_cmd = [
            ("--name", quote(config.get('app', 'title'))),
            ("--version", version),
            ("--package", package),
            ("--sdk", config.getdefault('app', 'android.api',
                                        self.android_api)),
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

        # build only in debug right now.
        if self.build_mode == 'debug':
            build_cmd += [("debug", )]
            mode = 'debug'
        else:
            build_cmd += [("release", )]
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

        if is_gradle_build:
            # on gradle build, the apk use the package name, and have no version
            packagename = config.get('app', 'package.name')
            apk = u'{packagename}-{mode}.apk'.format(
                packagename=packagename, mode=mode)
            apk_dir = join(dist_dir, "build", "outputs", "apk", mode)
            apk_dest = u'{packagename}-{version}-{mode}.apk'.format(
                packagename=packagename, mode=mode, version=version)

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
            apk_dest = apk

        # copy to our place
        copyfile(join(apk_dir, apk), join(self.buildozer.bin_dir, apk_dest))

        self.buildozer.info('Android packaging done!')
        self.buildozer.info(
            u'APK {0} available in the bin directory'.format(apk_dest))
        self.buildozer.state['android:latestapk'] = apk_dest
        self.buildozer.state['android:latestmode'] = self.build_mode

    def get_release_mode(self):
        return "release-unsigned"

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
            self.buildozer.cmd('{0} install -r "{1}"'.format(
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
    return TargetAndroid(buildozer)
