# Contribution Guidelines

Buildozer is part of the [Kivy](https://kivy.org) ecosystem - a large group of
products used by many thousands of developers for free, but it
is built entirely by the contributions of volunteers. We welcome (and rely on) 
users who want to give back to the community by contributing to the project.

Contributions can come in many forms. See the latest 
[Contribution Guidelines](https://github.com/kivy/kivy/blob/master/CONTRIBUTING.md)
for general guidelines of how you can help us.

---

If you would like to work on Buildozer, you can set up a development build:
```bash
git clone https://github.com/kivy/buildozer
cd buildozer
python setup.py build
pip install -e .
```
---

Buildozer uses python-for-android, that is architected to be extensible with 
new recipes and new bootstraps.

If you do develop a new recipe on python-for-android, here is how to test it:

#. Fork `Python for Android <https://github.com/kivy/python-for-android>`_, and
   clone your own version (this will allow easy contribution later)::

```bash
git clone https://github.com/YOURNAME/python-for-android
```

#. Change your `buildozer.spec` to reference your version::

     p4a.source_dir = /path/to/your/python-for-android

#. Copy your recipe into `python-for-android/recipes/YOURLIB/recipe.sh`

#. Rebuild.

When your recipe works, you can ask us to
include it in the python-for-android project, by issuing a Pull Request:

#. Create a branch::

```bash
git checkout --track -b recipe-YOURLIB origin/master
```

#. Add and commit::

```bash
git add python-for-android/recipes/YOURLIB/*
git commit -am 'Add support for YOURLIB`
```  

#. Push to GitHub

```bash
git push origin master
```

#. Go to `https://github.com/YOURNAME/python-for-android`, and you should see
   your new branch and a button "Pull Request" on it. Use it, write a
   description about what you did, and Send!