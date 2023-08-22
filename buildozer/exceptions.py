class BuildozerException(Exception):
    """
    Exception raised for general situations buildozer cannot process.
    """

    pass


class BuildozerCommandException(BuildozerException):
    """
    Exception raised when an external command failed.

    See: `Buildozer.buildops.cmd()`.
    """

    pass
