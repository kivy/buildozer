#!/bin/bash -eux

wget http://bootstrap.pypa.io/get-pip.py
python get-pip.py
rm get-pip.py
apt-get -y install git openjdk-7-jdk --no-install-recommends zlib1g-dev
pip install cython buildozer
