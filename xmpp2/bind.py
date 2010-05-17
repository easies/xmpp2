from lxml import etree
from constants import NAMESPACES, NS_BIND


class Bind(object):

    def __init__(self, client):
        self.client = client

    def bind(self, resource=None):
        """Bind the resource to the server and return the resulting jid."""
        iq = etree.Element('iq', type='set', id='bind_1')
        bind = etree.SubElement(iq, 'bind', xmlns=NS_BIND)
        if resource is not None:
            res = etree.SubElement(bind, 'resource')
            res.text = str(resource)
        self.write(iq)
        result = self.next()
        jid = result.xpath('bind:bind/bind:jid', namespaces=NAMESPACES)
        if len(jid) > 0:
            return jid[0].text

    def write(self, s):
        self.client.write(s)

    def next(self):
        return self.client.gen.next()
