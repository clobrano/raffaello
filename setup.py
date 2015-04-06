#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name = 'Raffaello',
        version = '1.1.0',
        description = 'Raffaello is a command-line output colorizer',
        author = 'Carlo Lobrano',
        author_email = 'clobrano@gmail.com',
        url = 'https://github.com/clobrano/raffaello',
        long_description = open('README.md').read(),
        license = 'LICENCE',
        packages = find_packages(),
        scripts = ['raffaello'],

        package_data = {
            'examples' : ['*.cfg'],
            },
        )
