import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import logging
import threading
import xmpp2
import time
import select
from xmpp2 import XML

# non-blocking, poll example.
USERNAME = 'yourusername'
PASSWORD = 'yourpassword'
SERVER = 'example.com'

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('xmpp2.xml.handler').setLevel(logging.INFO)

c = xmpp2.Client(SERVER, stream_log_level=xmpp2.LOG_NONE)
c.connect()
c.auth(USERNAME, password=PASSWORD)
c.write(XML.presence.add(XML.priority.add(1)))
c.setblocking(False)

po = select.poll()
po.register(c, select.POLLIN)

while True:
    for fd, event in po.poll():
        msg = c.gen.next()
        if msg:
            sys.stdout.write(msg.pretty_print() + '\n')
