import base64
import logging
from hashlib import sha1
from lxml import etree
from constants import NAMESPACES, NS_AUTH, NS_SASL
from parser import RFC2831


class NON_SASL(object):

    def __init__(self, client, username, password, resource):
        self.client = client
        self.username = username
        self.password = password
        self.resource = resource
        self.to = None

    def start_auth(self):
        # Query for methods
        iq = etree.Element('iq', type='get', id='auth_1')
        query = etree.SubElement(iq, 'query', xmlns=NS_AUTH)
        username = etree.SubElement(query, 'username')
        username.text = self.username
        self.write(iq)
        # Get the response
        iq = self.next()

        methods = iq.xpath('auth:query/*', namespaces=NAMESPACES)
        prefix = '{%s}' % NS_AUTH
        self.set_attributes([m.tag.replace(prefix, '') for m in methods])

    def set_attributes(self, attribs):
        """Auth with digest"""
        iq = etree.Element('iq', type='set', id='auth_2')
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
        iq = self.next()
        # TODO error case
        self.to = iq.xpath('@to')[0]

    def get_digest(self):
        """The digest is sha1 hash of the stream's id + the password"""
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
        self.rspauth = None

    def start_auth(self):
        auth = etree.Element('auth', xmlns=NS_SASL, mechanism='DIGEST-MD5')
        self.write(auth)
        challenge_element = self.next()
        challenge = base64.b64decode(challenge_element.text)
        digest_challenge = RFC2831(challenge).get_challenge()
        response = digest_challenge.get_response(self.username, self.password)
        res = etree.Element('response', xmlns=NS_SASL)
        res.text = base64.b64encode(str(response))
        self.write(res)
        element = self.next()
        if element.tag.endswith('success'):
            rspauth = base64.b64decode(element.text)
            self.rspauth = rspauth.lstrip('rspauth=')
        elif element.tag.endswith('challenge'):
            rspauth = base64.b64decode(element.text)
            self.rspauth = rspauth.lstrip('rspauth=')
            self.write(Etree.element('response', xmlns=NS_SASL))
            self.next() # burn one, a success message
        else: pass # stream ends.

    def me(self):
        return self.to

    def write(self, s):
        self.client.write(s)

    def next(self):
        return self.client.gen.next()
