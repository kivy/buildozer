import sys
import tempfile
from unittest import mock

import pytest

from buildozer.targets.ios import TargetIos
from tests.targets.utils import init_buildozer, patch_buildozer_checkbin


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
