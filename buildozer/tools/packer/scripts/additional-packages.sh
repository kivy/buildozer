#!/bin/bash -eux
# Don't use openjdk-9, the conf directory is missing, and we get
# an error when using the android sdk:
# "Can't read cryptographic policy directory: unlimited"

wget http://bootstrap.pypa.io/get-pip.py
python get-pip.py
rm get-pip.py

apt-get -y install lib32stdc++6 lib32z1 lib32ncurses5
apt-get -y install build-essential
apt-get -y install git openjdk-8-jdk --no-install-recommends zlib1g-dev
pip install cython buildozer python-for-android
