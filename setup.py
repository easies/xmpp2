#!/usr/bin/env python

from distutils.core import setup


setup(
    name='xmpp2',
    version='0.3',
    description='An XMPP client',
    long_description='An XMPP client',
    author='Alex Lee',
    author_email='xmpp2@thirdbeat.com',
    maintainer='Alex Lee',
    maintainer_email='xmpp2@thirdbeat.com',
    url='http://xmpp2.thirdbeat.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers'
        'License :: OSI Approved :: MIT License',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development :: Libraries',
    ],
    packages=['xmpp2', 'xmpp2.handler']
)
