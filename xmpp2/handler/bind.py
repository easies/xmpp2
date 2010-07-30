from uuid import uuid4
from common import PlugOut
from xmpp2.model import Node
import logging


class BindHandler(object):
    NS_BIND = 'urn:ietf:params:xml:ns:xmpp-bind'
    NAMESPACES = {'bind': NS_BIND}

    def __init__(self, client, resource):
        self.client = client
        self.resource = resource

    def get_type(self):
        return 'iq'

    def get_ns(self):
        return 'jabber:client'

    def get_id(self):
        return uuid4().hex

    def start(self):
        node = Node('iq', type='set', id=self.get_id())
        bind = Node('bind', xmlns=self.NS_BIND)
        node.append(bind)
        if self.resource is not None:
            bind.append(Node('resource', self.resource))
        self.client.write(node)
        self.client.process()

    def handle(self, iq):
        jid = iq.xpath('bind:bind/bind:jid', namespaces=self.NAMESPACES)
        if len(jid) > 0:
            self.client._set_jid(jid[0].text)
        return PlugOut()
