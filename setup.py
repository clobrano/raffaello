#!/usr/bin/env python
from setuptools import setup, find_packages

__version__ = '3.0.1'

setup(name='raffaello',
      version=__version__,
      description='Raffaello command-line output colorizer',
      author='Carlo Lobrano',
      author_email='c.lobrano@gmail.com',
      license="MIT",
      url='https://github.com/clobrano/raffaello',
      keywords=['formatter', 'console', 'colorizer'],
      classifiers=[
           "Development Status :: 5 - Production/Stable",
           "Topic :: Utilities",
           "Topic :: System :: Logging",
      ],
      packages=find_packages('src'),
      package_dir={'': 'src'},
      install_requires=['docopt', ],

      py_modules=['raffaello'],
      entry_points={
          'console_scripts': ['raffaello=raffaello:main'],
      },
      include_package_data=True,
      )
