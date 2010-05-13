import logging
from lxml import etree
from stream import XMLStream
import transport
import auth
from constants import NAMESPACES


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

    def initiate(self, sock):
        sock.write('''<?xml version='1.0'? encoding='UTF-8'>
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
        sock = transport.TCP(self.host, self.port)
        sock.connect()
        self.initiate(sock)
        stream = XMLStream(sock)
        gen = stream.generator()

        # should be stream:features
        starttls = None 
        while True:
            element = gen.next()
            logging.debug(str((element.tag, element.attrib)))
            if element.tag.endswith('features'):
                self.features = element
                break
            elif element.tag.endswith('starttls'):
                starttls = element
        logging.info(etree.tostring(element))

        if starttls is not None:
            # Send starttls request
            logging.info('Sending starttls request')
            sock.write('<starttls xmlns="%s" />' % starttls.nsmap[None])
            element = gen.next()
            if element.tag.endswith('proceed'):
                logging.info('Proceeding with TLS')
                sock = transport.TCP_SSL(sock.sock)
                # Re-initiate the stream.
                self.initiate(sock)
                self.features.clear()
                self.features = None
                stream = XMLStream(sock)
                gen = stream.generator()
            else:
                logging.warn('Not proceeding with TLS')

        self.sock = sock
        self.stream = stream
        self.gen = gen

    def _connect_secure(self):
        sock = transport.TCP(self.host, self.port)
        sock.connect()
        self.sock = transport.TCP_SSL(sock.sock)
        self.initiate(sock)
        self.stream = XMLStream(sock)
        self.gen = self.stream.generator()

    def auth(self, username, password=None, resource=None):
        if self.features is None:
            while True:
                element = self.gen.next()
                if element.tag.endswith('features'):
                    self.features = element
                    break
        logging.info(self.features)
        mechanisms = self.features.xpath('sasl:mechanisms/sasl:mechanism',
                                         namespaces=NAMESPACES)
        logging.info(mechanisms)
        nsasl = auth.NON_SASL([m.text for m in mechanisms], self, username,
                              password, resource)
        self.me = nsasl.me()

    def read(self):
        return self.sock.read()

    def write(self, s):
        if type(s) == str:
            self.sock.write(unicode(s))
        else:
            x = etree.tostring(s, encoding=unicode)
            logging.debug(x)
            self.sock.write(x)

    def disconnect(self):
        self.stream.close()


class JID(object):

    def __init__(self, node, domain, resource):
        self.node = node
        self.domain = domain
        self.resource = resource

    def __str__(self):
        """
        >>> jid = JID('hello', 'example.com', 'xyz')
        >>> jid.__str__()
        'hello@example.com/xyz'
        """
        return '%s@%s/%s' % (self.node, self.domain, self.resource)

    def __repr__(self):
        return self.__str__()
