import logging
from lxml import etree
from stream import XMLStream
import transport
import auth
from constants import NAMESPACES, NS_TLS
from handler.interface import ExitType
from handler.features import FeaturesHandler
from handler.tls import TLSHandler
from handler.bind import BindHandler


class Client(object):
    """An XMPP client"""

    def __init__(self, host, port=5222, sasl=True, ssl=False):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.stream = None
        self.sock = None
        self.gen = None
        self.features = None
        self.me = None
        self.handlers = []
        self.jid = None

    def add_handler(self, handler):
        self.handlers.append(handler)
        if hasattr(handler, 'start'):
            handler.start()

    def remove_handler(self, handler):
        self.handlers.remove(handler)

    def _set_jid(self, jid):
        if jid is not None:
            self.jid = JID.from_string(jid)

    def initiate(self, sock):
        sock.write('''<?xml version="1.0" encoding="UTF-8">
        <stream:stream xmlns:stream="http://etherx.jabber.org/streams"
            to="%s"
            version="1.0"
            xmlns="jabber:client">''' % self.host)

    def connect(self):
        if self.ssl:
            self._connect_secure()
        else:
            self._connect_plain()

    def _connect_plain(self):
        self.sock = transport.TCP(self.host, self.port)
        self.sock.connect()
        self.initiate(self.sock)
        self.stream = XMLStream(self.sock)
        self.gen = self.stream.generator()

        # process features
        self.add_handler(FeaturesHandler(self))
        self.process()

        if self.features.has_feature('starttls'):
            self.add_handler(TLSHandler(self))
            self.process()

    def _connect_secure(self):
        self.sock = transport.TCP(self.host, self.port)
        self.sock.connect()
        self.upgrade_to_tls()

    def upgrade_to_tls(self):
        """Upgrade the connection to TLS"""
        sock = transport.TCP_SSL(self.sock.sock)
        # Re-initiate the stream.
        self.initiate(sock)
        self.stream = XMLStream(sock)
        self.gen = self.stream.generator()
        self.sock = sock
        self.add_handler(FeaturesHandler(self))

    def auth(self, username, password=None, resource=None):
        mechanisms = self.features.get_feature('mechanisms')
        if mechanisms is not None:
            mechanisms = [m.text for m in mechanisms]
            logging.info(mechanisms)
            sasl = auth.SASL(mechanisms, self, username, password, resource)
            sasl.start_auth()
            self.me = sasl.me()
            self.initiate(self.sock)
            self.gen = self.stream.generator()
            # process features
            self.add_handler(FeaturesHandler(self))
            self.process()
            # bind the resource
            self.bind(resource)
        else:
            nsasl = auth.NON_SASL(self, username, password, resource)
            self.me = nsasl.me()

    def bind(self, resource=None):
        """Bind to the resource. The resulting resource may be different."""
        self.add_handler(BindHandler(self, resource))
        self.process()

    def read(self):
        return self.sock.read()

    def write(self, s):
        if type(s) == str:
            self.sock.write(unicode(s))
        else:
            x = etree.tostring(s, encoding=unicode)
            logging.debug(x)
            self.sock.write(x)

    def process(self):
        element = self.gen.next()
        for handler in self.handlers:
            ret = handler.handle(element)
            if ret is None:
                continue
            elif hasattr(ret, 'act'):
                ret.act(self, handler)

    def disconnect(self):
        self.stream.close()


class JID(object):

    def __init__(self, node, domain, resource):
        self.node = node
        self.domain = domain
        self.resource = resource

    @classmethod
    def from_string(cls, jid):
        """
        >>> x = 'node@domain/resource'
        >>> jid = JID.from_string(x)
        >>> str(jid) == x
        True
        >>> jid.node
        'node'
        >>> jid.domain
        'domain'
        >>> jid.resource
        'resource'
        """
        node, other = jid.split('@', 2)
        domain, resource = other.split('/', 2)
        return JID(node, domain, resource)

    def __str__(self):
        """
        >>> jid = JID('hello', 'example.com', 'xyz')
        >>> jid.__str__()
        'hello@example.com/xyz'
        """
        return '%s@%s/%s' % (self.node, self.domain, self.resource)

    def __repr__(self):
        return self.__str__()
