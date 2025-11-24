import re
import os
import codecs
import shutil
import unittest
import buildozer as buildozer_module
from buildozer import Buildozer
from io import StringIO
from sys import platform
import tempfile
from unittest import mock
from unittest.mock import PropertyMock

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


class TestCopyApplicationSources(unittest.TestCase):
    """Tests for the _copy_application_sources method."""

    def setUp(self):
        """Create temporary directories for source and app."""
        self.temp_dir = tempfile.mkdtemp()
        self.source_dir = os.path.join(self.temp_dir, 'source')
        self.app_dir = os.path.join(self.temp_dir, 'app')
        os.makedirs(self.source_dir)
        os.makedirs(self.app_dir)

        # Create a temporary spec file
        # (even if empty, to avoid file_exists issues)
        self.specfile = tempfile.NamedTemporaryFile(
            mode='w', suffix='.spec', delete=False, dir=self.temp_dir
        )
        self.specfile.write('')
        self.specfile.close()
        self.specfilename = self.specfile.name

        # Default config values (empty filters)
        self.default_config = {
            ('app', 'source.dir', '.'): self.source_dir,
            ('app', 'source.include_exts', ''): [],
            ('app', 'source.exclude_exts', ''): [],
            ('app', 'source.exclude_dirs', ''): [],
            ('app', 'source.exclude_patterns', ''): [],
            ('app', 'source.include_patterns', ''): [],
            ('buildozer', 'log_level', '2'): '2',
            ('buildozer', 'bin_dir', None): None,
        }

        # Patches that will be used in create_buildozer
        self.patches = []

    def tearDown(self):
        """Remove temporary directories and stop patches."""
        # Stop all patches
        for p in self.patches:
            p.stop()

        # Clean up temp files
        if hasattr(self, 'specfile') and os.path.exists(self.specfilename):
            os.unlink(self.specfilename)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_buildozer(self, custom_config=None):
        """
        Helper to create a Buildozer instance with mocked dependencies.

        Args:
            custom_config: Optional dict to override default_config values.
                          If provided, it will be merged with default_config.

        Returns a Buildozer instance ready to call _copy_application_sources.
        """
        # Use custom config if provided, otherwise use default
        config = self.default_config.copy()
        if custom_config:
            config.update(custom_config)

        # Mock SpecParser to return our test config
        mock_spec_parser = mock.MagicMock()

        def config_getdefault(*args):
            key = args if len(args) == 3 else args[:2]
            return config.get(key, args[-1] if len(args) == 3 else '')

        def config_getlist(*args):
            key = args if len(args) == 3 else args[:2]
            result = config.get(key, args[-1] if len(args) == 3 else '')
            # Ensure we return a list
            if isinstance(result, str):
                return [result] if result else []
            return result if result else []

        mock_spec_parser.read = mock.Mock()
        mock_spec_parser.getdefault = mock.Mock(side_effect=config_getdefault)
        mock_spec_parser.getlist = mock.Mock(side_effect=config_getlist)

        # Patch SpecParser constructor
        spec_parser_patch = mock.patch('buildozer.SpecParser',
                                       return_value=mock_spec_parser)
        self.patches.append(spec_parser_patch)
        spec_parser_patch.start()

        # Mock check_configuration_tokens to do nothing
        check_config_patch = mock.patch.object(
            __import__('buildozer').Buildozer,
            'check_configuration_tokens',
            mock.Mock()
        )
        self.patches.append(check_config_patch)
        check_config_patch.start()

        # Import and create Buildozer instance
        from buildozer import Buildozer

        buildozer = Buildozer(filename=self.specfilename)

        # Patch app_dir property
        app_dir_patch = mock.patch.object(
            type(buildozer),
            'app_dir',
            new_callable=PropertyMock,
            return_value=self.app_dir
        )
        self.patches.append(app_dir_patch)
        app_dir_patch.start()

        return buildozer

    def create_file(self, relpath, content=''):
        """Helper to create a file in source_dir."""
        filepath = os.path.join(self.source_dir, relpath)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath

    @mock.patch('buildozer.buildops')
    def test_ignore_hidden_files_and_directories_in_source(self,
                                                           mock_buildops):
        """Test that hidden files directories under source_dir are ignored."""
        # Create structure:
        # source/
        #   main.py
        #   .hidden_file.py
        #   .hidden/
        #     secret.py
        #   visible/
        #     code.py
        #   subdir/
        #     code2.py
        #     .hidden2.py
        self.create_file('main.py', 'print("main")')
        self.create_file('.hidden_file.py', 'print("hidden")')
        self.create_file('.hidden/secret.py', 'print("secret")')
        self.create_file('visible/code.py', 'print("code")')
        self.create_file('subdir/code2.py', 'print("code2")')
        self.create_file('subdir/.hidden2.py', 'print("hidden2")')

        buildozer = self.create_buildozer()
        buildozer._copy_application_sources()

        # Check that file_copy was called for main.py and visible/code.py
        # but NOT for .hidden/secret.py
        copy_calls = mock_buildops.file_copy.call_args_list
        copied_files = [call[0][0] for call in copy_calls]

        self.assertTrue(any('main.py' in f for f in copied_files))
        self.assertTrue(any('visible' in f and 'code.py' in f
                            for f in copied_files))
        self.assertTrue(any('subdir' in f and 'code2.py' in f
                            for f in copied_files))
        self.assertFalse(any('.hidden' in f for f in copied_files))
        self.assertFalse(any('secret.py' in f for f in copied_files))
        self.assertFalse(any('.hidden_file.py' in f for f in copied_files))
        self.assertFalse(any('.hidden2.py' in f for f in copied_files))

    @mock.patch('buildozer.buildops')
    def test_source_dir_with_hidden_parent(self, mock_buildops):
        """
        Test that files are copied even when source_dir has hidden parents.
        """
        # Create a source directory with hidden parent
        hidden_source = os.path.join(self.temp_dir, '.hidden_parent',
                                     'project')
        os.makedirs(hidden_source)

        # Create files in the hidden parent path
        main_file = os.path.join(hidden_source, 'main.py')
        with open(main_file, 'w') as f:
            f.write('print("main")')

        # Create a hidden subdirectory under source
        hidden_sub = os.path.join(hidden_source, '.sub_hidden')
        os.makedirs(hidden_sub)
        secret_file = os.path.join(hidden_sub, 'secret.py')
        with open(secret_file, 'w') as f:
            f.write('print("secret")')

        # Use custom config with the hidden source directory
        custom_config = {
            ('app', 'source.dir', '.'): hidden_source
        }

        buildozer = self.create_buildozer(custom_config=custom_config)
        buildozer._copy_application_sources()

        copy_calls = mock_buildops.file_copy.call_args_list
        copied_files = [call[0][0] for call in copy_calls]

        # main.py should be copied (not in a hidden dir relative to source)
        self.assertTrue(any('main.py' in f for f in copied_files))
        # .sub_hidden/secret.py should NOT be copied
        # (hidden relative to source)
        self.assertFalse(any('.sub_hidden' in f for f in copied_files))

    @mock.patch('buildozer.buildops')
    def test_include_extensions_filter(self, mock_buildops):
        """Test that only files with specified extensions are included."""
        self.create_file('main.py', 'print("main")')
        self.create_file('image.png', 'PNG')
        self.create_file('doc.txt', 'text')

        # Set include_exts to only py and png
        custom_config = {
            ('app', 'source.include_exts', ''): ['py', 'png']
        }

        buildozer = self.create_buildozer(custom_config=custom_config)
        buildozer._copy_application_sources()

        copy_calls = mock_buildops.file_copy.call_args_list
        copied_files = [call[0][0] for call in copy_calls]

        self.assertTrue(any('main.py' in f for f in copied_files))
        self.assertTrue(any('image.png' in f for f in copied_files))
        self.assertFalse(any('doc.txt' in f for f in copied_files))

    @mock.patch('buildozer.buildops')
    def test_exclude_dirs_filter(self, mock_buildops):
        """Test that specified directories are excluded."""
        self.create_file('main.py', 'print("main")')
        self.create_file('tests/test_main.py', 'test')
        self.create_file('venv/lib/module.py', 'module')
        self.create_file('src/code.py', 'code')

        # Exclude tests and venv directories
        custom_config = {
            ('app', 'source.exclude_dirs', ''): ['tests', 'venv']
        }

        buildozer = self.create_buildozer(custom_config=custom_config)
        buildozer._copy_application_sources()

        copy_calls = mock_buildops.file_copy.call_args_list
        copied_files = [call[0][0] for call in copy_calls]

        self.assertTrue(any('main.py' in f for f in copied_files))
        self.assertTrue(any('src' in f and 'code.py' in f
                            for f in copied_files))
        self.assertFalse(any('tests' in f for f in copied_files))
        self.assertFalse(any('venv' in f for f in copied_files))

    @mock.patch('buildozer.buildops')
    def test_exclude_patterns(self, mock_buildops):
        """Test that files matching exclude patterns are excluded."""
        self.create_file('LICENSE', 'license text')
        self.create_file('main.py', 'code')
        self.create_file('images/photo.jpg', 'jpg')
        self.create_file('images/icon.png', 'png')

        # Exclude license and jpg files
        custom_config = {
            ('app', 'source.exclude_patterns', ''): ['license', '*.jpg']
        }

        buildozer = self.create_buildozer(custom_config=custom_config)
        buildozer._copy_application_sources()

        copy_calls = mock_buildops.file_copy.call_args_list
        copied_files = [call[0][0] for call in copy_calls]

        self.assertTrue(any('main.py' in f for f in copied_files))
        self.assertTrue(any('icon.png' in f for f in copied_files))
        self.assertFalse(any('LICENSE' in f for f in copied_files))
        self.assertFalse(any('photo.jpg' in f for f in copied_files))
