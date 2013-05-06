[app]

# (str) Title of your application
title = My Application

# (str) Package name
package.name = myapp

# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (list) Source files to exclude (let empty to not excluding anything)
#source.exclude_exts = spec

# (str) Application versionning (method 1)
version.regex = __version__ = '(.*)'
version.filename = %(source.dir)s/main.py

# (str) Application versionning (method 2)
# version = 1.2.0

# (list) Application requirements
requirements = kivy

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, portrait or all)
orientation = landscape

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1


#
# Android specific
#

# (list) Permissions
#android.permissions = INTERNET

# (int) Android API to use
#android.api = 14

# (int) Minimum API required (8 = Android 2.2 devices)
#android.minapi = 8

# (int) Android SDK version to use
#android.sdk = 21

# (str) Android NDK version to use
#android.ndk = 8c

# (str) Android NDK directory (if empty, it will be automatically downloaded.)
#android.ndk_path =

# (str) Android SDK directory (if empty, it will be automatically downloaded.)
#android.sdk_path = 

# (str) Android entry point, default is ok for Kivy-based app
#android.entrypoint = org.renpy.android.PythonActivity

# (str) python-for-android branch to use, if not master, useful to try
# not yet merged features.
#android.branch = master

#
# iOS specific
#

# (str) Name of the certificate to use for signing the debug version
#ios.codesign.debug = "iPhone Developer: <lastname> <firstname> (<hexstring>)"

# (str) Name of the certificate to use for signing the release version
#ios.codesign.release = %(ios.codesign.debug)s


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 1
