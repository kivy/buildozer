import unittest
from buildozer.logger import Logger

from io import StringIO
from unittest import mock


class TestLogger(unittest.TestCase):
    def test_log_print(self):
        """
        Checks logger prints different info depending on log level.
        """
        logger = Logger()

        # Test ERROR Level
        Logger.set_level(0)
        assert logger.log_level == logger.ERROR

        # at this level, only error messages should be printed
        with mock.patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger.debug("debug message")
            logger.info("info message")
            logger.error("error message")
        # using `in` keyword rather than `==` because of color prefix/suffix
        assert "debug message" not in mock_stdout.getvalue()
        assert "info message" not in mock_stdout.getvalue()
        assert "error message" in mock_stdout.getvalue()

        # Test INFO Level
        Logger.set_level(1)
        assert logger.log_level == logger.INFO

        # at this level, debug messages should not be printed
        with mock.patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger.debug("debug message")
            logger.info("info message")
            logger.error("error message")
        # using `in` keyword rather than `==` because of color prefix/suffix
        assert "debug message" not in mock_stdout.getvalue()
        assert "info message" in mock_stdout.getvalue()
        assert "error message" in mock_stdout.getvalue()

        # sets log level to 2 in the spec file
        Logger.set_level(2)
        assert logger.log_level == logger.DEBUG
        # at this level all message types should be printed
        with mock.patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger.debug("debug message")
            logger.info("info message")
            logger.error("error message")
        assert "debug message" in mock_stdout.getvalue()
        assert "info message" in mock_stdout.getvalue()
        assert "error message" in mock_stdout.getvalue()
