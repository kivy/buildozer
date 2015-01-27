Changelog
=========

%%version%% (unreleased)
------------------------

- Bump to 0.23dev. [Mathieu Virbel]

0.22 (2015-01-27)
-----------------

- Bump to 0.22. [Mathieu Virbel]

- Android: dont lookup to android sdk/ndk if we didnt change the
  buildozer.spec options related to it, and if everything was working in
  the first time. [Mathieu Virbel]

- Whitelist: always generate the whitelist even after the initial
  distribution build. Otherwise, any further changes are not reflected
  in the final app. [Mathieu Virbel]

- Bump version to 0.22dev after release. [Mathieu Virbel]

- Version 0.21. [Mathieu Virbel]

- Bump to 0.20. [Mathieu Virbel]

- Pexpect: fix python2 decoding issue. [Mathieu Virbel]

- Merge pull request #168 from chozabu/diff_default_indentation.
  [Mathieu Virbel]

  removed some indentation in example info, added to actual comments
  inste...

- Bump to 0.20-dev. [Mathieu Virbel]

- Bump to 0.19. [Mathieu Virbel]

- Upgrade ant tool, as ant < 1.9 cannot handle java 8. [Mathieu Virbel]

- Bump to 0.19-dev. [Mathieu Virbel]

- Bump to 0.18. [Mathieu Virbel]

- Avoid dpkg check on non-linux platform. [Mathieu Virbel]

- Merge pull request #163 from olymk2/master. [Mathieu Virbel]

  fix build error and allow redirecting build folder

- Merge pull request #160 from attakei/master. [Mathieu Virbel]

  Remove duplicated checkbin().

- Merge pull request #156 from attakei/patches/resolve_compare_versions.
  [Mathieu Virbel]

  Fixed logic to compare with “non installed” with “minor version upped"

- Merge pull request #157 from nickyspag/master. [Akshay Arora]

  added note about buildozer not having anything to do with buildozer.io

- Merge pull request #155 from attakei/patches/lock_java_file_encoding.
  [Akshay Arora]

  Set "UTF-8" to java file.encoding for android update command
  explicitly

- Merge pull request #148 from chozabu/clarify_reqs_example. [Mathieu
  Virbel]

  added example to default.spec requirements showing comma seperation

- Bump to 0.17-dev. [Mathieu Virbel]

0.17 (2014-09-22)
-----------------

- Bump to 0.17. [Mathieu Virbel]

- Merge branch 'master' of ssh://github.com/kivy/buildozer. [Mathieu
  Virbel]

- Bump to 0.17-dev. [Mathieu Virbel]

0.16 (2014-09-22)
-----------------

- Bump to 0.16. [Mathieu Virbel]

- Backport android version check fixes from @monkut. Closes #137. Closes
  #143. [Mathieu Virbel]

- Fixed warn_on_root default value. [Alexander Taylor]

- Merge pull request #128 from inclement/root_check. [Akshay Arora]

  Added check for buildozer running as root

- Android: manually check the installed version for the build-tools, in
  order to install the latest one. without -a in android list sdk, we
  cannot known if a new build-tools is available or not. [Mathieu
  Virbel]

- Fix version regex. [tshirtman]

- Fix download of Android SDK in linux with python 3.3. Closes #110.
  [Mathieu Virbel]

- Merge pull request #116 from manuelbua/check-before-chmod. [Mathieu
  Virbel]

  Fix #115

- Merge pull request #118 from techtonik/master. [Mathieu Virbel]

  Execute buildozer as "python -m buildozer"

- Merge pull request #119 from techtonik/patch-1. [Mathieu Virbel]

  Add link to the right android python project

- Bump to 0.16-dev. [Mathieu Virbel]

0.15 (2014-06-02)
-----------------

- Bump to 0.15. [Mathieu Virbel]

- Merge pull request #112 from cbenhagen/patch-2. [Mathieu Virbel]

  Ignore UTF-8 decoding errors. Closes #108

- Merge pull request #111 from cbenhagen/patch-1. [Akshay Arora]

  chmod ug+x android_cmd

- Missing use buildozer.debug. [qua-non]

- Merge branch 'master' of ssh://github.com/kivy/buildozer. [Mathieu
  Virbel]

- Add support for copying libraries for armeabi, armeabi-v7a, x86, mips.
  closes #63. [Mathieu Virbel]

- Change the regex to capture the version with " too. closes #67.
  [Mathieu Virbel]

- Ensure libz is installed too. closes #72. [Mathieu Virbel]

- Add instructions for using custom recipe + contributing back. closes
  #76. [Mathieu Virbel]

- Avoid showing the exception, print and exit when checkbin() fail.
  closes #80. [Mathieu Virbel]

- Merge branch 'master' of ssh://github.com/kivy/buildozer. [Mathieu
  Virbel]

- Correctly pass android.minapi/api to build.py. closes #93. [Mathieu
  Virbel]

- Bump to 0.15-dev. [Mathieu Virbel]

0.14 (2014-04-20)
-----------------

- Fixes python2 console write (as before) [Mathieu Virbel]

0.13 (2014-04-20)
-----------------

- Bump to 0.13. [Mathieu Virbel]

- Fixes windows color. [Mathieu Virbel]

- Fixes for Python 2 + color. [Mathieu Virbel]

0.12 (2014-04-20)
-----------------

- Bump to 0.12. [Mathieu Virbel]

- Fix open() for python2 in buildozer. [Mathieu Virbel]

- Bump to 0.12-dev. [Mathieu Virbel]

0.11 (2014-04-20)
-----------------

- Bump to 0.11. [Mathieu Virbel]

- Update changes. [Mathieu Virbel]

- Fixes buildozer for Windows. closes #90. [Mathieu Virbel]

- Add missing documentation configuration. [Mathieu Virbel]

- Add documentation. [Mathieu Virbel]

- Add changes file. [Mathieu Virbel]

- Move scripts into buildozer.scripts.*, and use console_scripts for
  setup() [Mathieu Virbel]

- First pass to make buildozer compatible with python3. [Mathieu Virbel]

- Bump to 0.11-dev. [Mathieu Virbel]

0.10 (2014-04-09)
-----------------

- Bump to 0.10. [Mathieu Virbel]

- Use timeout=None to prevent TIMEOUT during child.expect. [Mathieu
  Virbel]

- Merge branch 'master' of ssh://github.com/kivy/buildozer. [Mathieu
  Virbel]

- Install libs as well. [Mathieu Virbel]

- Merge branch 'relpath' of https://github.com/inclement/buildozer into
  inclement-relpath. [Mathieu Virbel]

  Conflicts:         buildozer/targets/android.py

- Correctly update and download Android SDK with tools/platform-tools
  /build-tools if available. And install the API if necessary. closes
  #101, #21, #89. [Mathieu Virbel]

- Dont try to copy garden if the directory doesnt exists. [Mathieu
  Virbel]

- Dont try to install garden if the user doesnt use anything from
  garden. [Mathieu Virbel]

- Merge pull request #100 from kivy/garden_venv_fix. [Akshay Arora]

  Fixed garden install for newer virtualenvs

- Merge pull request #96 from pengjia/master. [Akshay Arora]

  fix ln if soft link existed

- Merge pull request #41 from Ian-Foote/garden_requirements. [Akshay
  Arora]

  Garden requirements

- Merge pull request #85 from inclement/p4a_dir_fixes. [Alexander
  Taylor]

  Documented env var checking and fixed a bug in the p4a_dir check

- Bump to 0.10-dev. [Mathieu Virbel]

0.9 (2014-02-13)
----------------

- Merge pull request #82 from kivy/update_ndk_to_9c. [akshayaurora]

  Updated Android NDK default version to 9c

- Merge pull request #60 from inclement/p4a. [Mathieu Virbel]

  Add ability to choose python-for-android directory

- Merge pull request #78 from josephlee021/master. [qua-non]

  Add 'bin' to suggested default directory excludes

- Merge pull request #75 from inclement/readme3. [Gabriel Pettier]

  Clarified wording in README

- Merge pull request #65 from inclement/packagename. [qua-non]

  Check for package name starting with number

- Merge branch 'master' of ssh://github.com/kivy/buildozer. [Mathieu
  Virbel]

- Correctly check requirements if a specific version is used
  (package==version will check the requirement only on package, not the
  full requirement token.) [Mathieu Virbel]

- Add meta-data support, external android libraries support, and custom
  java files to include in the APK. [Mathieu Virbel]

- More android/python-for-android directory to clean after building the
  distribution. [Mathieu Virbel]

- Fix buildozer PACKAGES_PATH to use global buildozer directory instead
  of the local one. [Mathieu Virbel]

- Enjoy of the latest python-for-android addition: cache for packages.
  set correctly the PACKAGES_PATH to the global buildozer
  directory/target/packages. [Mathieu Virbel]

- Rename privatestorage to private_storage. [Mathieu Virbel]

- Merge pull request #58 from brousch/android-storagetype-option.
  [Mathieu Virbel]

  Added --private and --dir Android storage option

- Merge pull request #49 from brousch/serve_command. [Mathieu Virbel]

  Added a 'serve' command to serve bin/ over SimpleHTTPServer

0.8 (2013-10-29)
----------------

- Bump to 0.8. [Mathieu Virbel]

- Reduce the size of the remaining .buildozer. [Mathieu Virbel]

- Allow custom permissions. [Mathieu Virbel]

- Fix lower case permission when section is used instead of key=value.
  [Mathieu Virbel]

- Merge pull request #53 from brousch/update-default-ndk-r9. [qua-non]

  Update default Android NDK to r9

- Merge pull request #48 from brousch/patch-3. [qua-non]

  Fixed another 'Unknown' typo

- Merge pull request #51 from brousch/android.wakelock. [qua-non]

  Added android.wakelock option

- Merge pull request #47 from brousch/patch-1. [qua-non]

  Fixed spelling of 'Unknown'

- Merge pull request #46 from brousch/patch-2. [qua-non]

  Fixed missing 'r' on ANDROIDNDKVER environment export

- Merge pull request #44 from kivy/android_branch. [Mathieu Virbel]

  make sure android.branch works with fresh clone

- Merge pull request #26 from kivy/fix_service_path. [Mathieu Virbel]

  add applibs in path for service too

- Merge pull request #25 from kivy/autofix_distribute. [Mathieu Virbel]

  fix distribute install before installing every dependencies, fix a few
  i...

- Merge pull request #40 from nithinbose87/master. [Gabriel Pettier]

  Fixed a typo in setdefault description

- Merge pull request #38 from Ian-Foote/package_paths. [Mathieu Virbel]

  Package paths

0.7 (2013-09-11)
----------------

- Merge branch 'master' of ssh://github.com/kivy/buildozer. [Mathieu
  Virbel]

- Bump to 0.7. [Mathieu Virbel]

- Fix android.add_jars to be a "list" type, and be consistent with
  others token. Multiple .jar are now separated with "," and not ";".
  Also, it can be configured as a specific section (as all the others
  list types.) [Mathieu Virbel]

- New android.add_libs_armeabi to add custom .so in the libs/armeabi
  directory. [Mathieu Virbel]

- Implement profiles. bump to 0.6. [Mathieu Virbel]

- Bump to 0.5. [Mathieu Virbel]

- Add the possilibity to use the content of a section as a list. Ie,
  instead of doing "source.exclude_dirs = dir1,dir2", just create a
  section [app:source.exclude_dirs], and put one directory per line.
  [Mathieu Virbel]

- Add source.exclude_dirs and source.exclude_patterns options in [app].
  Check the default.spec for informations. [Mathieu Virbel]

- Simulate a chrome for downloading. It seem that some download
  (ndk/sdk) are faster using it. [Mathieu Virbel]

- Add possibility to use public key/identity instead of password.
  [Mathieu Virbel]

- Buildozer is now under MIT license. [Mathieu Virbel]

- Add help for getting a list of identities for ios platform. [Mathieu
  Virbel]

- Add ability for not checking the configuration for some commands.
  [Mathieu Virbel]

- Merge pull request #20 from roskakori/master. [Mathieu Virbel]

  Fixed #18: Builds fail on Ubuntu 13.04 with zlib.h missing.

- Avoid empty lines when checking adb serials. [Mathieu Virbel]

- Avoid start message of adb. [Mathieu Virbel]

- Avoid start message of adb. [Mathieu Virbel]

- Fix adb devices by using the self.adb_cmd. [Mathieu Virbel]

- Merge pull request #19 from fabiankreutz/master. [Mathieu Virbel]

  Europython sprint updates

- Enhance error message when version capture failed. Credits goes to
  Dabian Snovna. [Mathieu Virbel]

- Use the right 32/64 bits version of NDK depending of the current
  platform. Credits goes to Dabian Snovna. [Mathieu Virbel]

- Update to 0.4. [Mathieu Virbel]

- Merge pull request #16 from kivy/copy_back. [Mathieu Virbel]

  copy the generated apk back from remote

- Allows multiple devices in ANDROID_SERIAL env variables, separated
  with comma. [Mathieu Virbel]

- Support fo intent_filters on android. [Mathieu Virbel]

- Various bugfixes for osx. [Mathieu Virbel]

- Merge pull request #14 from bob-the-hamster/ouya-support. [Mathieu
  Virbel]

  Ouya support

- Merge pull request #15 from bob-the-hamster/add-jars. [Mathieu Virbel]

  android.add_jars config option

- Add support for orientation and fullscreen (working on android only
  right now.) [Mathieu Virbel]

- Android: if multiples devices are plugged, deploy and run on all of
  them. except if a ANDROID_SERIAL env is set. [Mathieu Virbel]

- Fixes for the android.branch feature. [tshirtman]

  Use getdefault instead of get (duh) Add commented option to
  default.spec for documentation
  fix: #12

- Update README.rst. [Mathieu Virbel]

- Ios: use the package.name instead of the title for creating the app-
  directory. [Mathieu Virbel]

- Remove bad readme. [Mathieu Virbel]

- Add cython check for ios target. closes #5. [Mathieu Virbel]

- Avoid to prepend app_dir for icon/presplash. use root_dir instead.
  [Mathieu Virbel]

- Merge branch 'master' of ssh://github.com/kivy/buildozer. [Mathieu
  Virbel]

- Fix get_config_list when the string is empty. closes #8. [Mathieu
  Virbel]

- Merge branch 'master' of ssh://github.com/kivy/buildozer. [Mathieu
  Virbel]

- Fix config list when a default value is given. [Mathieu Virbel]

- Rework how buildozer-remote pipeline commands works (support stdin
  now.) [Mathieu Virbel]

- Ios: correctly unlock the keychain, to be able to remotely sign the
  app. [Mathieu Virbel]

- Don't remove include_exts/exclude_exts with remote, or no app sources
  will be used. [Mathieu Virbel]

- Add more include_exts by default. [Mathieu Virbel]

- Introducing buildozer-remote, WIP. It connect to a ssh server, create
  build directory, copy buildozer and the app source code, and invoke
  buildozer commands. Missing: documentation, sync binaries back to the
  host, etc. [Mathieu Virbel]

- Ios: update the plist to include correct package domain+name, version,
  build id, and resample the icon if the dimensions are not ok. [Mathieu
  Virbel]

- Add ios support. compilation, packaging, deploy and running works, all
  from command line. Marvelous!! [Mathieu Virbel]

- Add icon and presplash support. [Mathieu Virbel]

- Virtualenv: avoid to reinstall applibs except if requirements changed.
  [Mathieu Virbel]

- First pass to install possible external requirements within a
  virtualenv + copy the installed packages into an _applibs + patch
  main.py to include the _applibs. [Mathieu Virbel]

- Merge branch 'master' of ssh://github.com/kivy/buildozer. [Mathieu
  Virbel]

- Don't check configuration tokens if the buildozer.spec has not been
  loaded. [Mathieu Virbel]

- Avoid double-logging of commands. [Mathieu Virbel]

- Fix debug() issue, and avoid % in print. [Mathieu Virbel]

- Add target configuration check (like ensure the android permissions
  are the correct one, according to the platform sdk). [Mathieu Virbel]

- Add initial .spec tokens checks. [Mathieu Virbel]

- Add logging level capability. restrict to error+info by default. use
  --verbose/-v, or log_level=2 in the spec for increasing to debug, and
  show command output. [Mathieu Virbel]

- Add color in the log! [Mathieu Virbel]

- Enhance cmd() stdout/stderr capture, and use fcntl/select to faster
  redirection. avoid to store stdout/stderr if not used. [Mathieu
  Virbel]

- Add custom commands + usage + ability to follow an stdout command.
  [Mathieu Virbel]

- Moar typo. [Mathieu Virbel]

- Typo. [Mathieu Virbel]

- Bump to 0.3-dev. [Mathieu Virbel]

0.2 (2012-12-20)
----------------

- Update README + bump to 0.2. [Mathieu Virbel]

- Fix readme. [Mathieu Virbel]

- Add seperation between "global" and "local" stuff, and allow to use
  custom ndk/sdk/ant directory. [Mathieu Virbel]

- Fix default command. [Mathieu Virbel]

- Seperate the state.db from the platform dir. avoid to create platform
  dir until we know the target. [Mathieu Virbel]

- Add missing .buildozer creation0. [Mathieu Virbel]

- Fix doc. [Mathieu Virbel]

- Avoid multiple execution of build() and prepare_for_build() method.
  [Mathieu Virbel]

- Include the default.spec when using setup.py install. [Mathieu Virbel]

- Fix buildozer init. [Mathieu Virbel]

- Add missing files, and publish a first version. [Mathieu Virbel]

- Remove unused usage. [Mathieu Virbel]

- Rework command line arguments / target / usage add deploy and run
  command. [Mathieu Virbel]

- Add more doc. [Mathieu Virbel]

- Finish buildozer android target (only debug build are supported right
  now.) [Mathieu Virbel]

- Wip. [Mathieu Virbel]

- Typo. [Mathieu Virbel]


