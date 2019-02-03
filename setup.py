'''
Buildozer
'''

from setuptools import setup
from os.path import dirname, join
import codecs
import os
import re
import io

here = os.path.abspath(os.path.dirname(__file__))


def find_version(*file_paths):
    # Open in Latin-1 so that we avoid encoding errors.
    # Use codecs.open for Python 2 compatibility
    with codecs.open(os.path.join(here, *file_paths), 'r', 'utf-8') as f:
        version_file = f.read()

    # The version line must have the form
    # __version__ = 'ver'
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


curdir = dirname(__file__)
with io.open(join(curdir, "README.md"), encoding="utf-8") as fd:
    readme = fd.read()
with io.open(join(curdir, "CHANGELOG.md"), encoding="utf-8") as fd:
    changelog = fd.read()

setup(
    name='buildozer',
    version=find_version('buildozer', '__init__.py'),
    description='Generic Python packager for Android / iOS and Desktop',
    long_description=readme + "\n\n" + changelog,
    long_description_content_type='text/markdown',
    author='Mathieu Virbel',
    author_email='mat@kivy.org',
    url='http://github.com/kivy/buildozer',
    license='MIT',
    packages=[
        'buildozer', 'buildozer.targets', 'buildozer.libs', 'buildozer.scripts'
        ],
    package_data={'buildozer': ['default.spec']},
    include_package_data=True,
    install_requires=['pexpect', 'virtualenv', 'sh'],
    classifiers=[
        'Development Status :: 4 - Beta', 'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ],
    entry_points={
        'console_scripts': [
            'buildozer=buildozer.scripts.client:main',
            'buildozer-remote=buildozer.scripts.remote:main'
        ]
    })
