Installation
============

Buildozer itself doesn't depend on any library, and works on Python 2.7 and >=
3.3. Depending the platform you'll target, you might need more tools installed.
Buildozer tries to give you hints or try to install few things for you, but it
doesn't cover all the cases.

First, install the buildozer project with::

    pip install --upgrade buildozer

If you target Android, you must install at least Cython, few build libs, a Java
SDK. Some binaries of the Android SDK are still in 32 bits, so you need few
32bits libraries available::

    pip install --upgrade cython
    apt-get install ccache build-essential lib32stdc++6 libz1g-dev openjdk-7-jdk
