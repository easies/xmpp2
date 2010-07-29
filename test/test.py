import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import logging
from xmpp2 import Client

logging.basicConfig(level=logging.DEBUG)

logging.getLogger('xmpp2.xml.handler').setLevel(logging.INFO)

c = Client('dds-master.ccs.neu.edu')
c.connect()
c.auth('lee-server', password='lee-server')
c.write('<presence><priority>1</priority></presence>')
for n in c.gen:
    print n
