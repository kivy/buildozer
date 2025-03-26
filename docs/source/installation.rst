Installation
============

Buildozer can be installed on Linux or Macos, Windows users must install WSL to use Linux. 
Target platforms are Android and iOS, iOS is only available for MacOS installs. 
After Buildozer installation read the Quickstart documentation.

This page contains install instructions for targeting Android or iOS. The Android section contains instructions 
for installing Buildozer on Ubuntu or on MacOS, also there are special notes for WSL users. Other Linux OS can 
be used (for example Colab) but there are no instructions. The iOS section 
contains instructions for installing kivy-ios on MacOS.

Buildozer is tested on Python 3.8 and above. 

Targeting Android
-----------------

Install on Ubuntu 24.04
~~~~~~~~~~~~~~~~~~~~~~~

Install the system packages on which a Buildozer build may depend::

    sudo apt update
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

to ~/.bashrc, and to open a new shell. The leading period in the line above above is important.

Activate an existing Python virtual environment, or create and activate a new Python virtual environment. 
Python 3.12 defaults to requiring a virtual environment::

    cd
    virtualenv venv
    source venv/bin/activate

Install Buildozer and it's required Python packages::

    pip install buildozer, setuptools, cython==0.29.34


Install on Ubuntu 20.04 and 22.04 (64bit)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install the system packages on which a Buildozer build may depend::

    sudo apt update
    sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool \
    pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev \
    libssl-dev automake

    # add the following line at the end of your ~/.bashrc file
    export PATH=$PATH:~/.local/bin/
    
If `openjdk-17 <https://openjdk.org/projects/jdk/17/>`_ is not compatible with other installed programs,
for Buildozer the minimum compatible openjdk version is 11.

Then install the buildozer project with::

    pip3 install --user --upgrade buildozer

Notes for WSL users
~~~~~~~~~~~~~~~~~~~

Legacy WSL1 users must upgrade to WSL2. WSL1 has a known fatal issue.

Copy your Kivy project directory from the Windows file system (usually under /mnt/c) to the WSL file system (under ~).

It is important to build on the WSL file system. Builds are about 5 times faster than the Windows file system, 
and using an NTFS formatted disk on a Linux system may cause some Python packages to incorrectly behave as if they are 
configured for Windows.

For debugging, WSL does not have direct access to USB. Copy the .apk file to the Windows partition and run ADB
(Android Debug Bridge) from a Windows prompt. ADB is part of Android Studio, if you do not have this installed
you can install just the platform tools which also contain ADB.

- Visit the `Android SDK Platform Tools <https://developer.android.com/tools/releases/platform-tools>`_ page, and
  select "Download SDK Platform-Tools for Windows".

- Unzip the downloaded file to a new folder. For example, `C:\\platform-tools\\`


Install on macOS
~~~~~~~~~~~~~~~~

Additional installation required to support macOS::

    python3 -m pip install --user --upgrade buildozer # the --user should be removed if you do this in a venv


Install TroubleShooting
~~~~~~~~~~~~~~~~~~~~~~~

Aidl not found, please install it.
""""""""""""""""""""""""""""""""""

Delete "~/.buildozer" and run buildozer again. You must type 'y' to accept each Google license agreement.

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

