Installation
============

Buildozer is tested on Python 3.8 and above.
Depending the platform you want to target, you might need more tools installed.
Buildozer tries to give you hints or tries to install few things for
you, but it doesn't cover every situation.

First, install the buildozer project.

The most-recently released version can be installed with::

    pip install --user --upgrade buildozer

Add the `--user` option if you are not using a virtual environment (not recommended).

If you would like to install the latest version still under development::

    pip install https://github.com/kivy/buildozer/archive/master.zip


Targeting Android
-----------------

Android on Ubuntu 20.04 and 22.04 (64bit)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
  Later versions of Ubuntu are expected to work. However only the latest
  `Long Term Support (LTS) release <https://ubuntu.com/about/release-cycle>`_
  is regularly tested.

Additional installation required to support Android::

    sudo apt update
    sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev automake

    # add the following line at the end of your ~/.bashrc file
    export PATH=$PATH:~/.local/bin/
    
If `openjdk-17 <https://openjdk.org/projects/jdk/17/>`_ is not compatible with other installed programs,
for Buildozer the minimum compatible openjdk version is 11.

Then install the buildozer project with::

    pip3 install --user --upgrade buildozer


Android on Windows 10 or 11
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use Buildozer on Windows, you need first to enable Windows Subsystem for Linux (WSL) and
`install a Linux distribution <https://docs.microsoft.com/en-us/windows/wsl/install>`_.

These instructions were tested with WSL 1 and Ubuntu 18.04 LTS, and WSL2 with Ubuntu 20.04 and 22.04.

After installing WSL and Ubuntu on your Windows machine, open Ubuntu, run the commands listed in the previous section,
and restart your WSL terminal to enable the path change.

Copy your Kivy project directory from the Windows partition to the WSL partition.

.. warning::
    It is important to use the WSL partition. The Android SDK for Linux does not work on Windows' NTFS drives.
    This will lead to obscure failures.

For debugging, WSL does not have direct access to USB. Copy the .apk file to the Windows partition and run ADB
(Android Debug Bridge) from a Windows prompt. ADB is part of Android Studio, if you do not have this installed
you can install just the platform tools which also contain ADB.

- Visit the `Android SDK Platform Tools <https://developer.android.com/tools/releases/platform-tools>`_ page, and
  select "Download SDK Platform-Tools for Windows".

- Unzip the downloaded file to a new folder. For example, `C:\\platform-tools\\`

Before Using Buildozer
~~~~~~~~~~~~~~~~~~~~~~

If you wish, clone your code to a new folder where the build process will run.

You don't need to create a virtualenv for your code requirements. But just add these requirements to a configuration
file called `buildozer.spec` as you will see in the following sections.

Before running Buildozer in your code folder, remember to go into the Buildozer folder and activate the Buildozer
virtualenv.

Android on macOS
~~~~~~~~~~~~~~~~

Additional installation required to support macOS::

    python3 -m pip install --user --upgrade buildozer # the --user should be removed if you do this in a venv


TroubleShooting
~~~~~~~~~~~~~~~

Buildozer stuck on "Installing/updating SDK platform tools if necessary"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Press "y" then enter to continue, the license acceptance system is silently waiting for your input


Aidl not found, please install it.
""""""""""""""""""""""""""""""""""

Buildozer didn't install a necessary package

::

    ~/.buildozer/android/platform/android-sdk/tools/bin/sdkmanager "build-tools;29.0.0"

Then press "y" then enter to accept the license.

Alternatively, the Android SDK license can be automatically accepted - see `build.spec` for details.


python-for-android related errors
"""""""""""""""""""""""""""""""""
See the dedicated `p4a troubleshooting documentation
<https://python-for-android.readthedocs.io/en/latest/troubleshooting/>`_.


Targeting IOS
-------------

Additional installation required to support iOS:

* Install XCode and command line tools (through the AppStore)
* Install `Homebrew <https://brew.sh>`_::

    brew install pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer autoconf automake

* Install pip, virtualenv and Kivy for iOS::

    python -m pip install --user --upgrade pip virtualenv kivy-ios

