# Dockerfile for providing buildozer
#
# Build with:
# docker build --tag=kivy/buildozer .
#
# Or for macOS using Docker Desktop:
#
# docker buildx build --platform=linux/amd64 -t kivy/buildozer .
#
# In order to give the container access to your current working directory
# it must be mounted using the --volume option.
# Run with (e.g. `buildozer --version`):
# docker run --interactive --tty --rm \
#   --volume "$HOME/.buildozer":/home/user/.buildozer \
#   --volume "$PWD":/home/user/hostcwd \
#   kivy/buildozer --version
#
# Or for interactive shell:
# docker run --interactive --tty --rm \
#   --volume "$HOME/.buildozer":/home/user/.buildozer \
#   --volume "$PWD":/home/user/hostcwd \
#   --entrypoint /bin/bash \
#   kivy/buildozer
#
# If you get a `PermissionError` on `/home/user/.buildozer/cache`,
# try updating the permissions from the host with:
# sudo chown $USER -R ~/.buildozer
# Or simply recreate the directory from the host with:
# rm -rf ~/.buildozer && mkdir ~/.buildozer

FROM ubuntu:24.04

ENV USER="user"
ENV HOME_DIR="/home/${USER}"
ENV WORK_DIR="${HOME_DIR}/hostcwd" \
    SRC_DIR="${HOME_DIR}/src" \
    PATH="${HOME_DIR}/.local/bin:${PATH}"

# configures locale
RUN apt update -qq > /dev/null \
    && DEBIAN_FRONTEND=noninteractive apt install -qq --yes --no-install-recommends \
    locales && \
    locale-gen en_US.UTF-8
ENV LANG="en_US.UTF-8" \
    LANGUAGE="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8"

# system requirements to build most of the recipes
RUN apt update -qq > /dev/null \
    && DEBIAN_FRONTEND=noninteractive apt install -qq --yes --no-install-recommends \
    autoconf \
    automake \
    build-essential \
    ccache \
    cmake \
    gettext \
    git \
    libffi-dev \
    libltdl-dev \
    libssl-dev \
    libtool \
    openjdk-17-jdk \
    patch \
    pkg-config \
    python3-pip \
    python3-setuptools \
    python3-venv \
    sudo \
    unzip \
    zip \
    zlib1g-dev

# Create home directory and virtual environment
RUN mkdir -p ${HOME_DIR} \
    && python3 -m venv ${HOME_DIR}/.venv

WORKDIR ${WORK_DIR}
COPY . ${SRC_DIR}
COPY --chmod=755 entrypoint.sh /usr/local/bin/entrypoint.sh

# installs buildozer and dependencies from a virtual environment
ENV PATH="${HOME_DIR}/.venv/bin:${PATH}"
RUN pip install --upgrade "Cython<3.0" wheel pip ${SRC_DIR}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
