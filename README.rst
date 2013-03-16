Buildozer
=========

This tool is currently in alpha.

Buildozer is a tool for creating application packages easily.

The goal is to have one "buildozer.spec" file in your app directory: it
describe your application requirements, titles, etc.  Buildozer will use that
spec for create package for Android, iOS, Windows, OSX and Linux.

Usage example
-------------

#. Install buildozer::

    # latest dev
    git clone git://github.com/kivy/buildozer
    cd buildozer
    sudo python2.7 setup.py install

    # via pip (latest stable)
    sudo pip install buildozer

    # via easy_install
    sudo easy_install buildozer

#. Go into your application directory and do::

    buildozer init
    # edit the buildozer.spec, then
    buildozer android debug deploy run

Example of commands::

    # buildozer commands
    buildozer clean

    # buildozer target command
    buildozer android update
    buildozer android deploy
    buildozer android debug
    buildozer android release

    # or all in one (compile in debug, deploy on device)
    buildozer android debug deploy

    # set the default command if nothing set
    buildozer setdefault android debug deploy run


Usage
-----

::

    Usage: buildozer [--verbose] [target] [command1] [command2]

    Available targets:
      android            Android target, based on python-for-android project
      ios                iOS target, based on kivy-ios project. (not working yet.)

    Global commands (without target):
      clean              Clean the whole Buildozer environment.
      help               Show the Buildozer help.
      init               Create a initial buildozer.spec in the current directory
      setdefault         Set the default command to do when to arguments are given
      version            Show the Buildozer version

    Target commands:
      clean              Clean the target environment
      update             Update the target dependencies
      debug              Build the application in debug mode
      release            Build the application in release mode
      deploy             Deploy the application on the device
      run                Run the application on the device



buildozer.spec
--------------

See `buildozer/default.spec <https://raw.github.com/kivy/buildozer/master/buildozer/default.spec>`_ for an up-to-date spec file.

