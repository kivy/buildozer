.. _specifications:

Specifications
==============
.. rst-class:: lead

  This document explains in detail all the configuration tokens you can use in
  :class:`buildozer.spec`.

Section [app]
-------------

- :class:`title`: String, title of your application.
  
  It might be possible that some characters are not working depending on the
  targeted platform. It's best to try and see if everything works as expected.
  Try to avoid too long titles, as they will also not fit in the title
  displayed under the icon.

- :class:`package.name`: String, package name.

  The Package name is one word with only ASCII characters and/or numbers. It
  should not contain any special characters. For example, if your application
  is named :class:`Flat Jewels`, the package name can be :class:`flatjewels`.

- :class:`package.domain`: String, package domain.

  Package domain is a string that references the company or individual that
  did the app. Both domain+name will become your application identifier for
  Android and iOS, choose it carefully. As an example, when the Kivy`s team
  is publishing an application, the domain starts with :class:`org.kivy`.

- :class:`source.dir`: String, location of your application sources.

  The location must be a directory that contains a :class:`main.py` file. It defaults
  to the directory where :class:`buildozer.spec` is.

- Source Inclusion/Exclusion options.

  - :class:`source.include_exts`: List, file extensions to include.
  - :class:`source.exclude_exts`: List, file extensions to exclude, even if included by
    :class:`source.include_exts`
  - :class:`source.exclude_dirs`: List, directories to exclude.
  - :class:`source.exclude_patterns`: List, files to exclude if they match a pattern.
  - :class:`source.include_patterns`: List, files to include if they match a pattern, even if excluded by
    :class:`source.exclude_dirs` or :class:`source.exclude_patterns`

  By default, not all files are in your :class:`source.dir` are included. You can
  use these options to alter which files are included in your app and which
  are excluded.

  Directories and files starting with a "." are always excluded; this cannot be
  overridden.

  Files that have an extension that is not in :class:`source.include_exts` are excluded.
  (The default suggestion is :class:`py,png,jpg,kv,atlas`. You may want to include other
  file extensions such as resource files: gif, xml, mp3, etc.)  File names that
  have no extension (i.e contain no ".") are not excluded here.
  :class:`source.exclude_exts` takes priority over :class:`source.include_exts` - it excludes any listed extensions
  that were previously included.

  Files and directories in directories listed in :class:`source.exclude_dirs` are excluded. For example, you can exclude your
  :class:`tests` and `bin` directory with::

        source.exclude_dirs = tests, bin

  :class:`source.exclude_patterns` are also excluded. This is useful for excluding individual
  files. For example::

         source.exclude_patterns = license

  These dir and pattern exclusions may be overridden with
  :class:`source.include_patterns` - files and directories that match will once again be included.

  However, `source.include_patterns` does not override the :class:`source.include_exts` nor
  :class:`source.exclude_exts`. :class:`source.include_patterns` also cannot be used to include files or directories that
  start with ".")

- :class:`version.regex`: Regex, Regular expression to capture the version in
  :class:`version.filename`.

  The default capture method of your application version is by grepping a line
  like this::

    __version__ = "1.0"

  The :class:`1.0` will be used as a version.

- :class:`version.filename`: String, defaults to the main.py.

  File to use for capturing the version with :class:`version.regex`.

- :class:`version`: String, manual application version.

  If you don't want to capture the version, comment out both :class:`version.regex`
  and :class:`version.filename`, then put the version you want directly in the
  :class:`version` token::

    # version.regex =
    # version.filename = 
    version = 1.0

- :class:`requirements`: List, Python modules or extensions that your application
  requires.

  The requirements can be either a name of a recipe in the Python-for-android
  project, or a pure-Python package. For example, if your application requires
  Kivy and requests, you need to write::

    requirements = kivy,requests

  If your application tries to install a Python extension (ie, a Python
  package that requires compilation), and the extension doesn't have a recipe
  associated to Python-for-android, it will not work. We explicitly disable
  the compilation here. If you want to make it work, contribute to the
  Python-for-android project by creating a recipe. See :doc:`contribute`.

- :class:`presplash.filename`: String, loading screen of your application.

  Presplash is the image shown on the device during application loading.
  It is called presplash on Android, and Loading image on iOS. The image might
  have different requirements depending the platform. Currently, Buildozer
  works well only with Android, iOS support is not great on this.

  The image must be a JPG or PNG, preferable with Power-of-two size, e.g., a
  512x512 image is perfect to target all the devices. The image is not fitted,
  scaled, or anything on the device. If you provide a too-large image, it might
  not fit on small screens.

- :class:`icon.filename`: String, icon of your application.

  The icon of your application. It must be a PNG of 512x512 size to be able to
  cover all the various platform requirements.

- :class:`orientation`: List, supported orientations of the application.

  Indicate the orientations that your application supports.
  Valid values are: :class:`portrait`, :class:`landscape`, :class:`portrait-reverse`, :class:`landscape-reverse`.
  Defaults to :class:`[landscape]`.

- :class:`fullscreen`: Boolean, fullscreen mode.

  Defaults to true, your application will run in fullscreen. Means the status
  bar will be hidden. If you want to let the user access the status bar,
  hour, notifications, use 0 as a value.

- :class:`home_app`: Boolean, Home App (launcher app) usage.

  Defaults to false, your application will be listed as a Home App (launcher app) if true.

- :class:`display_cutout`: String, display-cutout mode to be used.

  Defaults to :class:`never`. Application will render around the cutout (notch) if set to either :class:`default`, :class:`shortEdges`.
