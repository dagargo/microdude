# -*- coding: utf-8 -*-

from distutils.core import setup
from setuptools import find_packages

setup(name='MicroDude',
    version='1.2.1',
    description='Editor for Arturia MicroBrute',
    author='David García Goñi',
    author_email='dagargo@gmail.com',
    url='https://github.com/dagargo/microdude',
    packages=find_packages(exclude=['doc', 'tests']),
    package_data={'microdude': ['resources/*']},
    license='GNU General Public License v3 (GPLv3)',
    install_requires=['mido<=1.1.16'],
    test_suite='tests',
    tests_require=[]
)
