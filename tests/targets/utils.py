import os
import re
from unittest import mock

import buildozer as buildozer_module
from buildozer import Buildozer


def patch_buildozer(method):
    return mock.patch("buildozer.Buildozer.{method}".format(method=method))


def patch_buildozer_cmd():
    return patch_buildozer("cmd")


def patch_buildozer_checkbin():
    return patch_buildozer("checkbin")


def patch_buildozer_file_exists():
    return patch_buildozer("file_exists")


def patch_buildozer_error():
    return patch_buildozer("error")


def default_specfile_path():
    return os.path.join(os.path.dirname(buildozer_module.__file__), "default.spec")


def init_buildozer(temp_dir, target, options=None):
    """
    Create a buildozer.spec file in the temporary directory and init the
    Buildozer instance.

    The optional argument can be used to overwrite the config options in
    the buildozer.spec file, e.g.:

        init_buildozer({'title': 'Test App'})

    will replace line 4 of the default spec file.
    """
    if options is None:
        options = {}

    spec_path = os.path.join(temp_dir.name, "buildozer.spec")

    with open(default_specfile_path()) as f:
        default_spec = f.readlines()

    spec = []
    for line in default_spec:
        if line.strip():
            match = re.search(r"[#\s]?([0-9a-z_.]+)", line)
            key = match and match.group(1)
            if key in options:
                line = "{} = {}\n".format(key, options[key])

        spec.append(line)

    with open(spec_path, "w") as f:
        f.writelines(spec)

    return Buildozer(filename=spec_path, target=target)
