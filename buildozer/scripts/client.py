'''
Main Buildozer client
=====================

'''

import sys
from buildozer import Buildozer, BuildozerCommandException, BuildozerException


def main():
    try:
        Buildozer().run_command(sys.argv[1:])
    except BuildozerCommandException:
        # don't show the exception in the command line. The log already show
        # the command failed.
        sys.exit(1)
    except BuildozerException as error:
        Buildozer().error('%s' % error)
        sys.exit(1)


if __name__ == '__main__':
    main()
