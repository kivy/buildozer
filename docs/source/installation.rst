Installation
============

Buildozer is tested on Python 3.8 and above.
Depending the platform you want to target, you might need more tools installed.
Buildozer tries to give you hints or tries to install few things for
you, but it doesn't cover every situation.

Buildozer runs on Linux and Macos, Windows users must install WSL to use Linux.

Targeting Android
-----------------

Android on Ubuntu 24.04
~~~~~~~~~~~~~~~~~~~~~~~

Install the system packages on which a Buildozer build may depend::

    sudo apt install -y git zip unzip openjdk-17-jdk python3-pip \
    python3-virtualenv autoconf libtool pkg-config zlib1g-dev \
    libncurses5-dev libncursesw5-dev libtinfo6 cmake libffi-dev \
    libssl-dev automake autopoint gettext

If there are multiple versions of Java installed, select `*17-openjdk*` using::

    sudo update-alternatives --config java
    sudo update-alternatives --config javac

Install Rust, and accept the default option::

    curl https://sh.rustup.rs -sSf | sh

Note that the Rust on-screen instructions specify to add::

    . "$HOME/.cargo/env"

to ~/.bashrc, and to open a new shell.

Activate an existing Python virtual environment, or create and activate a new Python virtual environment. This is a Python 3.12 requirement::

    virtualenv venv
    source venv/bin/activate

Install Buildozer and it's required Python packages::

    pip install buildozer, setuptools, cython==0.29.34


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

Buildozer on Windows 10 or 11
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use Buildozer on Windows, you need first to enable Windows Subsystem for Linux (WSL) and
`install a Linux distribution <https://docs.microsoft.com/en-us/windows/wsl/install>`_.

These instructions were tested with WSL2 with Ubuntu 20.04, 22.04, and 24.04. WSL1 has a known fatal issue.

After installing WSL and Ubuntu on your Windows machine, open Ubuntu, follow the instructions above,
and restart your WSL terminal to enable the path change.

Copy your Kivy project directory from the Windows partition (under /mnt/c) to the WSL partition (under ~).

It is important to use the WSL partition. Builds are about 5 times faster than the Windows partition, and using an NTFS partition on a Linux system may lead to obscure Python issues.

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
<https://python-for-android.readthedocs.io/en/latest/troubleshooting.html>`_.


Targeting IOS
-------------

Additional installation required to support iOS:

* Install XCode and command line tools (through the AppStore)
* Install `Homebrew <https://brew.sh>`_::

    brew install pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer autoconf automake

* Install pip, virtualenv and Kivy for iOS::

    python -m pip install --user --upgrade pip virtualenv kivy-ios

