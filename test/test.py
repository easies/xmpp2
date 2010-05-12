import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import logging
from xmpp2 import client

logging.basicConfig(level=logging.DEBUG)

c = client.Client('jabber.org')
c.connect()

for n in c.stream.generator():
    print (n, n.tag, n.attrib)
