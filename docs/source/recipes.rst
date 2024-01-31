Recipes
=======

Python apps may depend on third party packages and extensions.

Most packages are written in pure Python, and Buildozer can generally used them
without any modification.

However, some packages and Python extensions require modification to work on
mobile platforms.

For example, for extensions and packages that depend on C or other programming
languages, the default compilation instructions may not work for the target;
The ARM compiler and Android NDK introduce special requirements that the library
may not handle correctly

For such cases, a "recipe" is required. A recipe allows you to compile libraries
and Python extension for the mobile by patching them before use.

python-for-android and Kivy for iOS come, batteries included, with a number of
recipes for the most popular packages.

However, if you use a novel package - and there are no pure Python equivalents that
you can substitute in - you may need to write (or commission) your own recipe. We
would welcome your recipe as a contribution to the project to help the next developer
who wants to use the same library.

More instructions on how to write your own recipes is available in the
`Kivy for iOS <https://github.com/kivy/kivy-ios/>`_ and
`python-for-android documentation <https://python-for-android.readthedocs.io/en/latest/recipes/>`_.

Instructions on how to test your own recipes from Buildozer is available in the
`latest Buildozer Contribution Guidelines <https://github.com/kivy/buildozer/blob/master/CONTRIBUTING.md>`_.
