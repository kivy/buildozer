# Dockerfile for providing buildozer in a rootless container using Podman
#
# Build with:
#  podman build -f podman-rootless/Dockerfile \
#    --tag=docker.io/kivy/buildozer:rootless \
#    .
#
# In order to give the container access to your current working
# directory it must be mounted using the --volume option.  To have the
# unprivileged user mapped to your account so no shennanigans are
# needed, we must use --userns=keep-id.
#
# The shell in the container is started as "user" by default, it you want to run
# something as root ou can start it with --user=root (and use "su user" if needed).
#
# Run with (e.g. `buildozer --version`):
# podman run --interactive --tty --rm \
#   --userns=keep-id \
#   --volume "$HOME/.buildozer":/home/user/.buildozer \
#   --volume "$PWD":/home/user/hostcwd \
#   docker.io/kivy/buildozer:rootless --version
#
# Or for interactive shell:
# docker run --interactive --tty --rm \
#   --userns=keep-id \
#   --volume "$HOME/.buildozer":/home/user/.buildozer \
#   --volume "$PWD":/home/user/hostcwd \
#   --entrypoint /bin/bash \
#   docker.io/kivy/buildozer:rootless
#
# ... after which you'll need to run `. ~/.venv/bin/activate` before launching `buildozer`.

FROM ubuntu:26.04

ENV USER="user"
ENV HOME_DIR="/home/${USER}"
ENV WORK_DIR="${HOME_DIR}/hostcwd" \
    SRC_DIR="${HOME_DIR}/src" \
    PATH="${HOME_DIR}/.local/bin:${PATH}"

# configures locale
RUN apt-get update -qq > /dev/null \
    && DEBIAN_FRONTEND=noninteractive apt-get install -qq --yes --no-install-recommends \
    locales && \
    locale-gen en_US.UTF-8
ENV LANG="en_US.UTF-8" \
    LANGUAGE="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8"

# system requirements to build most of the recipes
RUN apt-get update -qq > /dev/null \
    && DEBIAN_FRONTEND=noninteractive apt-get install -qq --yes --no-install-recommends \
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

RUN <<EOF
# rename default Ubuntu user and its homedir to "user"
set -eux
mv ~ubuntu "${HOME_DIR}"
usermod --login "${USER}" --home "${HOME_DIR}" ubuntu
EOF

RUN DEBIAN_FRONTEND=noninteractive apt-get install -qq --yes --no-install-recommends \
    strace

USER user
WORKDIR ${WORK_DIR}

ADD --chown=$USER . ${SRC_DIR}

RUN <<EOF
# Create virtual environment, installs buildozer and dependencies
set -eux
python3 -m venv ~/.venv
. ~/.venv/bin/activate
pip install --upgrade "Cython<3.0" wheel pip ${SRC_DIR}
EOF

ADD --chmod=755 podman-rootless/entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
