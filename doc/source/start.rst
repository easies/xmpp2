===============
Getting Started
===============

xmpp2 is an `XMPP`_ client library much like `xmpppy`_.

Sample code::

    import logging
    import xmpp2
    from xmpp2 import XML

    USERNAME = 'USERNAME' # @gmail.com
    PASSWORD = 'PASSWORD'
    RESOURCE = 'hello'
    FRIEND = 'friend@example.com'

    client = xmpp2.Client('talk.google.com', domain='gmail.com')
    client.connect()
    client.auth(USERNAME, PASSWORD, RESOURCE)
    client.write(XML.presence.add(XML.priority.add(1)))
    client.write(XML.message(to=FRIEND)
            .add(XML.body.add("Hello World form Python")))
    for n in client.gen:
        print n.pretty_print()

.. _XMPP: http://xmpp.org/
.. _xmpppy: http://xmpppy.sourceforge.net/
