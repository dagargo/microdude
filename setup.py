# -*- coding: utf-8 -*-

from distutils.core import setup
from setuptools import find_packages

setup(name='MicroDude',
    version='1.0.2',
    description='Editor for Arturia MicroBrute',
    author='David García Goñi',
    author_email='dagargo@gmail.com',
    url='https://github.com/dagargo/microdude',
    packages=find_packages(exclude=['doc', 'test']),
    package_data={'microdude': ['resources/*']},
    license='GNU General Public License v3 (GPLv3)',
    install_requires=['mido']
)
