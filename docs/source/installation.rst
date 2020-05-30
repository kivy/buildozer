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

Android on Ubuntu 20.04 (64bit)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(expected to work as well in later version, but only regularly tested in the latest LTS)

::

    sudo apt update
    sudo apt install -y git zip unzip openjdk-8-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
    pip3 install --user --upgrade Cython==0.29.19 virtualenv  # the --user should be removed if you do this in a venv

    # add the following line at the end of your ~/.bashrc file
    export PATH=$PATH:~/.local/bin/


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
~~~~~~~~~~~~~

Install XCode and command line tools (through the AppStore)


Install homebrew (https://brew.sh)

::

    brew install pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer autoconf automake


Install pip and virtualenv

::

    python3 -m pip install --user --upgrade pip virtualenv kivy-ios
