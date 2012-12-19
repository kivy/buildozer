Buildozer
=========

THIS IS A WORK IN PROGRESS, DO NOT USE.

Buildozer is a tool for creating application packages easilly.

The goal is to have one "buildozer.spec" file in your app directory: it
describe your application requirements, titles, etc.  Buildozer will use that
spec for create package for Android, iOS, Windows, OSX and Linux.

Usage
-----

#. Add buildozer repo into your PYTHONPATH.
#. Create a .spec
#. Go into your application directory and do::

    buildozer.py -t android

buildozer.spec
--------------

::

    [app]

    # Title of your application
    title = My Application

    # Source code where the main.py live
    source.dir = .

    # Source files to include (let empty to include all the files)
    source.include_exts = py,png,jpg

    # Source files to exclude (let empty to not excluding anything)
    #source.exclude_exts = spec

    # Application versionning
    version.regex = __version__ = '(.*)'
    version.filename = %(source.dir)s/main.py

    # Application requirements
    requirements = twisted,kivy

    # Android specific
    android.permissions = INTERNET

