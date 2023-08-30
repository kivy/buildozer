import re
import os
import codecs
import unittest
import buildozer as buildozer_module
from buildozer import Buildozer
from io import StringIO
from sys import platform
import tempfile
from unittest import mock

from buildozer.targets.android import (
    TargetAndroid, DEFAULT_ANDROID_NDK_VERSION, MSG_P4A_RECOMMENDED_NDK_ERROR
)


class TestBuildozer(unittest.TestCase):

    def setUp(self):
        """
        Creates a temporary spec file containing the content of the default.spec.
        """
        self.specfile = tempfile.NamedTemporaryFile(suffix='.spec', delete=False)
        self.specfilename = self.specfile.name
        default_spec = codecs.open(self.default_specfile_path(), encoding='utf-8')
        self.specfile.write(default_spec.read().encode('utf-8'))
        self.specfile.close()

    def tearDown(self):
        """
        Deletes the temporary spec file.
        """
        os.unlink(self.specfile.name)

    @staticmethod
    def default_specfile_path():
        return os.path.join(
            os.path.dirname(buildozer_module.__file__),
            'default.spec')

    @staticmethod
    def file_re_sub(filepath, pattern, replace):
        """
        Helper method for inplace file regex editing.
        """
        with open(filepath) as f:
            file_content = f.read()
        file_content = re.sub(pattern, replace, file_content)
        with open(filepath, 'w') as f:
            f.write(file_content)

    @classmethod
    def set_specfile_log_level(cls, specfilename, log_level):
        """
        Helper method for setting `log_level` in a given `specfilename`.
        """
        pattern = 'log_level = [0-9]'
        replace = 'log_level = {}'.format(log_level)
        cls.file_re_sub(specfilename, pattern, replace)
        buildozer = Buildozer(specfilename)
        assert buildozer.logger.log_level == log_level

    def test_buildozer_base(self):
        """
        Basic test making sure the Buildozer object can be instantiated.
        """
        buildozer = Buildozer()
        assert buildozer.specfilename == 'buildozer.spec'
        # spec file doesn't have to exist
        assert os.path.exists(buildozer.specfilename) is False

    def test_buildozer_read_spec(self):
        """
        Initializes Buildozer object from existing spec file.
        """
        buildozer = Buildozer(filename=self.default_specfile_path())
        assert os.path.exists(buildozer.specfilename) is True

    def test_buildozer_help(self):
        """
        Makes sure the help gets display with no error, refs:
        https://github.com/kivy/buildozer/issues/813
        """
        buildozer = Buildozer()
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            buildozer.usage()
        assert 'Usage:' in mock_stdout.getvalue()

    def test_log_get_set(self):
        """
        Tests reading and setting log level from spec file.
        """
        # the default log level value is known
        buildozer = Buildozer('does_not_exist.spec')
        assert buildozer.logger.log_level == 2
        # sets log level to 1 on the spec file
        self.set_specfile_log_level(self.specfile.name, 1)
        buildozer = Buildozer(self.specfile.name)
        assert buildozer.logger.log_level == 1

    def test_run_command_unknown(self):
        """
        Makes sure the unknown command/target is handled gracefully, refs:
        https://github.com/kivy/buildozer/issues/812
        """
        buildozer = Buildozer()
        command = 'foobar'
        args = [command, 'debug']
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with self.assertRaises(SystemExit):
                buildozer.run_command(args)
        assert mock_stdout.getvalue() == 'Unknown command/target {}\n'.format(command)

    @unittest.skipIf(
        platform == "win32",
        "Test can't handle when resulting path is normalised on Windows")
    def test_android_ant_path(self):
        """
        Verify that the selected ANT path is being used from the spec file
        """
        my_ant_path = '/my/ant/path'

        buildozer = Buildozer(filename=self.default_specfile_path(), target='android')
        buildozer.config.set('app', 'android.ant_path', my_ant_path)  # Set ANT path
        target = TargetAndroid(buildozer=buildozer)

        # Mock first run
        with mock.patch('buildozer.buildops.download') as download, \
                mock.patch('buildozer.buildops.file_extract') as m_file_extract, \
                mock.patch('os.makedirs'):
            ant_path = target._install_apache_ant()
        assert m_file_extract.call_args_list == [
            mock.call(mock.ANY, cwd='/my/ant/path', env=mock.ANY)]
        assert ant_path == my_ant_path
        assert download.call_args_list == [
            mock.call("https://archive.apache.org/dist/ant/binaries/", mock.ANY, cwd=my_ant_path)]
        # Mock ant already installed
        with mock.patch('buildozer.buildops.file_exists', return_value=True):
            ant_path = target._install_apache_ant()
        assert ant_path == my_ant_path

    def test_p4a_recommended_ndk_version_default_value(self):
        self.set_specfile_log_level(self.specfile.name, 1)
        buildozer = Buildozer(self.specfile.name, 'android')
        assert buildozer.target.p4a_recommended_ndk_version is None

    def test_p4a_recommended_android_ndk_error(self):
        self.set_specfile_log_level(self.specfile.name, 1)
        buildozer = Buildozer(self.specfile.name, 'android')

        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            ndk_version = buildozer.target.p4a_recommended_android_ndk
        assert MSG_P4A_RECOMMENDED_NDK_ERROR in mock_stdout.getvalue()
        # and we should get the default android's ndk version of buildozer
        assert ndk_version == DEFAULT_ANDROID_NDK_VERSION

    @mock.patch('buildozer.targets.android.os.path.isfile')
    @mock.patch('buildozer.targets.android.os.path.exists')
    @mock.patch('buildozer.targets.android.open', create=True)
    def test_p4a_recommended_android_ndk_found(
            self, mock_open, mock_exists, mock_isfile
    ):
        self.set_specfile_log_level(self.specfile.name, 1)
        buildozer = Buildozer(self.specfile.name, 'android')
        expected_ndk = '19b'
        recommended_line = 'RECOMMENDED_NDK_VERSION = {expected_ndk}\n'.format(
            expected_ndk=expected_ndk)
        mock_open.return_value = StringIO(recommended_line)
        ndk_version = buildozer.target.p4a_recommended_android_ndk
        p4a_dir = os.path.join(
            buildozer.platform_dir, buildozer.target.p4a_directory_name)
        mock_open.assert_called_once_with(
            os.path.join(p4a_dir, "pythonforandroid", "recommendations.py"), 'r'
        )
        assert ndk_version == expected_ndk

        # now test that we only read one time p4a file, so we call again to
        # `p4a_recommended_android_ndk` and we should still have one call to `open`
        # file, the performed above
        ndk_version = buildozer.target.p4a_recommended_android_ndk
        mock_open.assert_called_once()
