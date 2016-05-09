# Change Log

## [v0.32](https://github.com/kivy/buildozer/tree/v0.32) (2016-05-09)
[Full Changelog](https://github.com/kivy/buildozer/compare/v0.31...v0.32)

- Added `source.include_patterns` app option
- Added `android_new` target to use the python-for-android revamp toolchain
- Added `build_dir` and `bin_dir` buildozer options
- Stopped using pip `--download-cache` flag, as it has been removed from recent pip versions
- Always use ios-deploy 1.7.0 - newer versions are completely different
- Fix bugs with Unicode app titles
- Fix bugs with directory handling
- Support using a custom kivy-ios dir
- Add `adb` command to android/android_new targets
- Disable bitcode on iOS builds (needed for newer Xcode)
- Fix `api`/`minapi` values for android target
- Use kivy-ios to build icons for all supported sizes
- Fix p4a branch handling
- Let p4a handle pure-Python packages (android_new)
- Use colored output in p4a (android_new)

## [v0.31](https://github.com/kivy/buildozer/tree/v0.31) (2016-01-07)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.30...v0.31)

**Closed issues:**

- Logo aspect ratio problem [\#263](https://github.com/kivy/buildozer/issues/263)
- Is there a way to seperate building environment and building apk? [\#259](https://github.com/kivy/buildozer/issues/259)
- buildozer must be ran with sudo [\#258](https://github.com/kivy/buildozer/issues/258)
- Invalid NDK platform [\#253](https://github.com/kivy/buildozer/issues/253)
- Q:compile error [\#252](https://github.com/kivy/buildozer/issues/252)
- Please update SDK url [\#249](https://github.com/kivy/buildozer/issues/249)
- java.lang.NoSuchMethodException: isSupportChangeBadgeByCallMethod \[\] [\#243](https://github.com/kivy/buildozer/issues/243)
- AttributeError: 'NoneType' object has no attribute 'group' [\#242](https://github.com/kivy/buildozer/issues/242)
- Error: Flag '-a' is not valid for 'list sdk'. [\#241](https://github.com/kivy/buildozer/issues/241)
- Provide custom path for android SDK to buildozer [\#237](https://github.com/kivy/buildozer/issues/237)
- kivy examples seem to need \_\_version\_\_ [\#236](https://github.com/kivy/buildozer/issues/236)
- pyliblo [\#235](https://github.com/kivy/buildozer/issues/235)

**Merged pull requests:**

- OS X Target for Bulldozer [\#262](https://github.com/kivy/buildozer/pull/262) ([akshayaurora](https://github.com/akshayaurora))
- kill easy\_install [\#244](https://github.com/kivy/buildozer/pull/244) ([techtonik](https://github.com/techtonik))
- install requires virtualenv [\#239](https://github.com/kivy/buildozer/pull/239) ([cbenhagen](https://github.com/cbenhagen))
- Fixed Space in app path issue. Fixes \#13 [\#231](https://github.com/kivy/buildozer/pull/231) ([dvenkatsagar](https://github.com/dvenkatsagar))

## [0.30](https://github.com/kivy/buildozer/tree/0.30) (2015-10-04)
[Full Changelog](https://github.com/kivy/buildozer/compare/v0.29...0.30)

**Closed issues:**

- subprocess.CalledProcessError: Command '\['ant', 'debug'\]' returned non-zero exit status 1 [\#234](https://github.com/kivy/buildozer/issues/234)
- Cannot use numpy with buildozer [\#232](https://github.com/kivy/buildozer/issues/232)
- Problem downloading ndk version \> r9d [\#229](https://github.com/kivy/buildozer/issues/229)
- Error likely to missing 32 bit packages [\#228](https://github.com/kivy/buildozer/issues/228)
- Bulldozer can't download new ndks 10x... [\#227](https://github.com/kivy/buildozer/issues/227)
- Error while trying to install Buildozer in Windows  10 [\#225](https://github.com/kivy/buildozer/issues/225)
- Making reverse engineering .apk harder [\#224](https://github.com/kivy/buildozer/issues/224)
- Buildozer wont compile libraries with cython 0.23 or 0.22 [\#223](https://github.com/kivy/buildozer/issues/223)
- These are the errors I get when I try to package the file...  [\#222](https://github.com/kivy/buildozer/issues/222)
- Buildozer installs platform despite setting ndk & sdk paths [\#220](https://github.com/kivy/buildozer/issues/220)
- Can't find config.ini buildozer solution [\#219](https://github.com/kivy/buildozer/issues/219)
- Ant error: SDK does not have any Build Tools installed [\#218](https://github.com/kivy/buildozer/issues/218)
- Buildozer fails because of build-tools package name [\#217](https://github.com/kivy/buildozer/issues/217)
- ImportError: No module named pygments [\#216](https://github.com/kivy/buildozer/issues/216)
- buildozer android camera [\#215](https://github.com/kivy/buildozer/issues/215)
- Error when first time Building apk   [\#212](https://github.com/kivy/buildozer/issues/212)
- cannot import name spawnu [\#211](https://github.com/kivy/buildozer/issues/211)
- Buildozer recompiles p4a when a custom for of plyer is used. [\#210](https://github.com/kivy/buildozer/issues/210)
- Add android.ant\_path to default.spec [\#209](https://github.com/kivy/buildozer/issues/209)
- Problems with adding wav, ogg and ttf files [\#208](https://github.com/kivy/buildozer/issues/208)
- cython issue with kivy and buildozer development versions [\#207](https://github.com/kivy/buildozer/issues/207)
- subprocess.CalledProcessError: Command '\['ant', 'debug'\]' returned non-zero exit status 1 [\#205](https://github.com/kivy/buildozer/issues/205)
- Buildozer isn't building if I try to include some requirements [\#195](https://github.com/kivy/buildozer/issues/195)
- Cant build APK for android.api = 10 [\#193](https://github.com/kivy/buildozer/issues/193)
- Doc error: "buildozer clean" does not exist [\#189](https://github.com/kivy/buildozer/issues/189)
- Can't install pillow requirement [\#188](https://github.com/kivy/buildozer/issues/188)
- \#error from Cython compilation [\#150](https://github.com/kivy/buildozer/issues/150)
- Space in app path path name causes ./distribute -m kivy to fail [\#13](https://github.com/kivy/buildozer/issues/13)

**Merged pull requests:**

- Changed p4a download to pull old\_toolchain branch [\#233](https://github.com/kivy/buildozer/pull/233) ([inclement](https://github.com/inclement))
- Added support for downloading and handling android ndk r10 versions. Fixes \#229 and \#227 [\#230](https://github.com/kivy/buildozer/pull/230) ([dvenkatsagar](https://github.com/dvenkatsagar))
- make \_read\_version\_subdir return parse\('0'\) instead of \[0\], otherwise… [\#206](https://github.com/kivy/buildozer/pull/206) ([denys-duchier](https://github.com/denys-duchier))

## [v0.29](https://github.com/kivy/buildozer/tree/v0.29) (2015-06-01)
[Full Changelog](https://github.com/kivy/buildozer/compare/v0.27...v0.29)

**Fixed bugs:**

- version problem with split [\#201](https://github.com/kivy/buildozer/issues/201)

**Closed issues:**

- buildozer android release hangs at "compile platform" [\#199](https://github.com/kivy/buildozer/issues/199)
- Hang up at Fetching https://dl-ssl.google.com/android/repository/addons\_list-2.xml [\#198](https://github.com/kivy/buildozer/issues/198)
- Python 3 Import error on urllib.request. [\#187](https://github.com/kivy/buildozer/issues/187)

**Merged pull requests:**

- needs testing, should fix \#201 using pypa implementation of PEP440 [\#202](https://github.com/kivy/buildozer/pull/202) ([tshirtman](https://github.com/tshirtman))
- check for complete dist instead of dist dir [\#197](https://github.com/kivy/buildozer/pull/197) ([kived](https://github.com/kived))
- fix ios targets xcode command [\#194](https://github.com/kivy/buildozer/pull/194) ([cbenhagen](https://github.com/cbenhagen))
- Windows fix [\#192](https://github.com/kivy/buildozer/pull/192) ([jaynakus](https://github.com/jaynakus))
- some python 3 compatibility [\#191](https://github.com/kivy/buildozer/pull/191) ([pohmelie](https://github.com/pohmelie))
- allow custom source folders in buildozer.spec [\#185](https://github.com/kivy/buildozer/pull/185) ([kived](https://github.com/kived))
- use upstream pexpect instead of shipping it [\#176](https://github.com/kivy/buildozer/pull/176) ([tshirtman](https://github.com/tshirtman))

## [v0.27](https://github.com/kivy/buildozer/tree/v0.27) (2015-03-08)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.26...v0.27)

**Closed issues:**

- subprocess.CalledProcessError: Command '\['ant', 'debug'\]' returned non-zero exit status 1 [\#183](https://github.com/kivy/buildozer/issues/183)
- Buildozer get error during packaging for android [\#182](https://github.com/kivy/buildozer/issues/182)
- Bug with android.p4a\_whitelist in buildozer.spec file. [\#180](https://github.com/kivy/buildozer/issues/180)
- You need an option for git https [\#178](https://github.com/kivy/buildozer/issues/178)
- Buildozer .apk file creation issue [\#177](https://github.com/kivy/buildozer/issues/177)
- sudo buildozer Fails [\#174](https://github.com/kivy/buildozer/issues/174)
- Buildozer iOS Apps Won't Open [\#171](https://github.com/kivy/buildozer/issues/171)
- always show python-for-android output on failure [\#170](https://github.com/kivy/buildozer/issues/170)
- Buildozer tries to install android sdk every time you try to compile an android application. [\#169](https://github.com/kivy/buildozer/issues/169)
- automatic installation of android sdk fails due to unicode parsing error [\#166](https://github.com/kivy/buildozer/issues/166)
- Move from fruitstrap to ios-deploy [\#107](https://github.com/kivy/buildozer/issues/107)
- buildozer ios debug build fails on MacOS Mavericks [\#83](https://github.com/kivy/buildozer/issues/83)
- gdb doesn't work anymore with Xcode 5 [\#54](https://github.com/kivy/buildozer/issues/54)
- buildozer ios debug deploy fails on running fruitstrap at 70% with error AMDeviceInstallApplication failed [\#9](https://github.com/kivy/buildozer/issues/9)

**Merged pull requests:**

- fix black text in log [\#184](https://github.com/kivy/buildozer/pull/184) ([kived](https://github.com/kived))

## [0.26](https://github.com/kivy/buildozer/tree/0.26) (2015-01-28)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.25...0.26)

**Merged pull requests:**

- ensure whitelist always has a list [\#172](https://github.com/kivy/buildozer/pull/172) ([kived](https://github.com/kived))

## [0.25](https://github.com/kivy/buildozer/tree/0.25) (2015-01-27)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.24...0.25)

## [0.24](https://github.com/kivy/buildozer/tree/0.24) (2015-01-27)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.23...0.24)

## [0.23](https://github.com/kivy/buildozer/tree/0.23) (2015-01-27)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.22...0.23)

## [0.22](https://github.com/kivy/buildozer/tree/0.22) (2015-01-27)
[Full Changelog](https://github.com/kivy/buildozer/compare/v0.21...0.22)

## [v0.21](https://github.com/kivy/buildozer/tree/v0.21) (2015-01-14)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.19...v0.21)

**Merged pull requests:**

- removed some indentation in example info, added to actual comments inste... [\#168](https://github.com/kivy/buildozer/pull/168) ([chozabu](https://github.com/chozabu))

## [0.19](https://github.com/kivy/buildozer/tree/0.19) (2014-12-17)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.18...0.19)

## [0.18](https://github.com/kivy/buildozer/tree/0.18) (2014-12-17)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.17...0.18)

**Closed issues:**

- buildozer can't download python libs due to ssl certificate check fail [\#164](https://github.com/kivy/buildozer/issues/164)
- Buildozer feature redirect .buildozer folder outside your project [\#162](https://github.com/kivy/buildozer/issues/162)
- Buildozer fails on clean build [\#161](https://github.com/kivy/buildozer/issues/161)
- pjnius build fails on Arch Linux when requiring netifaces [\#159](https://github.com/kivy/buildozer/issues/159)
- error compiling with buildozer [\#158](https://github.com/kivy/buildozer/issues/158)
- C compiler cannot create executables [\#152](https://github.com/kivy/buildozer/issues/152)
- Requirements needing commas instead of spaces \(like p4a\) is non-obvious [\#147](https://github.com/kivy/buildozer/issues/147)

**Merged pull requests:**

- fix build error and allow redirecting build folder [\#163](https://github.com/kivy/buildozer/pull/163) ([olymk2](https://github.com/olymk2))
- Remove duplicated checkbin\(\). [\#160](https://github.com/kivy/buildozer/pull/160) ([attakei](https://github.com/attakei))
- added note about buildozer not having anything to do with buildozer.io [\#157](https://github.com/kivy/buildozer/pull/157) ([nickyspag](https://github.com/nickyspag))
- Fixed logic to compare with “non installed” with “minor version upped"  [\#156](https://github.com/kivy/buildozer/pull/156) ([attakei](https://github.com/attakei))
- Set "UTF-8" to java file.encoding for android update command explicitly [\#155](https://github.com/kivy/buildozer/pull/155) ([attakei](https://github.com/attakei))
- added example to default.spec requirements showing comma seperation [\#148](https://github.com/kivy/buildozer/pull/148) ([chozabu](https://github.com/chozabu))

## [0.17](https://github.com/kivy/buildozer/tree/0.17) (2014-09-22)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.16...0.17)

## [0.16](https://github.com/kivy/buildozer/tree/0.16) (2014-09-22)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.15...0.16)

**Closed issues:**

- `install\_android\_packages` is too slow to run in china. [\#143](https://github.com/kivy/buildozer/issues/143)
- Buildozer setup.py fails with Module ImportError [\#140](https://github.com/kivy/buildozer/issues/140)
- buildozer downloads Android SDK 20 during every call to deploy app [\#137](https://github.com/kivy/buildozer/issues/137)
- Buildozerv0.15: lib/pexpect.py is not Python 3 compatable [\#131](https://github.com/kivy/buildozer/issues/131)
- Keep on gettting version error [\#129](https://github.com/kivy/buildozer/issues/129)
- arm-linux-androideabi-gcc: fatal error: no input files [\#127](https://github.com/kivy/buildozer/issues/127)
- I am new to python and buildozer, using buildozer to compile my first android app [\#125](https://github.com/kivy/buildozer/issues/125)
- I am new to python and buildozer, using buildozer to compile my first android app, [\#124](https://github.com/kivy/buildozer/issues/124)
- Command Failed [\#122](https://github.com/kivy/buildozer/issues/122)
- Exception: Cython cythonnot found [\#120](https://github.com/kivy/buildozer/issues/120)
- Enable use for packaging OSX apps [\#114](https://github.com/kivy/buildozer/issues/114)
- Errors on 'buildozer android debug deploy run' [\#113](https://github.com/kivy/buildozer/issues/113)
- Fail to download Android SDK in Linux and Python 3.3 [\#110](https://github.com/kivy/buildozer/issues/110)
- Unable to add "requirements" buildozer.spec [\#109](https://github.com/kivy/buildozer/issues/109)
- TypeError: 'encoding' is an invalid keyword argument for this function [\#106](https://github.com/kivy/buildozer/issues/106)
- Custom activity [\#33](https://github.com/kivy/buildozer/issues/33)
- Buildozer fails to install on Windows [\#27](https://github.com/kivy/buildozer/issues/27)
- support blacklist changes in python-for-android [\#17](https://github.com/kivy/buildozer/issues/17)

**Merged pull requests:**

- Test in file\_rename if target directory exists. [\#144](https://github.com/kivy/buildozer/pull/144) ([droundy](https://github.com/droundy))
- Fix for android.library\_references path issue [\#139](https://github.com/kivy/buildozer/pull/139) ([excessivedemon](https://github.com/excessivedemon))
- Specs doc revision [\#134](https://github.com/kivy/buildozer/pull/134) ([dessant](https://github.com/dessant))
- Make pexpect.py Python 3 Compatable [\#133](https://github.com/kivy/buildozer/pull/133) ([FeralBytes](https://github.com/FeralBytes))
- Added check for buildozer running as root [\#128](https://github.com/kivy/buildozer/pull/128) ([inclement](https://github.com/inclement))
- Add link to the right android python project [\#119](https://github.com/kivy/buildozer/pull/119) ([techtonik](https://github.com/techtonik))
- Execute buildozer as "python -m buildozer" [\#118](https://github.com/kivy/buildozer/pull/118) ([techtonik](https://github.com/techtonik))
- Fix \#115 [\#116](https://github.com/kivy/buildozer/pull/116) ([manuelbua](https://github.com/manuelbua))

## [0.15](https://github.com/kivy/buildozer/tree/0.15) (2014-06-02)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.14...0.15)

**Closed issues:**

- Do not set permissions \(ug+x\) if already set [\#115](https://github.com/kivy/buildozer/issues/115)
- UTF-8 Encoding Error, \_\_init.py\_\_ 0.15-dev [\#108](https://github.com/kivy/buildozer/issues/108)
- incorrect minapi android manifest value [\#93](https://github.com/kivy/buildozer/issues/93)
- libpython wait4 linker error [\#92](https://github.com/kivy/buildozer/issues/92)
- fcntl import error [\#88](https://github.com/kivy/buildozer/issues/88)
- No Python 3 Support [\#84](https://github.com/kivy/buildozer/issues/84)
- Uncaught exception on missing cython [\#80](https://github.com/kivy/buildozer/issues/80)
- Where are custom python-for-android recipes meant to go? [\#76](https://github.com/kivy/buildozer/issues/76)
- Error compiling Cython file: [\#73](https://github.com/kivy/buildozer/issues/73)
- Zlib still giving issues on Ubuntu 13.04 [\#72](https://github.com/kivy/buildozer/issues/72)
- DBAccessError permission denied in app [\#71](https://github.com/kivy/buildozer/issues/71)
- Selective update of depencencies [\#70](https://github.com/kivy/buildozer/issues/70)
- 32-bit SDK installed on 64-bit system [\#69](https://github.com/kivy/buildozer/issues/69)
- wrong version regex [\#67](https://github.com/kivy/buildozer/issues/67)
- sdk update fails on license question [\#66](https://github.com/kivy/buildozer/issues/66)
- x86 and armeabi-v7 libs [\#63](https://github.com/kivy/buildozer/issues/63)
- Missing dependenced during compilation [\#59](https://github.com/kivy/buildozer/issues/59)
- Bad magic number when reading generated state.db file in VMware Ubuntu guest [\#42](https://github.com/kivy/buildozer/issues/42)
- x86 apk support on buildozer [\#11](https://github.com/kivy/buildozer/issues/11)

**Merged pull requests:**

- Ignore UTF-8 decoding errors. Closes \#108 [\#112](https://github.com/kivy/buildozer/pull/112) ([cbenhagen](https://github.com/cbenhagen))
- chmod ug+x android\_cmd [\#111](https://github.com/kivy/buildozer/pull/111) ([cbenhagen](https://github.com/cbenhagen))
- p4a whitelist [\#98](https://github.com/kivy/buildozer/pull/98) ([b3ni](https://github.com/b3ni))

## [0.14](https://github.com/kivy/buildozer/tree/0.14) (2014-04-20)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.13...0.14)

## [0.13](https://github.com/kivy/buildozer/tree/0.13) (2014-04-20)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.12...0.13)

## [0.12](https://github.com/kivy/buildozer/tree/0.12) (2014-04-20)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.11...0.12)

## [0.11](https://github.com/kivy/buildozer/tree/0.11) (2014-04-20)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.10...0.11)

**Closed issues:**

- Text provider [\#105](https://github.com/kivy/buildozer/issues/105)
- No installation instructions [\#104](https://github.com/kivy/buildozer/issues/104)

## [0.10](https://github.com/kivy/buildozer/tree/0.10) (2014-04-09)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.9...0.10)

**Closed issues:**

- Android SDK installation not working anymore [\#101](https://github.com/kivy/buildozer/issues/101)
- Buildozer almost completes and then errors saying file exists [\#99](https://github.com/kivy/buildozer/issues/99)
- Java compilernot found [\#95](https://github.com/kivy/buildozer/issues/95)
- Absolute path problem [\#91](https://github.com/kivy/buildozer/issues/91)
- Error when running: buildozer --verbose android debug deploy run [\#89](https://github.com/kivy/buildozer/issues/89)
- buildozer.spec passing requirements  [\#87](https://github.com/kivy/buildozer/issues/87)
- debugging "Command failed" is tedious [\#86](https://github.com/kivy/buildozer/issues/86)
- No module named sqlite3  [\#56](https://github.com/kivy/buildozer/issues/56)
- Garden packages are unsupported [\#39](https://github.com/kivy/buildozer/issues/39)
- python-for-android repo is hard-coded in buildozer [\#37](https://github.com/kivy/buildozer/issues/37)
- virtualenv-2.7 hardcoded [\#22](https://github.com/kivy/buildozer/issues/22)
- Buildozer error no build.py [\#21](https://github.com/kivy/buildozer/issues/21)

**Merged pull requests:**

- Fixed garden install for newer virtualenvs [\#100](https://github.com/kivy/buildozer/pull/100) ([brousch](https://github.com/brousch))
- fix ln if soft link existed [\#96](https://github.com/kivy/buildozer/pull/96) ([pengjia](https://github.com/pengjia))
- Added realpath modifier to p4a\_dir token [\#94](https://github.com/kivy/buildozer/pull/94) ([inclement](https://github.com/inclement))
- Documented env var checking and fixed a bug in the p4a\_dir check [\#85](https://github.com/kivy/buildozer/pull/85) ([inclement](https://github.com/inclement))
- Delete dist dir if running distribute.sh [\#81](https://github.com/kivy/buildozer/pull/81) ([inclement](https://github.com/inclement))
- implement the `clean` command. [\#79](https://github.com/kivy/buildozer/pull/79) ([akshayaurora](https://github.com/akshayaurora))
- Garden requirements [\#41](https://github.com/kivy/buildozer/pull/41) ([Ian-Foote](https://github.com/Ian-Foote))

## [0.9](https://github.com/kivy/buildozer/tree/0.9) (2014-02-13)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.8...0.9)

**Closed issues:**

-  Command failed: ./distribute.sh -m "kivy" error message [\#77](https://github.com/kivy/buildozer/issues/77)
- Error importing \_scproxy [\#68](https://github.com/kivy/buildozer/issues/68)
- Package names beginning with a number cause an obscure crash with an unclear error message [\#64](https://github.com/kivy/buildozer/issues/64)
- failing to compile sample android app with buildozer  [\#61](https://github.com/kivy/buildozer/issues/61)
- Default android.sdk setting causes sensor rotate on Android to fail [\#32](https://github.com/kivy/buildozer/issues/32)
- Add wakelock to options [\#31](https://github.com/kivy/buildozer/issues/31)

**Merged pull requests:**

- Updated Android NDK default version to 9c [\#82](https://github.com/kivy/buildozer/pull/82) ([brousch](https://github.com/brousch))
- Add 'bin' to suggested default directory excludes [\#78](https://github.com/kivy/buildozer/pull/78) ([josephlee021](https://github.com/josephlee021))
- Clarified wording in README [\#75](https://github.com/kivy/buildozer/pull/75) ([inclement](https://github.com/inclement))
- Check for package name starting with number [\#65](https://github.com/kivy/buildozer/pull/65) ([inclement](https://github.com/inclement))
- \[FIX\] Detect 32/64 bit on Windows, to download Android NDK [\#62](https://github.com/kivy/buildozer/pull/62) ([alanjds](https://github.com/alanjds))
- Add ability to choose python-for-android directory [\#60](https://github.com/kivy/buildozer/pull/60) ([inclement](https://github.com/inclement))
- Added --private and --dir Android storage option [\#58](https://github.com/kivy/buildozer/pull/58) ([brousch](https://github.com/brousch))
- Added a 'serve' command to serve bin/ over SimpleHTTPServer [\#49](https://github.com/kivy/buildozer/pull/49) ([brousch](https://github.com/brousch))

## [0.8](https://github.com/kivy/buildozer/tree/0.8) (2013-10-29)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.7...0.8)

**Fixed bugs:**

- \_patch\_application\_sources breaks from \_\_future\_\_ imports [\#35](https://github.com/kivy/buildozer/issues/35)

**Closed issues:**

- unresolved domain: pygame.org [\#34](https://github.com/kivy/buildozer/issues/34)

**Merged pull requests:**

- Update default Android NDK to r9 [\#53](https://github.com/kivy/buildozer/pull/53) ([brousch](https://github.com/brousch))
- Added android.wakelock option [\#51](https://github.com/kivy/buildozer/pull/51) ([brousch](https://github.com/brousch))
- Fixed another 'Unknown' typo [\#48](https://github.com/kivy/buildozer/pull/48) ([brousch](https://github.com/brousch))
- Fixed spelling of 'Unknown' [\#47](https://github.com/kivy/buildozer/pull/47) ([brousch](https://github.com/brousch))
- Fixed missing 'r' on ANDROIDNDKVER environment export [\#46](https://github.com/kivy/buildozer/pull/46) ([brousch](https://github.com/brousch))
- make sure android.branch works with fresh clone [\#44](https://github.com/kivy/buildozer/pull/44) ([akshayaurora](https://github.com/akshayaurora))
- Fixed a typo in setdefault description [\#40](https://github.com/kivy/buildozer/pull/40) ([nithin-bose](https://github.com/nithin-bose))
- Package paths [\#38](https://github.com/kivy/buildozer/pull/38) ([Ian-Foote](https://github.com/Ian-Foote))
- add applibs in path for service too [\#26](https://github.com/kivy/buildozer/pull/26) ([tshirtman](https://github.com/tshirtman))
- fix distribute install before installing every dependencies, fix a few i... [\#25](https://github.com/kivy/buildozer/pull/25) ([tshirtman](https://github.com/tshirtman))

## [0.7](https://github.com/kivy/buildozer/tree/0.7) (2013-09-11)
[Full Changelog](https://github.com/kivy/buildozer/compare/0.2...0.7)

**Closed issues:**

- Builds fail on Ubuntu 13.04 with zlib.h missing [\#18](https://github.com/kivy/buildozer/issues/18)
- "buildozer android update" fails with an error about android.branch [\#12](https://github.com/kivy/buildozer/issues/12)
- Problem Ubuntu compilation on network drive [\#10](https://github.com/kivy/buildozer/issues/10)
- \[app\] "android.permission" contain an unknown permission  [\#6](https://github.com/kivy/buildozer/issues/6)
- buildozer on ios fails at: Command failed: tools/build-all.sh [\#5](https://github.com/kivy/buildozer/issues/5)
- Automatically installing Android SDK fails in file\_rename called from \_install\_android\_sdk [\#4](https://github.com/kivy/buildozer/issues/4)
- buildozer does not support ~ in android.sdk\_path [\#3](https://github.com/kivy/buildozer/issues/3)

**Merged pull requests:**

- Fix typo 'versionning' -\> 'versioning'. [\#29](https://github.com/kivy/buildozer/pull/29) ([Ian-Foote](https://github.com/Ian-Foote))
- Fixed hard-coded Android API 14 [\#23](https://github.com/kivy/buildozer/pull/23) ([brousch](https://github.com/brousch))
- Fixed \#18: Builds fail on Ubuntu 13.04 with zlib.h missing. [\#20](https://github.com/kivy/buildozer/pull/20) ([roskakori](https://github.com/roskakori))
- Europython sprint updates [\#19](https://github.com/kivy/buildozer/pull/19) ([fabiankreutz](https://github.com/fabiankreutz))
- copy the generated apk back from remote [\#16](https://github.com/kivy/buildozer/pull/16) ([akshayaurora](https://github.com/akshayaurora))
- android.add\_jars config option [\#15](https://github.com/kivy/buildozer/pull/15) ([bob-the-hamster](https://github.com/bob-the-hamster))
- Ouya support [\#14](https://github.com/kivy/buildozer/pull/14) ([bob-the-hamster](https://github.com/bob-the-hamster))

## [0.2](https://github.com/kivy/buildozer/tree/0.2) (2012-12-20)


\* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)*
