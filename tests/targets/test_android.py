import os
import sys
import pytest
import codecs
import tempfile
import buildozer as buildozer_module
from buildozer import Buildozer
from buildozer.targets.android import TargetAndroid

try:
    from unittest import mock  # Python 3
except ImportError:
    import mock  # Python 2


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


class TestTargetAndroid:
    @staticmethod
    def default_specfile_path():
        return os.path.join(os.path.dirname(buildozer_module.__file__), "default.spec")

    def setup_method(self):
        """Creates a temporary spec file containing the content of the default.spec."""
        self.specfile = tempfile.NamedTemporaryFile(suffix=".spec", delete=False)
        default_spec = codecs.open(self.default_specfile_path(), encoding="utf-8")
        self.specfile.write(default_spec.read().encode("utf-8"))
        self.specfile.close()
        self.buildozer = Buildozer(filename=self.specfile.name, target="android")
        self.target_android = TargetAndroid(self.buildozer)

    def tear_method(self):
        """Deletes the temporary spec file."""
        os.unlink(self.specfile.name)

    def test_init(self):
        """Tests init defaults."""
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
            self.target_android.extra_p4a_args
            == ' --color=always --storage-dir="/tmp/.buildozer/android/platform/build-armeabi-v7a" --ndk-api=21'
        )
        assert self.target_android.p4a_apk_cmd == "apk --debug --bootstrap=sdl2"
        assert self.target_android.platform_update is False

    @pytest.mark.skipif(
        sys.version_info < (3, 0), reason="Python 2 ex_info.value.args is different"
    )
    def test_init_positional_buildozer(self):
        """Positional `buildozer` argument is required."""
        with pytest.raises(TypeError) as ex_info:
            TargetAndroid()
        assert ex_info.value.args == (
            "__init__() missing 1 required positional argument: 'buildozer'",
        )

    def test_sdkmanager(self):
        """Tests the _sdkmanager() method."""
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
        with mock.patch(
            "buildozer.targets.android.Target.check_configuration_tokens"
        ) as m_check_configuration_tokens:
            self.target_android.check_configuration_tokens()
        assert m_check_configuration_tokens.call_args_list == [mock.call([])]

    def test_install_android_sdk(self):
        """Basic tests for the _install_android_sdk() method."""
        with patch_buildozer_file_exists() as m_file_exists, patch_buildozer_download() as m_download:
            m_file_exists.return_value = True
            sdk_dir = self.target_android._install_android_sdk()
        assert m_file_exists.call_args_list == [
            mock.call(self.target_android.android_sdk_dir)
        ]
        assert m_download.call_args_list == []
        assert sdk_dir.endswith(".buildozer/android/platform/android-sdk")
        with patch_buildozer_file_exists() as m_file_exists, patch_buildozer_download() as m_download, patch_buildozer_file_extract() as m_file_extract:
            m_file_exists.return_value = False
            sdk_dir = self.target_android._install_android_sdk()
        assert m_file_exists.call_args_list == [
            mock.call(self.target_android.android_sdk_dir)
        ]
        assert m_download.call_args_list == [
            mock.call(
                "http://dl.google.com/android/repository/",
                "sdk-tools-linux-4333796.zip",
                cwd=mock.ANY,
            )
        ]
        assert m_file_extract.call_args_list == [
            mock.call("sdk-tools-linux-4333796.zip", cwd=mock.ANY)
        ]
        assert sdk_dir.endswith(".buildozer/android/platform/android-sdk")
