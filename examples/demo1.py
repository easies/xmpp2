import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import logging
import xmpp2
from xmpp2 import XML

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('xmpp2.xml.handler').setLevel(logging.INFO)

c = xmpp2.Client('jabber.org', stream_log_level=xmpp2.LOG_STREAM)
c.connect()
try:
    # Expect a failure.
    c.auth('test', password='test')
    assert 1 == 0
except Exception, e:
    sys.stdout.write(str(e))
