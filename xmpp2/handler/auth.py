import base64
import logging
from uuid import uuid4
from hashlib import sha1
from common import PlugOut
from sasl import DigestMD5
from xmpp2.model import XML

NS_AUTH = 'jabber:iq:auth'
NS_SASL = 'urn:ietf:params:xml:ns:xmpp-sasl'
NAMESPACES = {
    'auth': NS_AUTH,
    'sasl': NS_SASL,
}

class NON_SASLHandler(object):

    def __init__(self, client, username, password, resource):
        self.client = client
        self.username = username
        self.password = password
        self.resource = resource
        self.state = 0

    def start(self):
        # Query for methods
        self.write(XML.iq(type='get', id='auth_1').add(
            XML.query(xmlns=NS_AUTH).add(
                XML.username.add(self.username))))
        self.client.process()

    def handle(self, iq):
        if self.state == 0:
            methods = iq[0][:]
            prefix = '{%s}' % NS_AUTH
            methods = [m.tag.replace(prefix, '') for m in methods]
            logging.info('Requested authentication fields: %s' % methods)
            self.set_attributes(methods)
            self.state = 1
            self.client.process()
        elif self.state == 1:
            # TODO error case
            logging.debug(iq)
            return PlugOut()

    def set_attributes(self, attribs):
        """Auth with digest"""
        iq = XML.iq(type='set', id='auth_2')
        query = XML.query(xmlns=NS_AUTH)
        iq.add(query)
        if 'username' in attribs:
            query.add(XML.username.add(self.username))
        if 'resource' in attribs:
            if not self.resource:
                self.resource = uuid4().hex[:8]
            query.add(XML.resource.add(self.resource))
        if 'digest' in attribs:
            query.add(XML.digest.add(self.get_digest()))
        elif 'password' in attribs:
            query.add(XML.password.add(self.password))
        self.write(iq)
        # TODO error case

    def get_digest(self):
        """The digest is sha1 hash of the stream's id + the password"""
        h = sha1()
        h.update(self.client.get_id() + self.password)
        return h.hexdigest()

    def me(self):
        return self.to

    def write(self, s):
        self.client.write(s)

    def next(self):
        return self.client.gen.next()


class SASLHandler(object):

    def __init__(self, client, mechanisms, username, password, log=False):
        self.client = client
        self.mechanisms = mechanisms
        self.username = username
        self.password = password
        self.log = log
        self.state = 0
        self.is_done = False
        self.sasl_handler = None

    def start(self):
        self.sasl_handler = DigestMD5(self.client, self.username,
                                      self.password)
        mech = 'DIGEST-MD5'
        logging.info('Effective mechanism: %s' % mech)
        self.client.write(XML.auth(xmlns=NS_SASL, mechanism=mech))
        self.effective_mechanism = mech
        self.client.process()

    def handle(self, xml_obj):
        return self.sasl_handler.handle(xml_obj)
