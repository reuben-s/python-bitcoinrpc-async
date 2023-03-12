#!/usr/bin/env python

from distutils.core import setup

setup(
    name='python-bitcoinrpc-async',
    version='1.0.0',
    description='Enhanced version of python-jsonrpc for use with Bitcoin, for async use.',
    long_description="python-bitcoinrpc-async adds asyncronous functionality to the AuthServiceProxy. It includes asyncio compatible methods for making and handling requests, making it easy to integrate into your codebase. With python-bitcoin-rpc you can now take advantage of the benefits of asynchronous programming, using the modern async and await syntax.",
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
