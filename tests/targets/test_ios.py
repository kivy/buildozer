import sys
import tempfile
from unittest import mock

import pytest

from buildozer import BuildozerCommandException
from buildozer.targets.ios import TargetIos
from tests.targets.utils import (
    init_buildozer,
    patch_buildozer_checkbin,
    patch_buildozer_cmd,
    patch_buildozer_error,
    patch_buildozer_file_exists,
)


def patch_target_ios(method):
    return mock.patch("buildozer.targets.ios.TargetIos.{method}".format(method=method))


def init_target(temp_dir, options=None):
    buildozer = init_buildozer(temp_dir, "ios", options)
    return TargetIos(buildozer)


@pytest.mark.skipif(
    sys.platform != "darwin", reason="Only macOS is supported for target iOS"
)
class TestTargetIos:
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
        target = init_target(self.temp_dir)
        assert target.targetname == "ios"
        assert target.code_signing_allowed == "CODE_SIGNING_ALLOWED=NO"
        assert target.build_mode == "debug"
        assert target.platform_update is False

    def test_check_requirements(self):
        """Basic tests for the check_requirements() method."""
        target = init_target(self.temp_dir)
        buildozer = target.buildozer
        assert not hasattr(target, "adb_cmd")
        assert not hasattr(target, "javac_cmd")
        assert "PATH" not in buildozer.environ
        with patch_buildozer_checkbin() as m_checkbin:
            target.check_requirements()
        assert m_checkbin.call_args_list == [
            mock.call("Xcode xcodebuild", "xcodebuild"),
            mock.call("Xcode xcode-select", "xcode-select"),
            mock.call("Git git", "git"),
            mock.call("Cython cython", "cython"),
            mock.call("pkg-config", "pkg-config"),
            mock.call("autoconf", "autoconf"),
            mock.call("automake", "automake"),
            mock.call("libtool", "libtool"),
        ]
        assert target._toolchain_cmd.endswith("toolchain.py ")
        assert target._xcodebuild_cmd == "xcodebuild "

    def test_check_configuration_tokens(self):
        """Basic tests for the check_configuration_tokens() method."""
        target = init_target(self.temp_dir, {"ios.codesign.allowed": "yes"})
        with mock.patch(
            "buildozer.targets.android.Target.check_configuration_tokens"
        ) as m_check_configuration_tokens, mock.patch(
            "buildozer.targets.ios.TargetIos._get_available_identities"
        ) as m_get_available_identities:
            target.check_configuration_tokens()
        assert m_get_available_identities.call_args_list == [mock.call()]
        assert m_check_configuration_tokens.call_args_list == [
            mock.call(
                [
                    '[app] "ios.codesign.debug" key missing, you must give a certificate name to use.',
                    '[app] "ios.codesign.release" key missing, you must give a certificate name to use.',
                ]
            )
        ]

    def test_get_available_packages(self):
        """Checks the toolchain `recipes --compact` output is parsed correctly to return recipe list."""
        target = init_target(self.temp_dir)
        with patch_target_ios("toolchain") as m_toolchain:
            m_toolchain.return_value = ("hostpython3 kivy pillow python3 sdl2", None, 0)
            available_packages = target.get_available_packages()
        assert m_toolchain.call_args_list == [
            mock.call("recipes --compact", get_stdout=True)
        ]
        assert available_packages == [
            "hostpython3",
            "kivy",
            "pillow",
            "python3",
            "sdl2",
        ]

    def test_install_platform(self):
        """Checks `install_platform()` calls clone commands and sets `ios_dir` and `ios_deploy_dir` attributes."""
        target = init_target(self.temp_dir)
        assert target.ios_dir is None
        assert target.ios_deploy_dir is None
        with patch_buildozer_cmd() as m_cmd:
            target.install_platform()
        assert m_cmd.call_args_list == [
            mock.call("git clone https://github.com/kivy/kivy-ios", cwd=mock.ANY),
            mock.call(
                "git clone --branch 1.10.0 https://github.com/phonegap/ios-deploy",
                cwd=mock.ANY,
            ),
        ]
        assert target.ios_dir.endswith(".buildozer/ios/platform/kivy-ios")
        assert target.ios_deploy_dir.endswith(".buildozer/ios/platform/ios-deploy")

    def test_compile_platform(self):
        """Checks the `toolchain build` command is called on the ios requirements."""
        target = init_target(self.temp_dir)
        target.ios_deploy_dir = "/ios/deploy/dir"
        # fmt: off
        with patch_target_ios("get_available_packages") as m_get_available_packages, \
             patch_target_ios("toolchain") as m_toolchain, \
             patch_buildozer_file_exists() as m_file_exists:
            m_get_available_packages.return_value = ["hostpython3", "python3"]
            m_file_exists.return_value = True
            target.compile_platform()
        # fmt: on
        assert m_get_available_packages.call_args_list == [mock.call()]
        assert m_toolchain.call_args_list == [mock.call("build python3")]
        assert m_file_exists.call_args_list == [
            mock.call(target.ios_deploy_dir, "ios-deploy")
        ]

    def test_get_package(self):
        """Checks default package values and checks it can be overridden."""
        # default value
        target = init_target(self.temp_dir)
        package = target._get_package()
        assert package == "org.test.myapp"
        # override
        target = init_target(
            self.temp_dir,
            {"package.domain": "com.github.kivy", "package.name": "buildozer"},
        )
        package = target._get_package()
        assert package == "com.github.kivy.buildozer"

    def test_unlock_keychain_wrong_password(self):
        """A `BuildozerCommandException` should be raised on wrong password 3 times."""
        target = init_target(self.temp_dir)
        # fmt: off
        with mock.patch("buildozer.targets.ios.getpass") as m_getpass, \
             patch_buildozer_cmd() as m_cmd, \
             pytest.raises(BuildozerCommandException):
            m_getpass.return_value = "password"
            # the `security unlock-keychain` command returned an error
            # hence we'll get prompted to enter the password
            m_cmd.return_value = (None, None, 123)
            target._unlock_keychain()
        # fmt: on
        assert m_getpass.call_args_list == [
            mock.call("Password to unlock the default keychain:"),
            mock.call("Password to unlock the default keychain:"),
            mock.call("Password to unlock the default keychain:"),
        ]

    def test_build_package_no_signature(self):
        """Code signing is currently required to go through final `xcodebuild` steps."""
        target = init_target(self.temp_dir)
        target.ios_dir = "/ios/dir"
        # fmt: off
        with patch_target_ios("_unlock_keychain") as m_unlock_keychain, \
             patch_buildozer_error() as m_error, \
             mock.patch("buildozer.targets.ios.TargetIos.load_plist_from_file") as m_load_plist_from_file, \
             mock.patch("buildozer.targets.ios.TargetIos.dump_plist_to_file") as m_dump_plist_to_file, \
             patch_buildozer_cmd() as m_cmd:
            m_load_plist_from_file.return_value = {}
            target.build_package()
        # fmt: on
        assert m_unlock_keychain.call_args_list == [mock.call()]
        assert m_error.call_args_list == [
            mock.call(
                "Cannot create the IPA package without signature. "
                'You must fill the "ios.codesign.debug" token.'
            )
        ]
        assert m_load_plist_from_file.call_args_list == [
            mock.call("/ios/dir/myapp-ios/myapp-Info.plist")
        ]
        assert m_dump_plist_to_file.call_args_list == [
            mock.call(
                {
                    "CFBundleIdentifier": "org.test.myapp",
                    "CFBundleShortVersionString": "0.1",
                    "CFBundleVersion": "0.1.None",
                },
                "/ios/dir/myapp-ios/myapp-Info.plist",
            )
        ]
        assert m_cmd.call_args_list == [mock.call(mock.ANY, cwd=target.ios_dir), mock.call(
            "xcodebuild -configuration Debug -allowProvisioningUpdates ENABLE_BITCODE=NO "
            "CODE_SIGNING_ALLOWED=NO clean build",
            cwd="/ios/dir/myapp-ios",
        )]
