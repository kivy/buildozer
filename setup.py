from distutils.core import setup

setup(
    name='buildozer',
    version='0.1',
    author='Mathieu Virbel',
    author_email='mat@kivy.org',
    url='http://github.com/kivy/buildozer',
    license='MIT',
    packages=[
        'buildozer',
        'buildozer.targets'],
    scripts=['tools/buildozer'],
    description='Generic Python packager for Android / iOS and Desktop'
)
