Specifications
==============

This document explain in details all the configuration token you can use in
`buildozer.spec`.

Section [app]
-------------

- `title`: String, title of your application.
  
  It might possible that some characters are not working depending the paltform
  targetted. Best for you is to try and see. Try to avoid too-long title, as
  they will also not fit in the title displayed under the icon.

- `package.name`: String, package name.

  The Package name is one word with only ASCII characters and/or numbers. It
  should not contain any special characters. For example, if your application
  is named `Flat Jewels`, the package name can be `flatjewels`.

- `package.domain`: String, package domain.

  Package domain is a string that reference the company or individual that did
  it. Both domain+name will become your application identifier for Android and
  iOS. Choose it carefully. As an example, when the Kivy`s team is publishing
  an application, the domain starts with `org.kivy`.

- `source.dir`: String, location of your application sources.

  The location must be a directory that contain a `main.py` file. It defaults
  to the same directory as the one `buildozer.spec` is.

- `source.include_exts`: List, files extensions to include.

  By default, not all the file in your `source.dir` are included, but only some
  of them, depending the extension. Ie, we includes `py,png,jpg,kv,atlas`. Feel
  free to add your own extensions, or put an empty value if you want to include
  everything.

- `source.exclude_exts`: List, files extensions to exclude.

  In contrary to `source.include_exts`, you could include all the files you
  want except the one that ends with an extension contain in this token. If
  empty, no files will be excluded by the extensions.

- `source.exclude_dirs`: List, directories to exclude.

  Same as `source.exclude_exts`, but for directory. You can exclude your
  `tests` or `bin` directory with::

    source.exclude_dirs = tests, bin

- `source.exclude_patterns`: List, file to exclude if they match a pattern.

  If you have a more complex application layout, you might need a pattern to
  exclude files. It works also even if you don't have a pattern. For example::

    source.exclude_patterns = license,images/originals/*

- `version.regex`: Regex, Regular expression to capture the version in
  `version.filename`.

  The default capture method of your application version is by grepping a line
  like that::

    __version__ = "1.0"

  The `1.0` will be used as a version.

- `version.filename`: String, default to the main.py.

  Filename to use for capturing the version with `version.regex`.

- `version`: String, manual application version.

  If you don't want to capture the version, comment both of `version.regex` and
  `version.filename`, then put the version you want directly in the `version`
  token::

    # version.regex =
    # version.filename = 
    version = 1.0

- `requirements`: List, Python module or extensions that your application
  require.

  The requirements can be either a name of a recipe in the Python-for-android
  project, or a pure-Python package. For example, if your application require
  Kivy and requests, you need to write::

    requirements = kivy,requests

  If your application try to install a Python extension (ie, a Python package
  that require compilation), and that it doesn't have a recipe associated to
  Python-for-android, it will not work. We explicitely disable the compilation
  here. If you want to make it work, contribute to the Python-for-android
  project by creating a recipe. See :doc:`contribute`

- `garden_requirements`: List, Garden packages to include.

  Add here the list of Kivy's garden package to include. For example::

    garder_requirements = graph

  Please note that if it doesn't work, it might be because of the garden
  package itself. Refer to the author of the package if he already tested it on
  the platform you are targetting, not us.

- `presplash.filename`: String, loading screen of your application.

  Presplash is the image showed on the device when the application is loading.
  It is called presplash on Android, and Loading image on iOS. The image might
  have different requirements depending the platform. Currently, Buildozer
  works well only with Android, iOS support is not great on this.

  The image must be a JPG or PNG, preferable with Power-of-two size. Ie, an
  512x512 image is perfect to target all the devices. The image is not fitted,
  scaled, or anything on the device. If you provide a too-large image, it might
  not fit on small screens.

- `icon.filename`: String, icon of your application.

  The icon of your application. It must be a PNG of 512x512 size to be able to
  cover all the various platform requirements.

- `orientation`: String, orientation of the application.

  Indicate the orientation that your application support. Defaults to
  `landscape`, but can be changed to `portrait` or `all`.

- `fullscreen`: Boolean, fullscreen mode.

  Defaults to true, your application will run in fullscreen. Means the status
  bar will be hidden. If you want to let the user access to the status bar,
  hour, notifications, put to 0.

