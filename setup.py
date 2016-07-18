#!/usr/bin/env python
from setuptools import setup, find_packages

__version__ = '3.0.0'

setup(name='raffaello',
      version=__version__,
      description='Raffaello is a command-line output colorizer',
      author='Carlo Lobrano',
      author_email='c.lobrano@gmail.com',
      url='https://github.com/clobrano/raffaello',

      packages=find_packages('src'),
      package_dir={'': 'src'},
      install_requires=['docopt', ],

      py_modules=['raffaello'],
      entry_points={
          'console_scripts': ['raffaello=raffaello:main'],
          },
      include_package_data=True,
      keywords=['formatter', 'cli', 'colorizer'])
