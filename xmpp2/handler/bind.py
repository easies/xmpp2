from uuid import uuid4
from common import PlugOut
from xmpp2.model import XML
import logging


class BindHandler(object):
    NS_BIND = 'urn:ietf:params:xml:ns:xmpp-bind'
    NAMESPACES = {'bind': NS_BIND}

    def __init__(self, client, resource):
        self.client = client
        self.resource = resource

    def get_type(self):
        return 'iq'

    def get_id(self):
        return uuid4().hex

    def start(self):
        iq = (XML.iq(type='set', id=self.get_id())
                .add(XML.bind(xmlns=self.NS_BIND)))
        if self.resource is not None:
            iq[0].add(XML.resource.add(self.resource))
        self.client.write(iq)
        self.client.process()

    def handle(self, iq):
        try:
            jid = iq[0][0].text
            self.client._set_jid(jid)
        except:
            pass
        return PlugOut()
