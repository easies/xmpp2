import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import logging
from xmpp2 import client

logging.basicConfig(level=logging.DEBUG)

c = client.Client('dds-master.ccs.neu.edu')
c.connect()
c.auth('lee-server', resource='test', password='lee-server')

for n in c.stream.generator():
    pass
    # print (n, n.tag, n.attrib, [x for x in n.iter()])
