# Buildozer

Buildozer is a development tool for turning  [Python](https://www.python.org/)
applications into binary packages ready for installation on any of a number of
platforms, including mobile devices.

The app developer provides a single "buildozer.spec" file, which describes the
application's requirements and settings, such as title and icons. Buildozer can
then create installable packages for Android, iOS, Windows, macOS and/or Linux.

Buildozer is managed by the [Kivy Team](https://kivy.org/about.html). It relies
on its sibling projects: 
[python-for-android](https://github.com/kivy/python-for-android/) and 
[Kivy for iOS](https://github.com/kivy/kivy-ios/). It has features to make
building apps using the [Kivy framework](https://github.com/kivy/kivy) easier,
but it can be used independently - even with other GUI frameworks.

For Android, buildozer will automatically download and prepare the
build dependencies. For more information, see
[Android SDK NDK Information](https://github.com/kivy/kivy/wiki/Android-SDK-NDK-Information).

> [!NOTE]
> This tool is unrelated to the online build service,
> `buildozer.io`.

[![Backers on Open Collective](https://opencollective.com/kivy/backers/badge.svg)](#backers)
[![Sponsors on Open Collective](https://opencollective.com/kivy/sponsors/badge.svg)](#sponsors)
[![GitHub contributors](https://img.shields.io/github/contributors-anon/kivy/buildozer)](https://github.com/kivy/buildozer/graphs/contributors)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

![PyPI - Version](https://img.shields.io/pypi/v/buildozer)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/buildozer)

[![Tests](https://github.com/kivy/buildozer/workflows/Tests/badge.svg)](https://github.com/kivy/buildozer/actions?query=workflow%3ATests)
[![Android](https://github.com/kivy/buildozer/workflows/Android/badge.svg)](https://github.com/kivy/buildozer/actions?query=workflow%3AAndroid)
[![iOS](https://github.com/kivy/buildozer/workflows/iOS/badge.svg)](https://github.com/kivy/buildozer/actions?query=workflow%3AiOS)
[![Coverage Status](https://coveralls.io/repos/github/kivy/buildozer/badge.svg)](https://coveralls.io/github/kivy/buildozer)


## Installation

Buildozer 

## Installing Buildozer with target Python 3 (default):

Buildozer incorporates a number of technologies, and has a complicated
dependencies, including platform dependencies outside of Python.

This means installation is more than a simple `pip install`; many of our support
requests are related to missing dependencies. 

So, it is important to follow the instructions carefully.

Please see the 
[Installation documentation](https://buildozer.readthedocs.io/en/latest/installation.html)
specific to this version.

## Buildozer Docker image

A Dockerfile is available to use buildozer through a Docker environment.

- Build with:

```bash
docker build --tag=kivy/buildozer .
```

For macOS, build with:

```bash
docker buildx build --platform=linux/amd64 -t kivy/buildozer .
```

- Run with:

```bash
docker run --volume "$(pwd)":/home/user/hostcwd kivy/buildozer --version
```

> [!WARNING]  
> [DockerHub](https://hub.docker.com/) contains an obsolete Docker image for
> Buildozer. It is deprecated. Build your own.

### Example Build with Caching
- Build and keep downloaded SDK and NDK in `~/.buildozer` directory: 

```bash
docker run -v $HOME/.buildozer:/home/user/.buildozer -v $(pwd):/home/user/hostcwd kivy/buildozer android debug
```


## Buildozer GitHub action

Use [ArtemSBulgakov/buildozer-action@v1](https://github.com/ArtemSBulgakov/buildozer-action)
to build your packages automatically on push or pull request.
See [full workflow example](https://github.com/ArtemSBulgakov/buildozer-action#full-workflow).

> [!WARNING]  
> This GitHub action may use an obsolete version of Buildozer; use with caution.

## Usage

```yml
Usage:
    buildozer [--profile <name>] [--verbose] [target] <command>...
    buildozer --version

Available targets:
    android        Android target, based on python-for-android project
    ios            iOS target, based on kivy-ios project

Global commands (without target):
    distclean          Clean the whole Buildozer environment
    help               Show the Buildozer help
    init               Create an initial buildozer.spec in the current directory
    serve              Serve the bin directory via SimpleHTTPServer
    setdefault         Set the default command to run when no arguments are given
    version            Show the Buildozer version

Target commands:
    clean      Clean the target environment
    update     Update the target dependencies
    debug      Build the application in debug mode
    release    Build the application in release mode
    deploy     Deploy the application on the device
    run        Run the application on the device
    serve      Serve the bin directory via SimpleHTTPServer

Target "ios" commands:
    list_identities    List the available identities to use for signing.
    xcode              Open the xcode project.

Target "android" commands:
    adb                Run adb from the Android SDK. Args must come after --, or
                        use --alias to make an alias
    logcat             Show the log from the device
    p4a                Run p4a commands. Args must come after --, or use --alias
                        to make an alias
```

## Examples of Buildozer commands

```bash
# buildozer target command
buildozer android clean
buildozer android update
buildozer android deploy
buildozer android debug
buildozer android release

# or all in one (compile in debug, deploy on device)
buildozer android debug deploy

# set the default command if nothing set
buildozer setdefault android debug deploy run
```

## `buildozer.spec`

Run `buildozer init` to have a new `buildozer.spec` file copied into the current
working directory. Edit it before running your first build.

See [buildozer/default.spec](https://raw.github.com/kivy/buildozer/master/buildozer/default.spec) for the template.

## Default config

You can override the value of any `buildozer.spec` config token by
setting an appropriate environment variable. These are all of the
form `$SECTION_TOKEN`, where SECTION is the config file section and
TOKEN is the config token to override. Dots are replaced by
underscores.

For example, here are some config tokens from the [app] section of the
config, along with the environment variables that would override them.

- `title` -> `$APP_TITLE`
- `package.name` -> `$APP_PACKAGE_NAME`
- `p4a.source_dir` -> `$APP_P4A_SOURCE_DIR`

## License

Buildozer is [MIT licensed](LICENSE), actively developed by a great
community and is supported by many projects managed by the 
[Kivy Organization](https://www.kivy.org/about.html).

## Documentation

[Documentation for this repository](https://buildozer.readthedocs.io/).

## Support

Are you having trouble using Buildozer or any of its related projects in the Kivy
ecosystem?
Is there an error you don’t understand? Are you trying to figure out how to use 
it? We have volunteers who can help!

The best channels to contact us for support are listed in the latest 
[Contact Us](https://github.com/kivy/buildozer/blob/master/CONTACT.md) document.

## Contributing

Buildozer is part of the [Kivy](https://kivy.org) ecosystem - a large group of
products used by many thousands of developers for free, but it
is built entirely by the contributions of volunteers. We welcome (and rely on) 
users who want to give back to the community by contributing to the project.

Contributions can come in many forms. See the latest 
[Contribution Guidelines](https://github.com/kivy/buildozer/blob/master/CONTRIBUTING.md)
for how you can help us.

## Code of Conduct

In the interest of fostering an open and welcoming community, we as 
contributors and maintainers need to ensure participation in our project and 
our sister projects is a harassment-free and positive experience for everyone. 
It is vital that all interaction is conducted in a manner conveying respect, 
open-mindedness and gratitude.

Please consult the [latest Code of Conduct](https://github.com/kivy/buildozer/blob/master/CODE_OF_CONDUCT.md).

## Contributors

This project exists thanks to 
[all the people who contribute](https://github.com/kivy/buildozer/graphs/contributors).
[[Become a contributor](CONTRIBUTING.md)].

<img src="https://contrib.nn.ci/api?repo=kivy/buildozer&pages=5&no_bot=true&radius=22&cols=18">

## Backers

Thank you to [all of our backers](https://opencollective.com/kivy)! 
🙏 [[Become a backer](https://opencollective.com/kivy#backer)]

<img src="https://opencollective.com/kivy/backers.svg?width=890&avatarHeight=44&button=false">

## Sponsors

Special thanks to 
[all of our sponsors, past and present](https://opencollective.com/kivy).
Support this project by 
[[becoming a sponsor](https://opencollective.com/kivy#sponsor)].

Here are our top current sponsors. Please click through to see their websites,
and support them as they support us. 

<!--- See https://github.com/orgs/kivy/discussions/15 for explanation of this code. -->
<a href="https://opencollective.com/kivy/sponsor/0/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/0/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/1/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/1/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/2/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/2/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/3/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/3/avatar.svg"></a>

<a href="https://opencollective.com/kivy/sponsor/4/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/4/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/5/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/5/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/6/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/6/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/7/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/7/avatar.svg"></a>

<a href="https://opencollective.com/kivy/sponsor/8/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/8/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/9/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/9/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/10/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/10/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/11/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/11/avatar.svg"></a>

<a href="https://opencollective.com/kivy/sponsor/12/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/12/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/13/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/13/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/14/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/14/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/15/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/15/avatar.svg"></a>
