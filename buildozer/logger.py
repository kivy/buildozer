"""
Logger
======

Logger implementation used by Buildozer.
The log itself is performed using rich and using the python logging framework.

rich automatically Supports colored output, where available.
"""

import logging
from rich.logging import RichHandler
from rich import print
from pprint import pformat
from rich.console import Console

console = Console(color_system="auto")

# Check if the console supports color for formatting
USE_COLOR = console.color_system != None


class Logger:
    ERROR = 0
    INFO = 1
    DEBUG = 2

    LOG_LEVELS = {ERROR: logging.ERROR, INFO: logging.INFO, DEBUG: logging.DEBUG}

    log_level = ERROR

    def __init__(self):
        """
        Initialize the Logger instance and configure rich logging settings.
        """
        self.handler = RichHandler(
            rich_tracebacks=True, tracebacks_show_locals=True, console=console
        )
        self.handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger = logging.getLogger("rich")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.handler)

    def log(self, level, msg):
        """
        Log a message with the specified log level.

        Args:
            level (int): Log level (ERROR, INFO, DEBUG).
            msg (str): Message to log.
        """
        if level > self.log_level:
            return
        self.logger.log(self.LOG_LEVELS[level], msg)

    def debug(self, msg):
        """
        Log a message with the DEBUG log level.

        Args:
            msg (str): Message to log.
        """
        self.log(self.DEBUG, msg)

    def info(self, msg):
        """
        Log a message with the INFO log level.

        Args:
            msg (str): Message to log.
        """
        self.log(self.INFO, msg)

    def error(self, msg):
        """
        Log a message with the ERROR log level.

        Args:
            msg (str): Message to log.
        """
        self.log(self.ERROR, msg)

    def log_env(self, level, env):
        """
        Log the environment variables.

        Args:
            level (int): Log level (ERROR, INFO, DEBUG).
            env (dict): Dictionary containing environment variables.
        """

        self.log(level, "ENVIRONMENT:")
        for k, v in env.items():
            self.log(level, "    {} = {}".format(k, pformat(v)))
    @classmethod
    def set_level(cls, level):
        """
        set minimum threshold for the logger.

        Args:
            level (int): Log level to set (ERROR, INFO, DEBUG).
        """
        cls.log_level = level
