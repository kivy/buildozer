#!/bin/bash -eux

wget http://bootstrap.pypa.io/get-pip.py
python get-pip.py
rm get-pip.py

apt-get -y install lib32z1 lib32ncurses5
apt-get -y install build-essential
apt-get -y install git openjdk-9-jdk --no-install-recommends zlib1g-dev
pip install cython buildozer python-for-android
