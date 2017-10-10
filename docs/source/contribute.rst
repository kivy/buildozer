Contribute
==========


Write your own recipe
---------------------

A recipe allows you to compile libraries / python extension for the mobile.
Most of the time, the default compilation instructions doesn't work for the
target, as ARM compiler / Android NDK introduce specifities that the library
you want doesn't handle correctly, and you'll need to patch. Also, because the
Android platform cannot load more than 64 inline dynamic libraries, we have a
mechanism to bundle all of them in one to ensure you'll not hit this
limitation.

To test your own recipe via Buildozer, you need to:

#. Fork `Python for Android <http://github.com/kivy/python-for-android>`_, and
   clone your own version (this will allow easy contribution later)::

     git clone http://github.com/YOURNAME/python-for-android

#. Change your `buildozer.spec` to reference your version::

     p4a.source_dir = /path/to/your/python-for-android

#. Copy your recipe into `python-for-android/recipes/YOURLIB/recipe.sh`

#. Rebuild.

When you correctly get the compilation and your recipe works, you can ask us to
include it in the python-for-android project, by issuing a Pull Request:

#. Create a branch::

     git checkout --track -b recipe-YOURLIB origin/master

#. Add and commit::

     git add python-for-android/recipes/YOURLIB/*
     git commit -am 'Add support for YOURLIB`

#. Push to Github

     git push origin master

#. Go to `http://github.com/YOURNAME/python-for-android`, and you should see
   your new branch and a button "Pull Request" on it. Use it, write a
   description about what you did, and Send!
