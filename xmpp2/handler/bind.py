from uuid import uuid4
from lxml import etree
from common import PlugOut


class BindHandler(object):
    NS_BIND = 'urn:ietf:params:xml:ns:xmpp-bind'
    NAMESPACES = {'bind': NS_BIND}

    def __init__(self, client, resource):
        self.client = client
        self.resource = resource

    def get_id(self):
        return uuid4().hex

    def start(self):
        iq = etree.Element('iq', type='set', id=self.get_id())
        bind = etree.SubElement(iq, 'bind', xmlns=self.NS_BIND)
        if self.resource is not None:
            # resource = etree.SubElement(bind, 'resource')
            # resource.text = str(resource)
            etree.SubElement(bind, 'resource').text = str(resource)
        self.client.write(iq)
        self.client.process()

    def handle(self, iq):
        jid = iq.xpath('bind:bind/bind:jid', namespaces=self.NAMESPACES)
        if len(jid) > 0:
            self.client._set_jid(jid[0].text)
        return PlugOut()
