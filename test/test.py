import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import logging
import xmpp2
from xmpp2 import XML

logging.basicConfig(level=logging.DEBUG)

logging.getLogger('xmpp2.xml.handler').setLevel(logging.INFO)

c = xmpp2.Client('dds-master.ccs.neu.edu', stream_log_level=xmpp2.LOG_STREAM)
c.connect()
c.auth('lee-server', password='lee-server')
print 'Got JID: %s' % c.jid
c.write(XML.presence.add(XML.priority.add(1)))
print 'Handlers: %s' % c.handlers
print 'ID: %s' % c.get_id()
for n in c.gen:
    print n
