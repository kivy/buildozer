import os
import mock
import unittest
import buildozer as buildozer_module
from buildozer import Buildozer
from six import StringIO


class TestBuildozer(unittest.TestCase):

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
        specfilepath = os.path.join(
            os.path.dirname(buildozer_module.__file__),
            'default.spec')
        buildozer = Buildozer(filename=specfilepath)
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
