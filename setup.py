#!/usr/bin/env python

from distutils.core import setup


setup(
    name='xmpp2',
    version='0.2',
    description='An XMPP client',
    long_description='An XMPP client',
    author='Alex Lee',
    author_email='xmpp2@thirdbeat.com',
    url='http://xmpp2.thirdbeat.com',
    packages=['xmpp2', 'xmpp2.handler']
)
