import logging
from stream import XMLStream
import transport
from constants import NAMESPACES, NS_TLS
from handler import (FeaturesHandler, TLSHandler, BindHandler, SASLHandler,
                     NON_SASLHandler)


class Client(object):
    """An XMPP client"""

    def __init__(self, host, port=5222, ssl=False):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.__stream = None
        self.sock = None
        self.gen = None
        self.features = None
        self.me = None
        self.handlers = {}
        self.__handlers = []
        self.jid = None

    def add_handler(self, handler):
        handler_type = None
        handler_ns = None
        if hasattr(handler, 'get_type'):
            handler_type = handler.get_type()
        if hasattr(handler, 'get_ns'):
            handler_ns = handler.get_ns()
        self.handlers[handler] = (handler_type, handler_ns)
        self.__handlers.append(handler)
        if hasattr(handler, 'start'):
            handler.start()

    def remove_handler(self, handler):
        try:
            self.handlers.pop(handler)
            self.__handlers.remove(handler)
        except:
            pass

    def _set_jid(self, jid):
        if jid is not None:
            self.jid = JID.from_string(jid)

    def initiate(self):
        self.__stream.initiate(self.host)

    # BEWARE, creating a generator will fuck up. DO NOT USE.
    def _create_generator(self):
        self.gen = self.__stream.generator()

    def connect(self):
        if self.ssl:
            self._connect_secure()
        else:
            self._connect_plain()

    def _connect_plain(self):
        self.sock = transport.TCP(self.host, self.port)
        self.sock.connect()
        self.__stream = XMLStream(self.sock)
        self.initiate()
        self.gen = self.__stream.generator()
        # process features
        self.add_handler(FeaturesHandler(self))
        if self.features.has_feature('starttls'):
            self.add_handler(TLSHandler(self))

    def _connect_secure(self):
        self.sock = transport.TCP(self.host, self.port)
        self.sock.connect()
        self.upgrade_to_tls()

    def upgrade_to_tls(self):
        """Upgrade the connection to TLS"""
        sock = transport.TCP_SSL(self.sock.sock)
        # Re-initiate the stream.
        self.__stream = XMLStream(sock)
        self.initiate()
        self.gen = self.__stream.generator()
        self.sock = sock
        self.add_handler(FeaturesHandler(self))

    def auth(self, username, password=None, resource=None):
        mechanisms = self.features.get_feature('mechanisms')
        if mechanisms is not None:
            mechanisms = [m.text for m in mechanisms]
            logging.debug('mechanisms: %s', mechanisms)
            sasl = SASLHandler(self, mechanisms, username, password)
            self.add_handler(sasl)
            self.add_handler(FeaturesHandler(self))
            self.add_handler(BindHandler(self, resource))
        else:
            nsasl = NON_SASLHandler(self, username, password, resource)
            self.add_handler(nsasl)

    def get_id(self):
        return self.__stream['id']

    def write(self, s):
        return self.__stream.write(s)

    def process(self):
        element = self.gen.next()
        tag = element.tag
        for handler in self.__handlers:
            handler_type, xmlns = self.handlers[handler]
            if handler_type is not None:
                if xmlns is not None:
                    if not tag == ('{%s}%s' % (xmlns, handler_type)):
                        continue
                elif not tag.endswith(handler_type):
                    continue
            ret = handler.handle(element)
            if ret is None:
                continue
            elif hasattr(ret, 'act'):
                ret.act(self, handler)

    def disconnect(self):
        self.__stream.close()


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
