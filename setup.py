#!/usr/bin/env python
from setuptools import setup, find_packages
from raffaello import __version__

setup(name = 'raffaello',
        version = __version__,
        description = 'Raffaello is a command-line output colorizer',
        author = 'Carlo Lobrano',
        author_email = 'c.lobrano@gmail.com',
        url = 'https://github.com/clobrano/raffaello',
        py_modules = ['raffaello'],
        long_description = open('README.md').read(),
        packages = find_packages(),
        entry_points = {'console_scripts': ['raffaello = raffaello:main'], },
        include_package_data = True,
    )
