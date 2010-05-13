import logging
from hashlib import sha1
from constants import NAMESPACES, NS_AUTH
from lxml import etree


class NON_SASL(object):

    def __init__(self, mechanisms, client, username, password, resource):
        self.mechanisms = mechanisms
        self.client = client
        self.username = username
        self.password = password
        self.resource = resource
        self.to = None
        self.start_auth()

    def start_auth(self):
        # Query for methods
        iq = etree.Element('iq', type='get', id='1')
        query = etree.SubElement(iq, 'query', xmlns=NS_AUTH)
        username = etree.SubElement(query, 'username')
        username.text = self.username
        self.write(iq)
        # Get the response
        while True:
            element = self.next()
            if element.tag.endswith('iq'):
                break
        logging.info(etree.tostring(element))

        methods = element.xpath('auth:query/*', namespaces=NAMESPACES)
        prefix = '{%s}' % NS_AUTH
        self.set_attributes([m.tag.replace(prefix, '') for m in methods])

    def set_attributes(self, attribs):
        """Auth with digest"""
        iq = etree.Element('iq', type='set', id='2')
        query = etree.SubElement(iq, 'query', xmlns=NS_AUTH)
        if 'username' in attribs:
            username = etree.SubElement(query, 'username')
            username.text = self.username
        if 'resource' in attribs:
            resource = etree.SubElement(query, 'resource')
            resource.text = self.resource
        if 'digest' in attribs:
            digest = etree.SubElement(query, 'digest')
            digest.text = self.get_digest()
        self.write(iq)
        while True:
            element = self.next()
            if element.tag.endswith('iq'):
                break
        # TODO error case
        self.to = element.xpath('@to')[0]
        logging.info(self.to)

    def get_digest(self):
        """The digest is sha1 hash of the stream's id + the password"""
        logging.info('id <%s>', self.client.stream.id)
        h = sha1()
        h.update(self.client.stream.id + self.password)
        return h.hexdigest()

    def me(self):
        return self.to

    def write(self, s):
        self.client.write(s)

    def next(self):
        return self.client.gen.next()
