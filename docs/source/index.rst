.. Buildozer documentation master file, created by
   sphinx-quickstart on Sun Apr 20 16:56:31 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Buildozer's documentation!
=====================================

Buildozer is a tool that aim to package mobiles application easily. It
automates the entire build process, download the prerequisites like
python-for-android, Android SDK, NDK, etc.

Buildozer manage a file named `buildozer.spec` in your application directory,
describing your application requirements and settings such as title, icon,
included modules etc. It will use the specification file to create a package
for Android, iOS, and more.

Currently, Buildozer supports packaging for:

- Android: via `Python for Android
  <https://github.com/kivy/python-for-android>`_. You must have a Linux or OSX
  computer to be able to compile for Android.

- iOS: via `Kivy iOS <https://github.com/kivy/kivy-ios>`_. You must have an OSX
  computer to be able to compile for iOS.

- Supporting others platform is in the roadmap (such as .exe for Windows, .dmg
  for OSX, etc.)

If you have any questions about Buildozer, please refer to the `Kivy's user
mailing list <https://groups.google.com/forum/#!forum/kivy-users>`_.

.. toctree::
   :maxdepth: 2

   installation
   quickstart
   specifications

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

