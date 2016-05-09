Buildozer
=========

This tool is currently in alpha.

Buildozer is a tool for creating application packages easily.

The goal is to have one "buildozer.spec" file in your app directory, describing
your application requirements and settings such as title, icon, included modules
etc. Buildozer will use that spec to create a package for Android, iOS, Windows,
OSX and/or Linux.

Buildozer currently supports packaging for Android via the `python-for-android
<http://github.com/kivy/python-for-android/>`_
project, and for iOS via the kivy-ios project. Support for other operating systems
is intended in the future.

Note that this tool has nothing to do with the eponymous online build service
`buildozer.io <http://buildozer.io />`_.

Usage example
-------------

#. Install buildozer::

    # via pip (latest stable, recommended)
    sudo pip install buildozer

    # latest dev version
    sudo pip install https://github.com/kivy/buildozer/archive/master.zip

    # git clone, for working on buildozer
    git clone https://github.com/kivy/buildozer
    cd buildozer
    python setup.py build
    sudo pip install -e .

#. Go into your application directory and do::

    buildozer init
    # edit the buildozer.spec, then
    buildozer android_new debug deploy run

Example of commands::

    # buildozer target command
    buildozer android_new clean
    buildozer android_new update
    buildozer android_new deploy
    buildozer android_new debug
    buildozer android_new release

    # or all in one (compile in debug, deploy on device)
    buildozer android_new debug deploy

    # set the default command if nothing set
    buildozer setdefault android_new debug deploy run


Usage
-----

::

    Usage:
        buildozer [--profile <name>] [--verbose] [target] <command>...
        buildozer --version

    Available targets:
      android            Android target, based on python-for-android project (old toolchain)
      ios                iOS target, based on kivy-ios project
      android_new        Android target, based on python-for-android project (new toolchain)

    Global commands (without target):
      distclean          Clean the whole Buildozer environment.
      help               Show the Buildozer help.
      init               Create a initial buildozer.spec in the current directory
      serve              Serve the bin directory via SimpleHTTPServer
      setdefault         Set the default command to run when no arguments are given
      version            Show the Buildozer version

    Target commands:
      clean      Clean the target environment
      update     Update the target dependencies
      debug      Build the application in debug mode
      release    Build the application in release mode
      deploy     Deploy the application on the device
      run        Run the application on the device
      serve      Serve the bin directory via SimpleHTTPServer

    Target "android" commands:
      adb                Run adb from the Android SDK. Args must come after --, or
                         use --alias to make an alias
      logcat             Show the log from the device

    Target "ios" commands:
      list_identities    List the available identities to use for signing.
      xcode              Open the xcode project.

    Target "android_new" commands:
      adb                Run adb from the Android SDK. Args must come after --, or
                         use --alias to make an alias
      logcat             Show the log from the device
      p4a                Run p4a commands. Args must come after --, or use --alias
                         to make an alias



buildozer.spec
--------------

See `buildozer/default.spec <https://raw.github.com/kivy/buildozer/master/buildozer/default.spec>`_ for an up-to-date spec file.


Default config
--------------

You can override the value of *any* buildozer.spec config token by
setting an appropriate environment variable. These are all of the
form ``$SECTION_TOKEN``, where SECTION is the config file section and
TOKEN is the config token to override. Dots are replaced by
underscores.

For example, here are some config tokens from the [app] section of the
config, along with the environment variables that would override them.

- ``title`` -> ``$APP_TITLE``
- ``package.name`` -> ``$APP_PACKAGE_NAME``
- ``android.p4a_dir`` -> ``$APP_ANDROID_P4A_DIR``

Support
-------

If you need assistance, you can ask for help on our mailing list:

* User Group : https://groups.google.com/group/kivy-users
* Email      : kivy-users@googlegroups.com

We also have an IRC channel:

* Server  : irc.freenode.net
* Port    : 6667, 6697 (SSL only)
* Channel : #kivy

Contributing
------------

We love pull requests and discussing novel ideas. Check out our
`contribution guide <http://kivy.org/docs/contribute.html>`_ and
feel free to improve buildozer.

The following mailing list and IRC channel are used exclusively for
discussions about developing the Kivy framework and its sister projects:

* Dev Group : https://groups.google.com/group/kivy-dev
* Email     : kivy-dev@googlegroups.com

IRC channel:

* Server  : irc.freenode.net
* Port    : 6667, 6697 (SSL only)
* Channel : #kivy-dev

License
-------

Buildozer is released under the terms of the MIT License. Please refer to the
LICENSE file.
