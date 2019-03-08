# Dockerfile for providing buildozer
# Build with:
# docker build --tag=buildozer .
# 
# In order to give the container access to your current working directory
# it must be mounted using the --volume option.
# Run with (e.g. `buildozer --version`):
# docker run --volume "$(pwd)":/home/user/hostcwd buildozer --version
# Or for interactive shell:
# docker run --volume "$(pwd)":/home/user/hostcwd --entrypoint /bin/bash -it --rm buildozer

FROM ubuntu:18.04

ENV USER="user"
ENV HOME_DIR="/home/${USER}"
ENV WORK_DIR="${HOME_DIR}/hostcwd" \
    SRC_DIR="${HOME_DIR}/src" \
    PATH="${HOME_DIR}/.local/bin:${PATH}"

# configures locale
RUN apt update -qq > /dev/null && \
    apt install -qq --yes --no-install-recommends \
    locales && \
    locale-gen en_US.UTF-8
ENV LANG="en_US.UTF-8" \
    LANGUAGE="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8"

# installs system dependencies (required to setup all the tools)
RUN apt install -qq --yes --no-install-recommends \
    sudo python3-pip python3-setuptools file

# https://buildozer.readthedocs.io/en/latest/installation.html#android-on-ubuntu-18-04-64bit
RUN dpkg --add-architecture i386 && apt update -qq > /dev/null && \
	apt install -qq --yes --no-install-recommends \
	build-essential ccache git libncurses5:i386 libstdc++6:i386 libgtk2.0-0:i386 \
	libpangox-1.0-0:i386 libpangoxft-1.0-0:i386 libidn11:i386 python2.7 python3 \
	python3-dev openjdk-8-jdk unzip zlib1g-dev zlib1g:i386

# prepares non root env
RUN useradd --create-home --shell /bin/bash ${USER}
# with sudo access and no password
RUN usermod -append --groups sudo ${USER}
RUN echo "%sudo ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER ${USER}
WORKDIR ${WORK_DIR}
COPY --chown=user:user . ${SRC_DIR}

# installs buildozer and dependencies
RUN pip3 install --user Cython==0.28.6 ${SRC_DIR}

ENTRYPOINT ["buildozer"]
