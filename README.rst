Buildozer
=========

.. image:: https://travis-ci.com/kivy/buildozer.svg?branch=master
       :target: https://travis-ci.com/kivy/buildozer

Buildozer is a tool for creating application packages easily.

The goal is to have one "buildozer.spec" file in your app directory, describing
your application requirements and settings such as title, icon, included modules
etc. Buildozer will use that spec to create a package for Android, iOS, Windows,
OSX and/or Linux.

Buildozer currently supports packaging for Android via the `python-for-android
<http://github.com/kivy/python-for-android/>`_
project, and for iOS via the kivy-ios project. iOS and OSX are still under work.

For Android: please have a look at `Android-SDK-NDK-Information
<https://github.com/kivy/kivy/wiki/Android-SDK-NDK-Information>`_. Please note that
the default SDK/NDK coded in Buildozer works for target Python 2.
For target Python 3, use appropriate SDK/NDK as per the documentation, and ensure you
have `python3` in your requirements.
You can still use Crystax Python 3, see `Installing Buildozer with target Python 3
(CrystaX) <#installing-buildozer-with-target-python-3-crystax>`_.
For host Python, both versions are seamlessly supported.

We provide a ready-to-use `Virtual Machine for Virtualbox <https://kivy.org/#download>`_.

Note that this tool has nothing to do with the eponymous online build service
`buildozer.io <http://buildozer.io />`_.

Installing Buildozer with target Python 3 (default):
----------------------------------------------------

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

#. Go into your application directory and run::

    buildozer init
    # edit the buildozer.spec, then
    buildozer android debug deploy run

Installing Buildozer with target Python 2:
-----------------------------------------

#. Follow the same installation and buildozer init as Python 3

#. Make sure the following lines are in your buildozer.spec file.::

    # Changes python3 to python2
    requirements = python2,kivy

#. Finally, build, deploy and run the app on your phone::

    buildozer android debug deploy run
    
    
Installing Buildozer with target Python 3 (CrystaX, deprecated):
----------------------------------------------------------------

After following the steps above to install buildozer and generate the default spec file,
you need to setup Crystax NDK as described below.

#. Download and extract the Crystax NDK somewhere (~/.buildozer/crystax-ndk is one option): https://www.crystax.net/en/download

#. Make sure the following lines are in your buildozer.spec file.::

    # Require python3crystax:
    requirements = python3crystax,kivy

    # Point to the directory where you extracted the crystax-ndk:
    android.ndk_path = <Your install path here.  Use ~ for home DIR>

#. Finally, build, deploy and run the app on your phone::

    buildozer android debug deploy run



Buildozer Docker image
----------------------

A Dockerfile is available to use buildozer through a Docker environment.

#. Build with::

    docker build --tag=buildozer .

#. Run with::

    docker run --volume "$(pwd)":/home/user/hostcwd buildozer --version


Examples of Buildozer commands:
--------------------------------

::

    # buildozer target command
    buildozer android clean
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

    Usage:
        buildozer [--profile <name>] [--verbose] [target] <command>...
        buildozer --version

    Available targets:
      android        Android target, based on python-for-android project
      ios            iOS target, based on kivy-ios project
      android_old    Android target, based on python-for-android project (old toolchain)

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

    Target "android_old" commands:
      adb                Run adb from the Android SDK. Args must come after --, or
                         use --alias to make an alias
      logcat             Show the log from the device

    Target "ios" commands:
      list_identities    List the available identities to use for signing.
      xcode              Open the xcode project.

    Target "android" commands:
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
- ``p4a.source_dir`` -> ``$APP_P4A_SOURCE_DIR``

Buildozer Virtual Machine
-------------------------

The current virtual machine (available via https://kivy.org/downloads/) allow
you to have a ready to use vm for building android application.

Using shared folders
++++++++++++++++++++

If the Virtualbox Guest tools are outdated, install the latest one:

- in the Virtualbox: `Devices` -> `Install Guest Additions CD images`
- in the guest/linux: Go to the cdrom and run the installer
- reboot the vm

VirtualBox filesystem doesn't support symlink anymore (don't
try the setextradata solution, it doesn't work.). So you must
do the build outside the shared folder. One solution:

- `sudo mkdir /build`
- `sudo chown kivy /build`
- In your buildozer.spec, section `[buildozer]`, set `build_dir = /build/buildozer-myapp`

Using your devices via the VM
+++++++++++++++++++++++++++++

There is a little icon on the bottom left that represent an USB plug.
Select it, and select your android device on it. Then you can check:

- `buildozer android adb -- devices`

If it doesn't, use Google. They are so many differents way / issues
depending your phone that Google will be your only source of
information, not us :)

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
