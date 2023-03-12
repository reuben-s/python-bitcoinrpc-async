#!/usr/bin/env python

from distutils.core import setup

setup(
    name='python-bitcoinrpc-async',
    version='1.0.0',
    description='Enhanced version of python-jsonrpc for use with Bitcoin, for async use.',
    long_description=open('README.md').read(),
    author='Reuben S',
    maintainer='Reuben S',
    url='https://github.com/reuben-s/python-bitcoinrpc-async',
    packages=['bitcoinrpcasync'],
    install_requires=[
        'aiohttp'
    ],
    classifiers=[
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)', 'Operating System :: OS Independent'
    ]
)
