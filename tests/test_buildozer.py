import re
import os
import codecs
import mock
import unittest
import buildozer as buildozer_module
from buildozer import Buildozer, IS_PY3
from six import StringIO
import tempfile

from buildozer.targets.android import TargetAndroid


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
        with open(filepath, 'w') as f:
            file_content = re.sub(pattern, replace, file_content)
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

    def test_buildozer_base(self):
        """
        Basic test making sure the Buildozer object can be instanciated.
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
        assert buildozer.log_level == 2
        # sets log level to 1 on the spec file
        self.set_specfile_log_level(self.specfile.name, 1)
        buildozer = Buildozer(self.specfile.name)
        assert buildozer.log_level == 1

    def test_log_print(self):
        """
        Checks logger prints different info depending on log level.
        """
        # sets log level to 1 in the spec file
        self.set_specfile_log_level(self.specfile.name, 1)
        buildozer = Buildozer(self.specfile.name)
        assert buildozer.log_level == 1
        # at this level, debug messages shouldn't not be printed
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            buildozer.debug('debug message')
            buildozer.info('info message')
            buildozer.error('error message')
        # using `in` keyword rather than `==` because of bash color prefix/suffix
        assert 'debug message' not in mock_stdout.getvalue()
        assert 'info message' in mock_stdout.getvalue()
        assert 'error message' in mock_stdout.getvalue()
        # sets log level to 2 in the spec file
        self.set_specfile_log_level(self.specfile.name, 2)
        buildozer = Buildozer(self.specfile.name)
        assert buildozer.log_level == 2
        # at this level all message types should be printed
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            buildozer.debug('debug message')
            buildozer.info('info message')
            buildozer.error('error message')
        assert 'debug message' in mock_stdout.getvalue()
        assert 'info message' in mock_stdout.getvalue()
        assert 'error message' in mock_stdout.getvalue()

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

    def test_android_ant_path(self):
        """
        Verify that the selected ANT path is being used from the spec file
        """
        my_ant_path = '/my/ant/path'

        buildozer = Buildozer(filename=self.default_specfile_path(), target='android')
        buildozer.config.set('app', 'android.ant_path', my_ant_path)  # Set ANT path
        target = TargetAndroid(buildozer=buildozer)

        # Mock first run
        with mock.patch('buildozer.Buildozer.download') as download, \
                mock.patch('buildozer.Buildozer.file_extract') as extract_file, \
                mock.patch('os.makedirs'):
            ant_path = target._install_apache_ant()
            assert ant_path == my_ant_path

        # Mock ant already installed
        with mock.patch.object(Buildozer, 'file_exists', return_value=True):
            ant_path = target._install_apache_ant()
            assert ant_path == my_ant_path

    def test_cmd_unicode_decode(self):
        """
        Verifies Buildozer.cmd() can properly handle non-unicode outputs.
        refs: https://github.com/kivy/buildozer/issues/857
        """
        buildozer = Buildozer()
        command = 'uname'
        kwargs = {
            'show_output': True,
            'get_stdout': True,
            'get_stderr': True,
        }
        command_output = b'\x80 cannot decode \x80'
        # showing the point that we can't decode it
        with self.assertRaises(UnicodeDecodeError):
            command_output.decode('utf-8')
        with mock.patch('buildozer.Popen') as m_popen, \
                mock.patch('buildozer.select') as m_select, \
                mock.patch('buildozer.stdout') as m_stdout:
            m_select.select().__getitem__.return_value = [0]
            # makes sure fcntl.fcntl() gets what it expects so it doesn't crash
            m_popen().stdout.fileno.return_value = 0
            m_popen().stderr.fileno.return_value = 2
            # Buildozer.cmd() is iterating through command output "chunk" until
            # one chunk is None
            m_popen().stdout.read.side_effect = [command_output, None]
            m_popen().returncode = 0
            stdout, stderr, returncode = buildozer.cmd(command, **kwargs)
        # when get_stdout is True, the command output also gets returned
        assert stdout == command_output.decode('utf-8', 'ignore')
        assert stderr is None
        assert returncode == 0
        # Python2 and Python3 have different approaches for decoding the output
        if IS_PY3:
            assert m_stdout.write.call_args_list == [
                mock.call(command_output.decode('utf-8', 'replace'))
            ]
        else:
            assert m_stdout.write.call_args_list == [
                mock.call(command_output)
            ]
