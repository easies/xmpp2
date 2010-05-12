import logging
from stream import XMLStream
import transport


class Client(object):
    """An XMPP client"""

    def __init__(self, host, port=5222, sasl=True, ssl=False):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.stream = None
        self.sock = None
        self.gen = None

    def initiate(self, sock):
        sock.write('''<?xml version='1.0'?>
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
                break
            elif element.tag.endswith('starttls'):
                starttls = element
        logging.info(element.getchildren())
        logging.info(starttls)
        logging.info(element.xpath('./starttls'))

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
                stream = XMLStream(sock)
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

    def read(self):
        return self.sock.read()

    def write(self, s):
        self.sock.write(s)

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
