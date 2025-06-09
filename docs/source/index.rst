.. _introduction:

Welcome to Buildozer's documentation!
=====================================

.. rst-class:: lead

   Generic Python packager for Android and iOS.

Overview
--------

.. figure:: /_static/images/banner.svg
   :alt: Buildozer
   :height: 300px
   :align: center

Buildozer is a development tool for turning Python
applications into binary packages ready for installation on any of a number of
platforms, including mobile devices. It automates the entire build process.

The app developer provides a single :class:`buildozer.spec` file, which describes the
application's requirements and settings, such as title and icons. Buildozer can
then create installable packages for Android, iOS, Windows, macOS and/or Linux.

Buildozer has features to make
building apps using the `Kivy framework <https://kivy.org/doc/stable/>`_ easier,
but it can be used independently - even with other GUI frameworks.

.. note::
   python-for-android toolchain only runs on Linux or macOS. (On Windows, a Linux emulator is
   required.)

   kivy-ios toolchain only runs on macOS.

Buildozer is managed by the `Kivy Team <https://kivy.org/about.html>`_. It relies
on its sibling projects:
`python-for-android toolchain <https://python-for-android.readthedocs.io/en/latest/>`_ for
Android packaging, and
`kivy-ios toolchain <https://github.com/kivy/kivy-ios/>`_ for iOS packaging.

Buildozer is released and distributed under the terms of the MIT license. You should have received a
copy of the MIT license alongside your distribution. Our
`latest license <https://github.com/kivy/buildozer/blob/master/LICENSE>`_
is also available.


.. note::
   This tool is has no relation to the online build service, `buildozer.io`.


.. toctree::
   :hidden:

   Introduction <self>

.. toctree::
   :hidden:

   installation
   quickstart
   specifications
   recipes
   faq
   contribute
   contact

