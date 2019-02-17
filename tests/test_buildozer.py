import re
import os
import codecs
import mock
import unittest
import buildozer as buildozer_module
from buildozer import Buildozer
from six import StringIO
import tempfile


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
        self.assertEqual(buildozer.specfilename, 'buildozer.spec')
        # spec file doesn't have to exist
        self.assertFalse(os.path.exists(buildozer.specfilename))

    def test_buildozer_read_spec(self):
        """
        Initializes Buildozer object from existing spec file.
        """
        buildozer = Buildozer(filename=self.default_specfile_path())
        self.assertTrue(os.path.exists(buildozer.specfilename))

    def test_buildozer_help(self):
        """
        Makes sure the help gets display with no error, refs:
        https://github.com/kivy/buildozer/issues/813
        """
        buildozer = Buildozer()
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            buildozer.usage()
        self.assertIn('Usage:', mock_stdout.getvalue())

    def test_log_get_set(self):
        """
        Tests reading and setting log level from spec file.
        """
        # the default log level value is known
        buildozer = Buildozer('does_not_exist.spec')
        assert buildozer.log_level == 1
        # sets log level to 2 on the spec file
        self.set_specfile_log_level(self.specfile.name, 2)
        buildozer = Buildozer(self.specfile.name)
        assert buildozer.log_level == 2

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
