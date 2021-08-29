import os
import tempfile
from six import StringIO
from unittest import mock

import pytest

from buildozer.targets.android import TargetAndroid
from tests.targets.utils import (
    init_buildozer,
    patch_buildozer,
    patch_buildozer_checkbin,
    patch_buildozer_cmd,
    patch_buildozer_file_exists,
)


def patch_buildozer_cmd_expect():
    return patch_buildozer("cmd_expect")


def patch_buildozer_download():
    return patch_buildozer("download")


def patch_buildozer_file_extract():
    return patch_buildozer("file_extract")


def patch_os_isfile():
    return mock.patch("os.path.isfile")


def patch_target_android(method):
    return mock.patch(
        "buildozer.targets.android.TargetAndroid.{method}".format(method=method)
    )


def patch_platform(platform):
    return mock.patch("buildozer.targets.android.platform", platform)


def init_target(temp_dir, options=None):
    buildozer = init_buildozer(temp_dir, "android", options)
    return TargetAndroid(buildozer)


def call_build_package(target_android):
    """
    Call the build_package() method of the tested TargetAndroid instance,
    patching the functions that would otherwise produce side-effects.

    Return the mocked execute_build_package() method of the TargetAndroid
    instance so that tests can easily check which command-line arguments
    would be passed on to python-for-android's toolchain.
    """
    buildozer = target_android.buildozer
    expected_dist_dir = (
        '{buildozer_dir}/android/platform/build-arm64-v8a_armeabi-v7a/dists/myapp'.format(
        buildozer_dir=buildozer.buildozer_dir)
    )

    with patch_target_android('_update_libraries_references') as m_update_libraries_references, \
         patch_target_android('_generate_whitelist') as m_generate_whitelist, \
         mock.patch('buildozer.targets.android.TargetAndroid.execute_build_package') as m_execute_build_package, \
         mock.patch('buildozer.targets.android.copyfile') as m_copyfile, \
         mock.patch('buildozer.targets.android.os.listdir') as m_listdir:
        m_listdir.return_value = ['30.0.0-rc2']
        target_android.build_package()

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
            '{bin_dir}/myapp-0.1-arm64-v8a_armeabi-v7a-debug.apk'.format(bin_dir=buildozer.bin_dir),
        )
    ]
    return m_execute_build_package


class TestTargetAndroid:

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

    def test_init(self):
        """Tests init defaults."""
        target_android = init_target(self.temp_dir)
        buildozer = target_android.buildozer
        assert target_android._archs == ["arm64-v8a", "armeabi-v7a"]
        assert target_android._build_dir.endswith(
            ".buildozer/android/platform/build-arm64-v8a_armeabi-v7a"
        )
        assert target_android._p4a_bootstrap == "sdl2"
        assert target_android._p4a_cmd.endswith(
            "python -m pythonforandroid.toolchain "
        )
        assert target_android.build_mode == "debug"
        assert (
            target_android.extra_p4a_args == (
                ' --color=always'
                ' --storage-dir="{buildozer_dir}/android/platform/build-arm64-v8a_armeabi-v7a" --ndk-api=21 --ignore-setup-py --debug'.format(
                buildozer_dir=buildozer.buildozer_dir)
            )
        )
        assert target_android.platform_update is False

    def test_init_positional_buildozer(self):
        """Positional `buildozer` argument is required."""
        with pytest.raises(TypeError) as ex_info:
            TargetAndroid()
        assert ex_info.value.args == (
            "__init__() missing 1 required positional argument: 'buildozer'",
        )

    def test_sdkmanager(self):
        """Tests the _sdkmanager() method."""
        target_android = init_target(self.temp_dir)
        kwargs = {}
        with patch_buildozer_cmd() as m_cmd, patch_buildozer_cmd_expect() as m_cmd_expect, patch_os_isfile() as m_isfile:
            m_isfile.return_value = True
            assert m_cmd.return_value == target_android._sdkmanager(**kwargs)
        assert m_cmd.call_count == 1
        assert m_cmd_expect.call_count == 0
        assert m_isfile.call_count == 1
        kwargs = {"return_child": True}
        with patch_buildozer_cmd() as m_cmd, patch_buildozer_cmd_expect() as m_cmd_expect, patch_os_isfile() as m_isfile:
            m_isfile.return_value = True
            assert m_cmd_expect.return_value == target_android._sdkmanager(
                **kwargs
            )
        assert m_cmd.call_count == 0
        assert m_cmd_expect.call_count == 1
        assert m_isfile.call_count == 1

    def test_check_requirements(self):
        """Basic tests for the check_requirements() method."""
        target_android = init_target(self.temp_dir)
        buildozer = target_android.buildozer
        assert not hasattr(target_android, "adb_cmd")
        assert not hasattr(target_android, "javac_cmd")
        assert "PATH" not in buildozer.environ
        with patch_buildozer_checkbin() as m_checkbin:
            target_android.check_requirements()
        assert m_checkbin.call_args_list == [
            mock.call("Git (git)", "git"),
            mock.call("Cython (cython)", "cython"),
            mock.call("Java compiler (javac)", "javac"),
            mock.call("Java keytool (keytool)", "keytool"),
        ]
        assert target_android.adb_cmd.endswith(
            ".buildozer/android/platform/android-sdk/platform-tools/adb"
        )
        assert target_android.javac_cmd == "javac"
        assert target_android.keytool_cmd == "keytool"
        assert "PATH" in buildozer.environ

    def test_check_configuration_tokens(self):
        """Basic tests for the check_configuration_tokens() method."""
        target_android = init_target(self.temp_dir)
        with mock.patch(
            "buildozer.targets.android.Target.check_configuration_tokens"
        ) as m_check_configuration_tokens:
            target_android.check_configuration_tokens()
        assert m_check_configuration_tokens.call_args_list == [mock.call([])]

    @pytest.mark.parametrize("platform", ["linux", "darwin"])
    def test_install_android_sdk(self, platform):
        """Basic tests for the _install_android_sdk() method."""
        target_android = init_target(self.temp_dir)
        with patch_buildozer_file_exists() as m_file_exists, patch_buildozer_download() as m_download:
            m_file_exists.return_value = True
            sdk_dir = target_android._install_android_sdk()
        assert m_file_exists.call_args_list == [
            mock.call(target_android.android_sdk_dir)
        ]
        assert m_download.call_args_list == []
        assert sdk_dir.endswith(".buildozer/android/platform/android-sdk")
        with patch_buildozer_file_exists() as m_file_exists, \
                patch_buildozer_download() as m_download, \
                patch_buildozer_file_extract() as m_file_extract, \
                patch_platform(platform):
            m_file_exists.return_value = False
            sdk_dir = target_android._install_android_sdk()
        assert m_file_exists.call_args_list == [
            mock.call(target_android.android_sdk_dir)
        ]
        platform_map = {"linux": "linux", "darwin": "mac"}
        platform = platform_map[platform]
        archive = "commandlinetools-{platform}-6514223_latest.zip".format(platform=platform)
        assert m_download.call_args_list == [
            mock.call(
                "https://dl.google.com/android/repository/",
                archive,
                cwd=mock.ANY,
            )
        ]
        assert m_file_extract.call_args_list == [mock.call(archive, cwd=mock.ANY)]
        assert sdk_dir.endswith(".buildozer/android/platform/android-sdk")

    def test_build_package(self):
        """Basic tests for the build_package() method."""
        target_android = init_target(self.temp_dir)
        buildozer = target_android.buildozer
        m_execute_build_package = call_build_package(target_android)
        assert m_execute_build_package.call_args_list == [
            mock.call(
                [
                    ("--name", "'My Application'"),
                    ("--version", "0.1"),
                    ("--package", "org.test.myapp"),
                    ("--minsdk", "21"),
                    ("--ndk-api", "21"),
                    ("--private", "{buildozer_dir}/android/app".format(buildozer_dir=buildozer.buildozer_dir)),
                    ("--android-entrypoint", "org.kivy.android.PythonActivity"),
                    ("--android-apptheme", "@android:style/Theme.NoTitleBar"),
                    ("--orientation", "portrait"),
                    ("--window",),
                    ("debug",),
                ]
            )
        ]

    def test_numeric_version(self):
        """The `android.numeric_version` config should be passed to `build_package()`."""
        target_android = init_target(self.temp_dir, {
            "android.numeric_version": "1234"
        })
        buildozer = target_android.buildozer
        m_execute_build_package = call_build_package(target_android)
        assert m_execute_build_package.call_args_list == [
            mock.call(
                [
                    ("--name", "'My Application'"),
                    ("--version", "0.1"),
                    ("--package", "org.test.myapp"),
                    ("--minsdk", "21"),
                    ("--ndk-api", "21"),
                    ("--private", "{buildozer_dir}/android/app".format(buildozer_dir=buildozer.buildozer_dir)),
                    ("--android-entrypoint", "org.kivy.android.PythonActivity"),
                    ("--android-apptheme", "@android:style/Theme.NoTitleBar"),
                    ("--orientation", "portrait"),
                    ("--window",),
                    ("--numeric-version", "1234"),
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

        target_android = init_target(self.temp_dir, {
            'android.manifest.intent_filters': 'filters.xml'
        })
        buildozer = target_android.buildozer
        m_execute_build_package = call_build_package(target_android)

        assert m_execute_build_package.call_args_list == [
            mock.call(
                [
                    ('--name', "'My Application'"),
                    ('--version', '0.1'),
                    ('--package', 'org.test.myapp'),
                    ('--minsdk', '21'),
                    ('--ndk-api', '21'),
                    ('--private', '{buildozer_dir}/android/app'.format(buildozer_dir=buildozer.buildozer_dir)),
                    ('--android-entrypoint', 'org.kivy.android.PythonActivity'),
                    ('--android-apptheme', '@android:style/Theme.NoTitleBar'),
                    ('--orientation', 'portrait'),
                    ('--window',),
                    ('--intent-filters', os.path.realpath(filters_path)),
                    ('debug',),
                ]
            )
        ]

    def test_allow_backup(self):
        """The `android.allow_backup` config should be passed to `build_package()`."""
        target_android = init_target(self.temp_dir, {
            "android.allow_backup": "false"
        })
        buildozer = target_android.buildozer
        m_execute_build_package = call_build_package(target_android)
        assert m_execute_build_package.call_args_list == [
            mock.call(
                [
                    ("--name", "'My Application'"),
                    ("--version", "0.1"),
                    ("--package", "org.test.myapp"),
                    ("--minsdk", "21"),
                    ("--ndk-api", "21"),
                    ("--private", "{buildozer_dir}/android/app".format(buildozer_dir=buildozer.buildozer_dir)),
                    ("--android-entrypoint", "org.kivy.android.PythonActivity"),
                    ("--android-apptheme", "@android:style/Theme.NoTitleBar"),
                    ("--orientation", "portrait"),
                    ("--window",),
                    ("--allow-backup", "false"),
                    ("debug",),
                ]
            )
        ]

    def test_backup_rules(self):
        """The `android.backup_rules` config should be passed to `build_package()`."""
        target_android = init_target(self.temp_dir, {
            "android.backup_rules": "backup_rules.xml"
        })
        buildozer = target_android.buildozer
        m_execute_build_package = call_build_package(target_android)
        assert m_execute_build_package.call_args_list == [
            mock.call(
                [
                    ("--name", "'My Application'"),
                    ("--version", "0.1"),
                    ("--package", "org.test.myapp"),
                    ("--minsdk", "21"),
                    ("--ndk-api", "21"),
                    ("--private", "{buildozer_dir}/android/app".format(buildozer_dir=buildozer.buildozer_dir)),
                    ("--android-entrypoint", "org.kivy.android.PythonActivity"),
                    ("--android-apptheme", "@android:style/Theme.NoTitleBar"),
                    ("--orientation", "portrait"),
                    ("--window",),
                    ("--backup-rules", "{root_dir}/backup_rules.xml".format(root_dir=buildozer.root_dir)),
                    ("debug",),
                ]
            )
        ]

    def test_install_platform_p4a_clone_url(self):
        """The `p4a.url` config should be used for cloning p4a before the `p4a.fork` option."""
        target_android = init_target(self.temp_dir, {
            'p4a.url': 'https://custom-p4a-url/p4a.git',
            'p4a.fork': 'myfork',
        })

        with patch_buildozer_cmd() as m_cmd, mock.patch('buildozer.targets.android.open') as m_open:
            m_open.return_value = StringIO('install_reqs = []')  # to stub setup.py parsing
            target_android._install_p4a()

        assert mock.call(
            'git clone -b master --single-branch https://custom-p4a-url/p4a.git python-for-android',
            cwd=mock.ANY) in m_cmd.call_args_list

    def test_install_platform_p4a_clone_fork(self):
        """The `p4a.fork` config should be used for cloning p4a."""
        target_android = init_target(self.temp_dir, {
            'p4a.fork': 'fork'
        })

        with patch_buildozer_cmd() as m_cmd, mock.patch('buildozer.targets.android.open') as m_open:
            m_open.return_value = StringIO('install_reqs = []')  # to stub setup.py parsing
            target_android._install_p4a()

        assert mock.call(
            'git clone -b master --single-branch https://github.com/fork/python-for-android.git python-for-android',
            cwd=mock.ANY) in m_cmd.call_args_list

    def test_install_platform_p4a_clone_default(self):
        """The default URL should be used for cloning p4a if no config options `p4a.url` and `p4a.fork` are set."""
        target_android = init_target(self.temp_dir)

        with patch_buildozer_cmd() as m_cmd, mock.patch('buildozer.targets.android.open') as m_open:
            m_open.return_value = StringIO('install_reqs = []')  # to stub setup.py parsing
            target_android._install_p4a()

        assert mock.call(
            'git clone -b master --single-branch https://github.com/kivy/python-for-android.git python-for-android',
            cwd=mock.ANY) in m_cmd.call_args_list
