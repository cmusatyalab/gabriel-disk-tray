from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from distutils.core import setup

setup(
    name='disktray',
    version='1.0.0',
    author='Junjue Wang',
    author_email='junjuew@cs.cmu.edu',
    packages=['disktray'],
    scripts=['bin/disktrayapp.py'],
    url='https://github.com/junjuew/gabriel-disk-tray',
    license='LICENSE',
    description='DiskTray Wearable Cognitive Assistance.',
    long_description=open('README.md').read(),
    classifiers=[
        'Programming Language :: Python :: 2.7'
    ]
)
