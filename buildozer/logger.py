"""
Logger
======

Logger implementation used by Buildozer.

Supports colored output, where available.
"""

from os import environ
from pprint import pformat
import sys

try:
    # if installed, it can give color to Windows as well
    import colorama

    colorama.init()
except ImportError:
    colorama = None

# set color codes
if colorama:
    RESET_SEQ = colorama.Fore.RESET + colorama.Style.RESET_ALL
    COLOR_SEQ = lambda x: x  # noqa: E731
    BOLD_SEQ = ""
    if sys.platform == "win32":
        BLACK = colorama.Fore.BLACK + colorama.Style.DIM
    else:
        BLACK = colorama.Fore.BLACK + colorama.Style.BRIGHT
    RED = colorama.Fore.RED
    BLUE = colorama.Fore.CYAN
    USE_COLOR = "NO_COLOR" not in environ
elif sys.platform != "win32":
    RESET_SEQ = "\033[0m"
    COLOR_SEQ = lambda x: "\033[1;{}m".format(30 + x)  # noqa: E731
    BOLD_SEQ = "\033[1m"
    BLACK = 0
    RED = 1
    BLUE = 4
    USE_COLOR = "NO_COLOR" not in environ
else:
    RESET_SEQ = ""
    COLOR_SEQ = ""
    BOLD_SEQ = ""
    RED = BLUE = BLACK = 0
    USE_COLOR = False


class Logger:
    ERROR = 0
    INFO = 1
    DEBUG = 2

    LOG_LEVELS_C = (RED, BLUE, BLACK)  # Map levels to colors
    LOG_LEVELS_T = "EID"  # error, info, debug

    log_level = ERROR

    def log(self, level, msg):
        if level > self.log_level:
            return
        if USE_COLOR:
            color = COLOR_SEQ(Logger.LOG_LEVELS_C[level])
            print("".join((RESET_SEQ, color, "# ", msg, RESET_SEQ)))
        else:
            print("{} {}".format(Logger.LOG_LEVELS_T[level], msg))

    def debug(self, msg):
        self.log(self.DEBUG, msg)

    def info(self, msg):
        self.log(self.INFO, msg)

    def error(self, msg):
        self.log(self.ERROR, msg)

    def log_env(self, level, env):
        """dump env into logger in readable format"""
        self.log(level, "ENVIRONMENT:")
        for k, v in env.items():
            self.log(level, "    {} = {}".format(k, pformat(v)))

    @classmethod
    def set_level(cls, level):
        """set minimum threshold for log messages"""
        cls.log_level = level
