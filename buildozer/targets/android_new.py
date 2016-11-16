# coding=utf-8
'''
Android target, based on python-for-android project (new toolchain)
'''
import sys

from buildozer.targets.android import TargetAndroid
from buildozer import USE_COLOR
from os.path import join, expanduser, realpath


class TargetAndroidNew(TargetAndroid):
    targetname = 'android_new'
    p4a_branch = "master"
    p4a_directory = "python-for-android-master"
    p4a_apk_cmd = "apk --bootstrap="
    extra_p4a_args = ''

    def __init__(self, buildozer):
        super(TargetAndroidNew, self).__init__(buildozer)
        self._build_dir = join(self.buildozer.platform_dir, 'build')
        self._p4a_cmd = ('python -m pythonforandroid.toolchain ')
        self._p4a_bootstrap = self.buildozer.config.getdefault(
            'app', 'android.bootstrap', 'sdl2')
        self.p4a_apk_cmd += self._p4a_bootstrap
        color = 'always' if USE_COLOR else 'never'
        self.extra_p4a_args = ' --color={} --storage-dir={}'.format(
            color, self._build_dir)

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
        onlyname = lambda x: x.split('==')[0]
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
        available_modules = self._p4a(
            "create --dist_name={} --bootstrap={} --requirements={} --arch armeabi-v7a {}".format(
                 dist_name, self._p4a_bootstrap, requirements, " ".join(options)),
            get_stdout=True)[0]

    def _update_libraries_references(self, dist_dir):
        # UNSUPPORTED YET
        pass

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
                continue
            if option == "--window":
                cmd.append("--window")
            elif option == "--sdk":
                cmd.append("--android_api")
                cmd.extend(values)
            else:
                cmd.extend(args)

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
        whitelist_src = self.buildozer.config.getdefault('app', 'android.p4a_whitelist_src', None)
        blacklist_src = self.buildozer.config.getdefault('app', 'android.p4a_blacklist_src', None)
        if whitelist_src:
            cmd.append('--whitelist')
            cmd.append(realpath(whitelist_src))
        if blacklist_src:
            cmd.append('--blacklist')
            cmd.append(realpath(blacklist_src))

        cmd = " ".join(cmd)
        self._p4a(cmd)

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
