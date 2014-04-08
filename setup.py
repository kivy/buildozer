from distutils.core import setup

import buildozer

setup(
    name='buildozer',
    version=buildozer.__version__,
    author='Mathieu Virbel',
    author_email='mat@kivy.org',
    url='http://github.com/kivy/buildozer',
    license='MIT',
    install_requires=[
        'pexpect'],
    packages=[
        'buildozer',
        'buildozer.targets'],
    package_data={'buildozer': ['default.spec']},
    scripts=['tools/buildozer', 'tools/buildozer-remote'],
    description='Generic Python packager for Android / iOS and Desktop'
)
