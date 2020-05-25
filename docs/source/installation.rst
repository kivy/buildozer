Installation
============

Buildozer itself doesn't depend on any library Python >= 3.3.
Depending the platform you want to target, you might need more tools installed.
Buildozer tries to give you hints or tries to install few things for
you, but it doesn't cover every situation.

First, install the buildozer project with::

    pip3 install --user --upgrade buildozer

Targeting Android
-----------------

Android on Ubuntu 18.04 (64bit)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(expected to work as well in later version, but only regularly tested in the latest LTS)

::

    sudo apt update
    sudo apt install -y git zip unzip openjdk-8-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
    pip3 install --user --upgrade cython virtualenv  # the --user should be removed if you do this in a venv

    # add the following line at the end of your ~/.bashrc file
    export PATH=$PATH:~/.local/bin/

Android on Windows 10
~~~~~~~~~~~~~~~~~~~~~

To use buildozer in Windows 10 you need first to enable Windows Subsystem for Linux (WSL) and install a Linux distribution: https://docs.microsoft.com/en-us/windows/wsl/install-win10.

These instructions were tested with WSL 1 and Ubuntu 18.04 LTS. 

With WSL and Ubuntu installed on your Windows 10 machine, open Ubuntu and run these commands:

::

    sudo apt update
    sudo apt install -y git zip unzip openjdk-8-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
    # Use here the python version you need
    sudo apt install -y python3.7-venv
    # Create a folder for buildozer
    mkdir /mnt/c/buildozer
    cd /mnt/c/buildozer
    python3.7 -m venv venv-buildozer
    source venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install --upgrade wheel
    python -m pip install --upgrade cython 
    python -m pip install --upgrade virtualenv 
    python -m pip install --upgrade buildozer
    # Add the following line at the end of your ~/.bashrc file
    export PATH=$PATH:~/.local/bin/
    # Restart your WSL terminal to enable the path change

Now you need to install the Windows version of ADB (Android Debug Bridge):

- Go to https://developer.android.com/studio/releases/platform-tools and click on "Download SDK Platform-Tools for Windows".

- Unzip the downloaded file to a new folder. For example, "C:\\platform-tools".

Before Using Buildozer
----------------------

If you wish, clone your code to a new folder, where the build process will run. You don't need to create a virtualenv for your code requirements. But just add these requirements to a configuration file called buildozer.spec as you will see in the following sections.

Before running buildozer in your code folder, remember to go into the buildozer folder and activate the buildozer virtualenv.

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


python-for-android related errors
"""""""""""""""""""""""""""""""""
See the dedicated `p4a troubleshooting documentation
<https://python-for-android.readthedocs.io/en/latest/troubleshooting/>`_.


Targeting IOS
~~~~~~~~~~~~~

Install XCode and command line tools (through the AppStore)


Install homebrew (https://brew.sh)

::

    brew install pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer autoconf automake


Install pip and virtualenv

::

    python -m pip install --user --upgrade pip virtualenv kivy-ios
