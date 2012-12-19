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

    # (str) Title of your application
    title = My Application

    # (str) Package name
    package.name = myapp

    # (str) Package domain (needed for android/ios packaging)
    package.domain = org.test

    # (str) Source code where the main.py live
    source.dir = .

    # (list) Source files to include (let empty to include all the files)
    source.include_exts = py,png,jpg

    # (list) Source files to exclude (let empty to not excluding anything)
    #source.exclude_exts = spec

    # (str) Application versionning (method 1)
    version.regex = __version__ = '(.*)'
    version.filename = %(source.dir)s/main.py

    # (str) Application versionning (method 2)
    # version = 1.2.0

    # (list) Application requirements
    requirements = twisted,kivy

    #
    # Android specific
    #

    # (list) Permissions
    #android.permissions = INTERNET

    # (int) Minimum SDK allowed for installation
    #android.minsdk = 8

    # (int) Android SDK to use
    #android.sdk = 16

