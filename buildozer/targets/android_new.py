# coding=utf-8
'''
Android target, based on python-for-android project
'''

import sys
import os

from buildozer import USE_COLOR
from buildozer.targets.android import TargetAndroid
from os.path import join, expanduser, realpath


class TargetAndroidNew(TargetAndroid):
    targetname = 'android'
    p4a_branch = "stable"
    p4a_directory = "python-for-android-new-toolchain"
    p4a_apk_cmd = "apk --debug --bootstrap="
    extra_p4a_args = ''

    def __init__(self, *args, **kwargs):
        super(TargetAndroidNew, self).__init__(*args, **kwargs)
        self._build_dir = join(self.buildozer.platform_dir, 'build')
        executable = sys.executable or 'python'
        self._p4a_cmd = '{} -m pythonforandroid.toolchain '.format(executable)
        self._p4a_bootstrap = self.buildozer.config.getdefault(
            'app', 'p4a.bootstrap', 'sdl2')
        self.p4a_apk_cmd += self._p4a_bootstrap
        color = 'always' if USE_COLOR else 'never'
        self.extra_p4a_args = ' --color={} --storage-dir="{}"'.format(
            color, self._build_dir)
        ndk_api = self.buildozer.config.getdefault('app', 'android.ndk_api', None)
        if ndk_api is not None:
            self.extra_p4a_args += ' --ndk-api={}'.format(ndk_api)
        hook = self.buildozer.config.getdefault("app", "p4a.hook", None)
        if hook is not None:
            self.extra_p4a_args += ' --hook={}'.format(realpath(hook))
        port = self.buildozer.config.getdefault('app', 'p4a.port', None)
        if port is not None:
            self.extra_p4a_args += ' --port={}'.format(port)

    def _p4a(self, cmd, **kwargs):
        if not hasattr(self, "pa_dir"):
            self.pa_dir = join(self.buildozer.platform_dir, self.p4a_directory)
        kwargs.setdefault('cwd', self.pa_dir)
        return self.buildozer.cmd(self._p4a_cmd + cmd + self.extra_p4a_args, **kwargs)

    def get_available_packages(self):
        return True

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
        config = self.buildozer.config
        self._p4a(
            ("create --dist_name={} --bootstrap={} --requirements={} "
             "--ndk-api {} "
             "--arch {} {}").format(
                 dist_name, self._p4a_bootstrap, requirements,
                 config.getdefault('app', 'android.minapi', self.android_minapi),
                 config.getdefault('app', 'android.arch', "armeabi-v7a"), " ".join(options)),
            get_stdout=True)[0]

    def get_dist_dir(self, dist_name):
        return join(self._build_dir, 'dists', dist_name)

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

        # support for gradle dependencies
        gradle_dependencies = self.buildozer.config.getlist('app', 'android.gradle_dependencies', [])
        for gradle_dependency in gradle_dependencies:
            cmd.append('--depend')
            cmd.append(gradle_dependency)

        cmd.append('--arch')
        cmd.append(self.buildozer.config.getdefault('app', 'android.arch', "armeabi-v7a"))

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
            self.buildozer.config.set('app', 'android.entrypoint',  'org.kivy.android.PythonActivity')
        return super(TargetAndroidNew, self).cmd_run(*args)

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
            sys.stderr.write('PYTHONPATH={} {}\n'.format(self.pa_dir, self._p4a_cmd))
        else:
            self._p4a(' '.join(args) if args else '')

    def cmd_clean(self, *args):
        '''
        Clean the build and distribution
        '''
        self._p4a("clean_builds")
        self._p4a("clean_dists")


def get_target(buildozer):
    buildozer.targetname = "android"
    return TargetAndroidNew(buildozer)
