# Dockerfile for providing buildozer
# Build with:
# docker build --tag=buildozer .
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
    PATH="${HOME_DIR}/.local/bin:${PATH}"

# configures locale
RUN apt update -qq > /dev/null && \
    apt install -qq --yes --no-install-recommends \
    locales && \
    locale-gen en_US.UTF-8 && \
    apt install -qq --yes mc openssh-client nano wget curl pkg-config autoconf automake libtool
ENV LANG="en_US.UTF-8" \
    LANGUAGE="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8"

# installs system dependencies (required to setup all the tools)
RUN apt install -qq --yes --no-install-recommends \
    sudo python-pip python-setuptools file

# https://buildozer.readthedocs.io/en/latest/installation.html#android-on-ubuntu-18-04-64bit
RUN dpkg --add-architecture i386 && apt update -qq > /dev/null && \
        apt install -qq --yes --no-install-recommends \
        build-essential ccache git libncurses5:i386 libstdc++6:i386 libgtk2.0-0:i386 \
        libpangox-1.0-0:i386 libpangoxft-1.0-0:i386 libidn11:i386 python2.7 \
        python2.7-dev openjdk-8-jdk unzip zlib1g-dev zlib1g:i386 python3 python3-dev time \
     && apt install -qq --yes python3-virtualenv python3-pip

# prepares non root env
RUN useradd --create-home --shell /bin/bash ${USER}
# with sudo access and no password
RUN usermod -append --groups sudo ${USER}
RUN echo "%sudo ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

WORKDIR ${WORK_DIR}

#COPY . .

#RUN chown user /home/user/ -Rv

USER ${USER}

# Crystax-NDK
ARG CRYSTAX_NDK_VERSION=10.3.2
ARG CRYSTAX_HASH=7305b59a3cee178a58eeee86fe78ad7bef7060c6d22cdb027e8d68157356c4c0
ARG cachebuildozerver=0.34
ARG cachebuildozersha=40b94a55aad8056a8298ad83b650ad3af3cb98e96642dc31a207161ecadac391
ARG cachebuildozerfile=cachebuildozer034.tar.gz

# installs buildozer and dependencies
RUN pip install --user Cython==0.25.2 appdirs buildozer==0.34 sh
# calling buildozer adb command should trigger SDK/NDK first install and update
# but it requires a buildozer.spec file
RUN cd /tmp/ && buildozer init && buildozer android adb -- version \
    # fix https://github.com/kivy/buildozer/issues/751
    && cd ~/.buildozer/android/platform/&& rm -vf android-ndk*.tar* android-sdk*.tgz apache-ant*.tar.gz \
    && cd - && cd ${WORK_DIR} \
    && set -ex \
  && wget https://www.crystax.net/download/crystax-ndk-${CRYSTAX_NDK_VERSION}-linux-x86_64.tar.xz?interactive=true -O ~/.buildozer/crystax-${CRYSTAX_NDK_VERSION}.tar.xz \
  && cd ~/.buildozer/ \
  && echo "${CRYSTAX_HASH}  crystax-${CRYSTAX_NDK_VERSION}.tar.xz" | sha256sum -c \
  && time tar -xf crystax-${CRYSTAX_NDK_VERSION}.tar.xz && rm ~/.buildozer/crystax-${CRYSTAX_NDK_VERSION}.tar.xz \
  && cd ~ && sudo wget --quiet https://github.com/homdx/buildozer/releases/download/${cachebuildozerver}/${cachebuildozerfile} \
  && echo "${cachebuildozersha}  ${cachebuildozerfile}" | sha256sum -c \
  && sudo chown user ${cachebuildozerfile} && sudo chown user ${WORK_DIR} -R \
  && cd ${WORK_DIR} && echo tar -xf /home/user/cachebuildozer034.tar.gz >cachebuildozer034.sh && chmod +x cachebuildozer034.sh && sudo mv -v cachebuildozer034.sh /bin

#COPY . app

#RUN sudo chown user ${WORK_DIR}/app -Rv

#USER ${USER}

#RUN cd ${WORK_DIR}/app && tar -xf /home/user/${cachebuildozerfile} && buildozer android debug || echo fix apk

CMD tail -f /var/log/faillog

#ENTRYPOINT ["buildozer"]
