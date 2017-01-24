#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name             = 'spotter',
    version          = '1.7.1',
    url              = "http://github.com/borntyping/spotter",

    author           = "Sam Clements",
    author_email     = "sam@borntyping.co.uk",

    description      = "A command line tool for watching files and running shell commands when they change.",
    long_description = open('README.rst').read(),
    license          = 'MIT',

    classifiers      = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Topic :: Software Development :: Testing',
        'Topic :: System :: Monitoring',
        'Topic :: Utilities',
    ],

    packages         = find_packages(),

    entry_points     = {
        'console_scripts': [
            'spotter = spotter:main',
        ]
    },

    install_requires = [
        'pyinotify>=0.9.4',
    ],
)
