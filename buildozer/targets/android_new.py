# coding=utf-8
'''
Android target, based on python-for-android project (new toolchain)
'''

from buildozer.targets.android import TargetAndroid
from os.path import join, expanduser, realpath


class TargetAndroidNew(TargetAndroid):
    p4a_branch = "master"
    p4a_directory = "python-for-android-master"
    p4a_apk_cmd = "apk --bootstrap=sdl2"

    def __init__(self, buildozer):
        super(TargetAndroidNew, self).__init__(buildozer)
        self._build_dir = join(self.buildozer.platform_dir, 'build')
        self._p4a_cmd = ('python -m pythonforandroid.toolchain '
                         '--storage-dir={} ').format(self._build_dir)

    def _p4a(self, cmd, **kwargs):
        kwargs.setdefault('cwd', self.pa_dir)
        return self.buildozer.cmd(self._p4a_cmd + cmd, **kwargs)

    def get_available_packages(self):
        available_modules = self._p4a(
            "recipes --compact",
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
        available_modules = self._p4a(
            "create --dist_name={} --bootstrap={} --requirements={} --arch armeabi-v7a {}".format(
                 dist_name, "sdl2", requirements, " ".join(options)),
            get_stdout=True)[0]

    def _update_libraries_references(self, dist_dir):
        # UNSUPPORTED YET
        pass

    def get_dist_dir(self, dist_name):
        return join(self._build_dir, 'dists', dist_name)

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

        cmd = " ".join(cmd)
        self._p4a(cmd)

    def cmd_run(self, *args):
        entrypoint = self.buildozer.config.getdefault(
            'app', 'android.entrypoint')
        if not entrypoint:
            self.buildozer.config.set('app', 'android.entrypoint',  'org.kivy.android.PythonActivity')
        return super(TargetAndroidNew, self).cmd_run(*args)


def get_target(buildozer):
    buildozer.targetname = "android"
    return TargetAndroidNew(buildozer)
