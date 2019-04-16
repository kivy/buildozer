import sys
import mock
import unittest
from buildozer import BuildozerCommandException
from buildozer.scripts import client


class TestClient(unittest.TestCase):

    def test_run_command_called(self):
        """
        Checks Buildozer.run_command() is being called with arguments from command line.
        """
        with mock.patch('buildozer.Buildozer.run_command') as m_run_command:
            client.main()
        assert m_run_command.call_args_list == [mock.call(sys.argv[1:])]

    def test_exit_code(self):
        """
        Makes sure the CLI exits with error code on BuildozerCommandException, refs #674.
        """
        with mock.patch('buildozer.Buildozer.run_command') as m_run_command:
            m_run_command.side_effect = BuildozerCommandException()
            with self.assertRaises(SystemExit) as context:
                client.main()
        assert context.exception.code == 1
