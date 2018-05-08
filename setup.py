from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from setuptools import setup

setup(
    name='disktray',
    version='1.0.0',
    author='Junjue Wang',
    author_email='junjuew@cs.cmu.edu',
    packages=['disktray'],
    entry_points={
        'console_scripts': [
            'disktrayapp = disktray.app:main',
            'objectserver.py = disktray.objectserver:main'
        ]
    },
    url='https://github.com/junjuew/gabriel-disk-tray',
    license='LICENSE',
    description='DiskTray Wearable Cognitive Assistance.',
    long_description=open('README.md').read(),
    classifiers=[
        'Programming Language :: Python :: 2.7'
    ]
)
