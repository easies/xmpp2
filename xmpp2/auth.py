import base64
import logging
from hashlib import sha1
from lxml import etree
from constants import NAMESPACES, NS_AUTH, NS_SASL
from parser import RFC2831


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


class SASL(object):

    def __init__(self, mechanisms, client, username, password, resource):
        self.mechanisms = mechanisms
        self.client = client
        self.username = username
        self.password = password
        self.resource = resource
        self.to = None
        self.start_auth()

    def start_auth(self):
        auth = etree.Element('auth', xmlns=NS_SASL, mechanism='DIGEST-MD5')
        self.write(auth)
        while True:
            element = self.next()
            if element.tag.endswith('challenge'):
                break
        logging.info(etree.tostring(element))
        challenge = base64.b64decode(element.text)
        logging.info(challenge)
        digest_challenge = RFC2831(challenge).get_challenge()
        response = digest_challenge.get_response(self.username, self.password)
        res = etree.Element('response', xmlns=NS_SASL)
        res.text = base64.b64encode(str(response))
        logging.info(str(response))
        self.write(res)
        while True:
            element = self.next()
            if element.tag.endswith('success'):
                element.clear()
                return True
            elif element.tag.endswith('failure'):
                element.clear()
                return False

    def me(self):
        return self.to

    def write(self, s):
        self.client.write(s)

    def next(self):
        return self.client.gen.next()
