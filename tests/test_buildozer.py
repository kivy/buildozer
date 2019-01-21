import os
import unittest
import buildozer as buildozer_module
from buildozer import Buildozer


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
