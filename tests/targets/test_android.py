import os
import tempfile
from unittest import mock

import pytest

import buildozer as buildozer_module
from buildozer import Buildozer
from buildozer.targets.android import TargetAndroid


def patch_buildozer(method):
    return mock.patch("buildozer.Buildozer.{method}".format(method=method))


def patch_buildozer_cmd():
    return patch_buildozer("cmd")


def patch_buildozer_cmd_expect():
    return patch_buildozer("cmd_expect")


def patch_buildozer_file_exists():
    return patch_buildozer("file_exists")


def patch_buildozer_download():
    return patch_buildozer("download")


def patch_buildozer_file_extract():
    return patch_buildozer("file_extract")


def patch_os_isfile():
    return mock.patch("os.path.isfile")


def patch_buildozer_checkbin():
    return patch_buildozer("checkbin")


def patch_target_android(method):
    return mock.patch(
        "buildozer.targets.android.TargetAndroid.{method}".format(method=method)
    )


def patch_platform(platform):
    return mock.patch("buildozer.targets.android.platform", platform)


class TestTargetAndroid:

    @staticmethod
    def default_specfile_path():
        return os.path.join(os.path.dirname(buildozer_module.__file__), "default.spec")

    def setup_method(self):
        """
        Create a temporary directory that will contain the spec file and will
        serve as the root_dir.
        """
        self.temp_dir = tempfile.TemporaryDirectory()

    def tear_method(self):
        """
        Remove the temporary directory created in self.setup_method.
        """
        self.temp_dir.cleanup()

    def init_target(self, options=None):
        """
        Create a buildozer.spec file in the temporary directory and init the
        Buildozer and TargetAndroid instances.

        The optional argument can be used to overwrite the config options in
        the buildozer.spec file, e.g.:

            self.init_target({'title': 'Test App'})

        will replace line 4 of the default spec file.
        """
        if options is None:
            options = {}

        spec_path = os.path.join(self.temp_dir.name, 'buildozer.spec')

        with open(TestTargetAndroid.default_specfile_path()) as f:
            default_spec = f.readlines()

        spec = []
        for line in default_spec:
            if line.strip():
                key = line.split()[0]

                if key.startswith('#'):
                    key = key[1:]

                if key in options:
                    line = '{} = {}\n'.format(key, options[key])

            spec.append(line)

        with open(spec_path, 'w') as f:
            f.writelines(spec)

        self.buildozer = Buildozer(filename=spec_path, target='android')
        self.target_android = TargetAndroid(self.buildozer)

    def call_build_package(self):
        """
        Call the build_package() method of the tested TargetAndroid instance,
        patching the functions that would otherwise produce side-effects.

        Return the mocked execute_build_package() method of the TargetAndroid
        instance so that tests can easily check which command-line arguments
        would be passed on to python-for-android's toolchain.
        """
        expected_dist_dir = (
            '{buildozer_dir}/android/platform/build-armeabi-v7a/dists/myapp__armeabi-v7a'.format(
            buildozer_dir=self.buildozer.buildozer_dir)
        )

        with patch_target_android(
            '_update_libraries_references'
        ) as m_update_libraries_references, patch_target_android(
            '_generate_whitelist'
        ) as m_generate_whitelist, mock.patch(
            'buildozer.targets.android.TargetAndroid.execute_build_package'
        ) as m_execute_build_package, mock.patch(
            'buildozer.targets.android.copyfile'
        ) as m_copyfile, mock.patch(
            'buildozer.targets.android.os.listdir'
        ) as m_listdir:
            m_listdir.return_value = ['30.0.0-rc2']
            self.target_android.build_package()

        assert m_listdir.call_count == 1
        assert m_update_libraries_references.call_args_list == [
            mock.call(expected_dist_dir)
        ]
        assert m_generate_whitelist.call_args_list == [mock.call(expected_dist_dir)]
        assert m_copyfile.call_args_list == [
            mock.call(
                '{expected_dist_dir}/bin/MyApplication-0.1-debug.apk'.format(
                    expected_dist_dir=expected_dist_dir
                ),
                '{bin_dir}/myapp-0.1-armeabi-v7a-debug.apk'.format(bin_dir=self.buildozer.bin_dir),
            )
        ]

        return m_execute_build_package

    def test_init(self):
        """Tests init defaults."""
        self.init_target()
        assert self.target_android._arch == "armeabi-v7a"
        assert self.target_android._build_dir.endswith(
            ".buildozer/android/platform/build-armeabi-v7a"
        )
        assert self.target_android._p4a_bootstrap == "sdl2"
        assert self.target_android._p4a_cmd.endswith(
            "python -m pythonforandroid.toolchain "
        )
        assert self.target_android.build_mode == "debug"
        assert self.target_android.buildozer == self.buildozer
        assert (
            self.target_android.extra_p4a_args == (
                ' --color=always'
                ' --storage-dir="{buildozer_dir}/android/platform/build-armeabi-v7a" --ndk-api=21'.format(
                buildozer_dir=self.buildozer.buildozer_dir)
            )
        )
        assert self.target_android.p4a_apk_cmd == "apk --debug --bootstrap=sdl2"
        assert self.target_android.platform_update is False

    def test_init_positional_buildozer(self):
        """Positional `buildozer` argument is required."""
        with pytest.raises(TypeError) as ex_info:
            TargetAndroid()
        assert ex_info.value.args == (
            "__init__() missing 1 required positional argument: 'buildozer'",
        )

    def test_sdkmanager(self):
        """Tests the _sdkmanager() method."""
        self.init_target()
        kwargs = {}
        with patch_buildozer_cmd() as m_cmd, patch_buildozer_cmd_expect() as m_cmd_expect, patch_os_isfile() as m_isfile:
            m_isfile.return_value = True
            assert m_cmd.return_value == self.target_android._sdkmanager(**kwargs)
        assert m_cmd.call_count == 1
        assert m_cmd_expect.call_count == 0
        assert m_isfile.call_count == 1
        kwargs = {"return_child": True}
        with patch_buildozer_cmd() as m_cmd, patch_buildozer_cmd_expect() as m_cmd_expect, patch_os_isfile() as m_isfile:
            m_isfile.return_value = True
            assert m_cmd_expect.return_value == self.target_android._sdkmanager(
                **kwargs
            )
        assert m_cmd.call_count == 0
        assert m_cmd_expect.call_count == 1
        assert m_isfile.call_count == 1

    def test_check_requirements(self):
        """Basic tests for the check_requirements() method."""
        self.init_target()
        assert not hasattr(self.target_android, "adb_cmd")
        assert not hasattr(self.target_android, "javac_cmd")
        assert "PATH" not in self.buildozer.environ
        with patch_buildozer_checkbin() as m_checkbin:
            self.target_android.check_requirements()
        assert m_checkbin.call_args_list == [
            mock.call("Git (git)", "git"),
            mock.call("Cython (cython)", "cython"),
            mock.call("Java compiler (javac)", "javac"),
            mock.call("Java keytool (keytool)", "keytool"),
        ]
        assert self.target_android.adb_cmd.endswith(
            ".buildozer/android/platform/android-sdk/platform-tools/adb"
        )
        assert self.target_android.javac_cmd == "javac"
        assert self.target_android.keytool_cmd == "keytool"
        assert "PATH" in self.buildozer.environ

    def test_check_configuration_tokens(self):
        """Basic tests for the check_configuration_tokens() method."""
        self.init_target()
        with mock.patch(
            "buildozer.targets.android.Target.check_configuration_tokens"
        ) as m_check_configuration_tokens:
            self.target_android.check_configuration_tokens()
        assert m_check_configuration_tokens.call_args_list == [mock.call([])]

    @pytest.mark.parametrize("platform", ["linux", "darwin"])
    def test_install_android_sdk(self, platform):
        """Basic tests for the _install_android_sdk() method."""
        self.init_target()
        with patch_buildozer_file_exists() as m_file_exists, patch_buildozer_download() as m_download:
            m_file_exists.return_value = True
            sdk_dir = self.target_android._install_android_sdk()
        assert m_file_exists.call_args_list == [
            mock.call(self.target_android.android_sdk_dir)
        ]
        assert m_download.call_args_list == []
        assert sdk_dir.endswith(".buildozer/android/platform/android-sdk")
        with patch_buildozer_file_exists() as m_file_exists, \
                patch_buildozer_download() as m_download, \
                patch_buildozer_file_extract() as m_file_extract, \
                patch_platform(platform):
            m_file_exists.return_value = False
            sdk_dir = self.target_android._install_android_sdk()
        assert m_file_exists.call_args_list == [
            mock.call(self.target_android.android_sdk_dir)
        ]
        archive = "sdk-tools-{platform}-4333796.zip".format(platform=platform)
        assert m_download.call_args_list == [
            mock.call(
                "http://dl.google.com/android/repository/",
                archive,
                cwd=mock.ANY,
            )
        ]
        assert m_file_extract.call_args_list == [mock.call(archive, cwd=mock.ANY)]
        assert sdk_dir.endswith(".buildozer/android/platform/android-sdk")

    def test_build_package(self):
        """Basic tests for the build_package() method."""
        self.init_target()
        m_execute_build_package = self.call_build_package()
        assert m_execute_build_package.call_args_list == [
            mock.call(
                [
                    ("--name", "'My Application'"),
                    ("--version", "0.1"),
                    ("--package", "org.test.myapp"),
                    ("--minsdk", "21"),
                    ("--ndk-api", "21"),
                    ("--private", "{buildozer_dir}/android/app".format(buildozer_dir=self.buildozer.buildozer_dir)),
                    ("--android-entrypoint", "org.kivy.android.PythonActivity"),
                    ("--android-apptheme", "@android:style/Theme.NoTitleBar"),
                    ("--orientation", "portrait"),
                    ("--window",),
                    ("debug",),
                ]
            )
        ]

    def test_build_package_intent_filters(self):
        """
        The build_package() method should honour the manifest.intent_filters
        config option.
        """
        filters_path = os.path.join(self.temp_dir.name, 'filters.xml')

        with open(filters_path, 'w') as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>')

        self.init_target({
            'android.manifest.intent_filters': 'filters.xml'
        })

        m_execute_build_package = self.call_build_package()

        assert m_execute_build_package.call_args_list == [
            mock.call(
                [
                    ('--name', "'My Application'"),
                    ('--version', '0.1'),
                    ('--package', 'org.test.myapp'),
                    ('--minsdk', '21'),
                    ('--ndk-api', '21'),
                    ('--private', '{buildozer_dir}/android/app'.format(buildozer_dir=self.buildozer.buildozer_dir)),
                    ('--android-entrypoint', 'org.kivy.android.PythonActivity'),
                    ('--android-apptheme', '@android:style/Theme.NoTitleBar'),
                    ('--orientation', 'portrait'),
                    ('--window',),
                    ('--intent-filters', os.path.realpath(filters_path)),
                    ('debug',),
                ]
            )
        ]
