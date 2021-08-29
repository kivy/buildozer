Quickstart
==========

Let's get started with Buildozer!

Init and build for Android
--------------------------

#. Buildozer will try to guess the version of your application, by searching a
   line like `__version__ = "1.0.3"` in your `main.py`. Ensure you have one at
   the start of your application. It is not mandatory but heavily advised.

#. Create a `buildozer.spec` file, with::

    buildozer init

#. Edit the `buildozer.spec` according to the :ref:`specifications`. You should
   at least change the `title`, `package.name` and `package.domain` in the
   `[app]` section.

#. Start a Android/debug build with::

    buildozer -v android debug

#. Now it's time for a coffee / tea, or a dinner if you have a slow computer.
   The first build will be slow, as it will download the Android SDK, NDK, and
   others tools needed for the compilation.
   Don't worry, thoses files will be saved in a global directory and will be
   shared across the different project you'll manage with Buildozer.

#. At the end, you should have an APK or AAB file in the `bin/` directory.


Run my application
------------------

Buildozer is able to deploy the application on your mobile, run it, and even
get back the log into the console. It will work only if you already compiled
your application at least once::

    buildozer android deploy run logcat

For iOS, it would look the same::

    buildozer ios deploy run

You can combine the compilation with the deployment::

    buildozer -v android debug deploy run logcat

You can also set this line at the default command to do if Buildozer is started
without any arguments::

    buildozer setdefault android debug deploy run logcat
    
    # now just type buildozer, and it will do the default command
    buildozer

To save the logcat output into a file named `my_log.txt` (the file will appear in your current directory)::

    buildozer -v android debug deploy run logcat > my_log.txt
    
To see your running application's print() messages and python's error messages, use:

::

    buildozer -v android deploy run logcat | grep python

Run my application from Windows 10
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Plug your Android device on a USB port.

- Open Windows PowerShell, go into the folder where you installed the Windows version of ADB, and activate the ADB daemon. When the daemon is started you must see a number besides the word "device" meaning your device was correctly detected. In case of trouble, try another USB port or USB cable.

::

    cd C:\platform-tools\
    .\adb.exe devices

- Open the Linux distribution you installed on Windows Subsystem for Linux (WSL) and proceed with the deploy commands:

::

    buildozer -v android deploy run
    
It is important to notice that Windows ADB and Buildozer installed ADB must be the same version. To check the versions, open PowerShell and type:

::

    cd C:\platform-tools\
    .\adb.exe version
    wsl
    cd ~/.buildozer/android/platform/android-sdk/platform-tools/
    ./adb version

Install on non-connected devices
--------------------------------

If you have compiled a package, and want to share it easily with others
devices, you might be interested with the `serve` command. It will serve the
`bin/` directory over HTTP. Then you just have to access to the URL showed in
the console from your mobile::

    buildozer serve

