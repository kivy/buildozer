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
        pass
    except BuildozerException as error:
        Buildozer().error('%s' % error)

if __name__ == '__main__':
    main()
