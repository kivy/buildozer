# This .spec config file tells Buildozer an app's requirements for being built.
#
# It largely follows the syntax of an .ini file.
# See the end of the file for more details and warnings about common mistakes.

[app]

# (str) Title of your application
title = My Application

# (str) Package name
package.name = myapp

# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (leave empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (leave empty to not exclude anything)
#source.exclude_exts = spec

# (list) List of directory to exclude (leave empty to not exclude anything)
#source.exclude_dirs = tests, bin, venv

# (list) List of exclusions using pattern matching
# Do not prefix with './'
#source.exclude_patterns = license,images/*/*.jpg

# (str) Application versioning (method 1)
version = 0.1

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy

# (str) Custom source folders for requirements
# Sets custom source for any requirements with recipes
# requirements.source.kivy = ../../kivy

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (bool) Indicate if the application should be fullscreen or not
#fullscreen = False


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
# bin_dir = ./bin

#-----------------------------------------------------------------------------
#   Notes about using this file:
#
#   Buildozer uses a variant of Python's ConfigSpec to read this file.
#   For the basic syntax, including interpolations, see
#       https://docs.python.org/3/library/configparser.html#supported-ini-file-structure
#
#   Warning: Comments cannot be used "inline" - i.e.
#       [app]
#       title = My Application # This is not a comment, it is part of the title.
#
#   Warning: Indented text is treated as a multiline string - i.e.
#       [app]
#       title = My Application
#          package.name = myapp # This is all part of the title.
#
#   Buildozer's .spec files have some additional features:
#
#   Buildozer supports lists - i.e.
#       [app]
#       source.include_exts = py,png,jpg
#       #                     ^ This is a list.
#
#       [app:source.include_exts]
#       py
#       png
#       jpg
#       # ^ This is an alternative syntax for a list.
#
#   Buildozer's option names are case-sensitive, unlike most .ini files.
#
#   Buildozer supports overriding options through environment variables.
#   Name an environment variable as SECTION_OPTION to override a value in a .spec
#   file.
#
#   Buildozer support overriding options through profiles.
#   For example, you want to deploy a demo version of your application without
#   HD content. You could first change the title to add "(demo)" in the name
#   and extend the excluded directories to remove the HD content.
#
#       [app@demo]
#       title = My Application (demo)
#
#       [app:source.exclude_patterns@demo]
#       images/hd/*
#
#   Then, invoke the command line with the "demo" profile:
#
#        buildozer --profile demo android debug
#
#   Environment variable overrides have priority over profile overrides.
#
#   For more platform specific configuration please run one of the following commands
#   so this file will be updated accordingly:
#       buildozer init android
#       buildozer init android --no-comments
#       buildozer init ios
#       buildozer init ios --no-docs
#       buildozer init osx