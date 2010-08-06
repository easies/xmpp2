import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import logging
import threading
import xmpp2
from xmpp2 import XML

USERNAME = 'yourusername'
PASSWORD = 'yourpassword'
SERVER = 'example.com'

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('xmpp2.xml.handler').setLevel(logging.INFO)

c = xmpp2.Client(SERVER, stream_log_level=xmpp2.LOG_STREAM)
c.connect()
c.auth(USERNAME, password=PASSWORD)
c.write(XML.presence.add(XML.priority.add(1)))

for n in c.gen:
    sys.stdout.write(str(n) + '\n')
