# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='sample',
    version='0.1.0',
    description='Discord bot for Echo Master League Management',
    long_description=readme,
    author='Orthura',
    author_email='orthura@gmail.com',
    url='https://github.com/EchoMasterLeague/EML-response-bot',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

