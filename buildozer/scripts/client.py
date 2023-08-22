'''
Main Buildozer client
=====================

'''

import sys

from buildozer import Buildozer
from buildozer.exceptions import BuildozerCommandException, BuildozerException
from buildozer.logger import Logger


def main():
    try:
        Buildozer().run_command(sys.argv[1:])
    except BuildozerCommandException:
        # don't show the exception in the command line. The log already show
        # the command failed.
        sys.exit(1)
    except BuildozerException as error:
        Logger().error('%s' % error)
        sys.exit(1)


if __name__ == '__main__':
    main()
