Buildozer
=========

THIS IS A WORK IN PROGRESS, DO NOT USE.

Buildozer is a tool for creating application packages easilly.

The goal is to have one "buildozer.spec" file in your app directory: it
describe your application requirements, titles, etc.  Buildozer will use that
spec for create package for Android, iOS, Windows, OSX and Linux.

Usage example
-------------

#. Add buildozer repo into your PYTHONPATH.
#. Go into your application directory and do::

    buildozer.py init
    # edit the buildozer.spec, then
    buildozer.py android build

Example of commands::

    # buildozer commands
    buildozer.py clean

    # buildozer target command
    buildozer.py android update
    buildozer.py android install
    buildozer.py android debug
    buildozer.py android release

    # or all in one (compile in debug, install on device)
    buildozer.py android debug install

    # set the default command if nothing set
    buildozer.py setdefault android debug install


Usage
-----

::

    Usage: buildozer [target] [command1] [command2]

    Available targets:
      android
        Android target, based on python-for-android project
      ios
        iOS target, based on kivy-ios project. (not working yet.)

    Global commands (without target):
      clean
        Clean the whole Buildozer environment.
      help
        Show the Buildozer help.
      init
        Create a initial buildozer.spec in the current directory
      setdefault
        Set the default command to do when to arguments are given

    Target commands:
      clean
        Clean the target environment
      update
        Update the target dependencies
      debug
        Build the application in debug mode
      release
        Build the application in release mode
      deploy
        Install the application on the device
      run
        Run the application on the device



buildozer.spec
--------------

See buildozer/default.spec for an up-to-date spec file.

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

    # (str) Android entry point, default is ok for Kivy-based app
    #android.entrypoint = org.renpy.android.PythonActivity

