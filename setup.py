import os, sys
from setuptools import setup


try:
    with open('README', 'rt') as readme:
        description = '\n' + readme.read()
except IOError:
    # maybe running setup.py from some other dir
    description = ''


setup(
    # metadata
    name='pyelftools',
    description='Library for analyzing ELF files and DWARF debugging information',
    long_description=description,
    license='Public domain',
    version='0.29',
    author='Eli Bendersky',
    maintainer='Eli Bendersky',
    author_email='eliben@gmail.com',
    url='https://github.com/eliben/pyelftools',
    platforms='Cross Platform',
    classifiers = [
        'Programming Language :: Python :: 3',
        ],

    # All packages and sub-packages must be listed here
    packages=[
        'elftools',
        'elftools.elf',
        'elftools.common',
        'elftools.dwarf',
        'elftools.ehabi',
        'elftools.construct', 'elftools.construct.lib',
        ],

    scripts=['scripts/readelf.py']
)
