# -*- coding: utf-8 -*-

from distutils.core import setup
from setuptools import find_packages

setup(name='MicroDude',
    version='2.3',
    description='Editor for Arturia MicroBrute',
    author='David García Goñi',
    author_email='dagargo@gmail.com',
    url='https://github.com/dagargo/microdude',
    packages=find_packages(exclude=['doc', 'tests']),
    package_data={'microdude': ['resources/*']},
    license='GNU General Public License v3 (GPLv3)'
)
