Installation
============

Buildozer itself doesn't depend on any library, and works on Python 2.7 and >=
3.3. Depending the platform you want to target, you might need more tools
installed. Buildozer tries to give you hints or tries to install few things for
you, but it doesn't cover every situation.

First, install the buildozer project with::

    pip install --upgrade buildozer

Targeting Android
-----------------

Android on Ubuntu 18.04 (64bit)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(expected to work as well in later version, but only regularly tested in the latest LTS)

::

    sudo apt update
    sudo apt install -y git zip unzip openjdk-8-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5
    pip3 install --user --upgrade cython virtualenv  # the --user should be removed if you do this in a venv

    # add the following line at the end of your ~/.bashrc file
    export PATH=$PATH:~/.local/bin/


TroubleShooting
~~~~~~~~~~~~~~~

Buildozer stuck on "Installing/updating SDK platform tools if necessary"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Press "y" then enter to continue, the license acceptance system is silently waiting for your input


Aidl not found, please install it.
""""""""""""""""""""""""""""""""""

Buildozer didn't install a necessary package

::
    ~/.buildozer/android/platform/android-sdk/tools/bin/sdkmanager --install "build-tools;29.0.0"

Then press "y" then enter to accept the license.


Targeting IOS
~~~~~~~~~~~~~

Install XCode and command line tools (through the AppStore)


Install homebrew (https://brew.sh)

::

    brew install pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer autoconf automake


Install pip and virtualenv

::

    python -m pip install --user --upgrade pip virtualenv kivy-ios
