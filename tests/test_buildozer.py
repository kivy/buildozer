import unittest
from buildozer import Buildozer


class TestBuildozer(unittest.TestCase):

    def test_buildozer_base(self):
        """
        Basic test making sure the Buildozer object can be instanciated.
        """
        buildozer = Buildozer()
        self.assertEqual(buildozer.specfilename, 'buildozer.spec')
