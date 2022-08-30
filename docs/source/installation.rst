
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

Android on Ubuntu 20.04 and 22.04 (64bit)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(expected to work as well in later version, but only regularly tested in the latest LTS)

::

    sudo apt update
    sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
    pip3 install --user --upgrade Cython==0.29.19 virtualenv  # the --user should be removed if you do this in a venv

    # add the following line at the end of your ~/.bashrc file
    export PATH=$PATH:~/.local/bin/
    
If openjdk-17 is not compatible with other installed programs, for Buildozer the minimum compatible openjdk version is 11. 

Android on Windows 10 or 11
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use buildozer in Windows you need first to enable Windows Subsystem for Linux (WSL) and install a Linux distribution: https://docs.microsoft.com/en-us/windows/wsl/install.

These instructions were tested with WSL 1 and Ubuntu 18.04 LTS, and WSL2 with Ubuntu 20.04 and 22.04. 

After installing WSL and Ubuntu on your Windows machine, open Ubuntu, run the commands listed in the previous section, and restart your WSL terminal to enable the path change.

Copy your Kivy project directory from the Windows partition to the WSL partition, and follow the Quickstart Instructions. **Do not** change to the project directory on the Windows partition and build there, this may give unexpected and obscure fails. 

For debugging, WSL does not have direct access to USB. Copy the .apk file to the Windows partition and run ADB (Android Debug Bridge) from a Windows prompt. ADB is part of Android Studio, if you do not have this installed you can install just the platform tools which also contain ADB. 

- Go to https://developer.android.com/studio/releases/platform-tools and click on "Download SDK Platform-Tools for Windows".

- Unzip the downloaded file to a new folder. For example, "C:\\platform-tools".

Before Using Buildozer
~~~~~~~~~~~~~~~~~~~~~~

If you wish, clone your code to a new folder, where the build process will run.

You don't need to create a virtualenv for your code requirements. But just add these requirements to a configuration file called buildozer.spec as you will see in the following sections.

Before running buildozer in your code folder, remember to go into the buildozer folder and activate the buildozer virtualenv.

Android on macOS
~~~~~~~~~~~~~~~~

::

    brew install openssl
    sudo ln -sfn /usr/local/opt/openssl /usr/local/ssl
    brew install pkg-config autoconf automake
    python3 -m pip install --user --upgrade Cython==0.29.19 virtualenv  # the --user should be removed if you do this in a venv

    # add the following line at the end of your `~/.bashrc` file
    export PATH=$PATH:~/Library/Python/3.7/bin


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
-------------

Install XCode and command line tools (through the AppStore)


Install homebrew (https://brew.sh)

::

    brew install pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer autoconf automake


Install pip and virtualenv

::

    python3 -m pip install --user --upgrade pip virtualenv kivy-ios
