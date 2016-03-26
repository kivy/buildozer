# coding=utf-8
'''
Android target, based on python-for-android project (new toolchain)
'''

from buildozer.targets.android import TargetAndroid
from os.path import join, expanduser


class TargetAndroidNew(TargetAndroid):
    p4a_branch = "master"
    p4a_directory = "python-for-android-master"
    p4a_apk_cmd = "python -m pythonforandroid.toolchain apk --bootstrap=sdl2"

    def get_available_packages(self):
        available_modules = self.buildozer.cmd(
            "python -m pythonforandroid.toolchain recipes --compact",
            cwd=self.pa_dir,
            get_stdout=True)[0]
        return available_modules.splitlines()[0].split()

    def compile_platform(self):
        app_requirements = self.buildozer.config.getlist(
            'app', 'requirements', '')
        available_modules = self.get_available_packages()
        onlyname = lambda x: x.split('==')[0]
        android_requirements = [x for x in app_requirements
                                if onlyname(x) in available_modules]
        dist_name = self.buildozer.config.get('app', 'package.name')
        requirements = ','.join(android_requirements)
        options = []
        if self.buildozer.config.getbooldefault('app', 'android.copy_libs', True):
            options.append("--copy-libs")
        available_modules = self.buildozer.cmd(
            ("python -m pythonforandroid.toolchain "
             "create --dist_name={} --bootstrap={} --requirements={} --arch armeabi-v7a {}").format(
                 dist_name, "sdl2", requirements, " ".join(options)),
            cwd=self.pa_dir,
            get_stdout=True)[0]

    def _update_libraries_references(self, dist_dir):
        # UNSUPPORTED YET
        pass

    def get_dist_dir(self, dist_name):
        return expanduser(join("~", ".local", "share", "python-for-android",
                               'dists', dist_name))

    def execute_build_package(self, build_cmd):
        # wrapper from previous old_toolchain to new toolchain
        dist_name = self.buildozer.config.get('app', 'package.name')
        cmd = [self.p4a_apk_cmd, "--dist_name", dist_name]
        for args in build_cmd:
            option, values = args[0], args[1:]
            if option == "debug":
                continue
            elif option == "release":
                cmd.append("--release")
                continue
            if option in ("--window", ):
                # missing option in sdl2 bootstrap yet
                continue
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

        cmd = " ".join(cmd)
        self.buildozer.cmd(cmd, cwd=self.pa_dir)

    def cmd_run(self, *args):
        entrypoint = self.buildozer.config.getdefault(
            'app', 'android.entrypoint')
        if not entrypoint:
            self.buildozer.config.set('app', 'android.entrypoint',  'org.kivy.android.PythonActivity')
        return super(TargetAndroidNew, self).cmd_run(*args)


def get_target(buildozer):
    buildozer.targetname = "android"
    return TargetAndroidNew(buildozer)
