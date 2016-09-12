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

If you target Android, you must install at least Cython, few build libs, and a
Java SDK. Some binaries of the Android SDK are still in 32 bits, so you need
few 32bits libraries available::

Android on Ubuntu 16.04 (64bit)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    sudo pip install --upgrade cython==0.21
    sudo dpkg --add-architecture i386
    sudo apt-get update
    sudo apt-get install build-essential ccache git libncurses5:i386 libstdc++6:i386 libgtk2.0-0:i386 libpangox-1.0-0:i386 libpangoxft-1.0-0:i386 libidn11:i386 python2.7 python2.7-dev openjdk-8-jdk unzip zlib1g-dev zlib1g:i386 

Android on Ubuntu 15.10 (64bit)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    sudo pip install --upgrade cython==0.21
    sudo dpkg --add-architecture i386
    sudo apt-get update
    sudo apt-get install build-essential ccache git libncurses5:i386 libstdc++6:i386 libgtk2.0-0:i386 libpangox-1.0-0:i386 libpangoxft-1.0-0:i386 libidn11:i386 python2.7 python2.7-dev openjdk-7-jdk unzip zlib1g-dev zlib1g:i386 

Android on Ubuntu 14.10 (64bit)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    sudo pip install --upgrade cython==0.21
    sudo dpkg --add-architecture i386
    sudo apt-get update
    sudo apt-get install build-essential ccache git lib32stdc++6 lib32z1 lib32z1-dev python2.7 python2.7-dev openjdk-7-jdk unzip zlib1g-dev zlib1g:i386

Android on Ubuntu 13.10 (64bit)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    sudo pip install --upgrade cython==0.21
    sudo dpkg --add-architecture i386
    sudo apt-get update
    sudo apt-get install build-essential ccache git lib32z1 lib32bz2-1.0 libncurses5:i386 libstdc++6:i386 python2.7 python2.7-dev openjdk-7-jdk unzip zlib1g-dev zlib1g:i386

Android on Ubuntu 12.04 (64bit)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    sudo pip install --upgrade cython==0.21
    sudo apt-get install build-essential ccache git lib32z1 lib32bz2-1.0 libncurses5:i386 libstdc++6:i386 python2.7 python2.7-dev openjdk-7-jdk unzip zlib1g-dev zlib1g:i386
