#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='pycta',
    version="0.0.1",
    packages=find_packages(include=["pycta*"]),
    author='Thomas Schmelzer',
    author_email='thomas.schmelzer@gmail.com',
    description='', install_requires=['pandas>=0.24.0']
)
