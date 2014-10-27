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
      setdefault         Set the default command to do when no arguments are given
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

