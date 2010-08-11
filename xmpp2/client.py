import logging
from stream import XMLStream
import transport
from constants import NAMESPACES, NS_TLS, LOG_SOCKET, LOG_STREAM, LOG_NONE
from handler import (FeaturesHandler, TLSHandler, BindHandler, SASLHandler,
                     NON_SASLHandler)


class Client(object):
    """An XMPP client"""

    def __init__(self, host, port=5222, ssl=False, stream_log_level=LOG_NONE,
                 domain=None):
        """
        :param host: The hostname in which to connect.
        :param port: The port number (default 5222).
        :param ssl: Enable SSL to begin with (the client will automatically
                    try starttls regardless of this flag).
        :param stream_log_level: Set the log level of the stream layer. See
                                 LOG_SOCKET, LOG_STREAM, and LOG_NONE from
                                 `xmpp2.constants`.
        :param domain: Override the domain name sent with the stream tag.

        """
        self.host = host
        self.port = port
        self.domain = host
        if domain:
            self.domain = domain
        self.ssl = ssl
        self.__stream = None
        self.sock = None
        self.gen = None
        self.features = None
        self.me = None
        self.handlers = {}
        self.__handlers = []
        self.jid = None
        self.stream_log_level = stream_log_level

    def add_handler(self, handler):
        """
        :param handler: The handler to attach to the client.
        """
        handler_type = ''
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
        """
        :param handler: Remove the given handler from the client.
        """
        try:
            self.handlers.pop(handler)
            self.__handlers.remove(handler)
        except:
            pass

    def _set_jid(self, jid):
        if jid is not None:
            self.jid = JID.from_string(jid)

    def initiate(self):
        self.__stream.initiate(self.domain)

    # BEWARE, creating a generator will fuck up. DO NOT USE.
    def _create_generator(self):
        self.gen = self.__stream.generator()

    def connect(self):
        """Connect to the host."""
        if self.ssl:
            self._connect_secure()
        else:
            self._connect_plain()

    def fileno(self):
        """
        :rtype: `integer`
        :return: The file descriptor number from the underlying stream.
        """
        return self.__stream.fileno()

    def setblocking(self, block):
        """
        Set the blocking mode on the underlying stream.

        :param block: Either True or False.
        """
        self.__stream.setblocking(block)

    def __create_stream(self):
        return XMLStream(self.sock, log_level=self.stream_log_level)

    def _connect_plain(self):
        self.sock = transport.TCP(self.host, self.port)
        self.sock.connect()
        self.__stream = self.__create_stream()
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
        self.sock = transport.TCP_SSL(self.sock.sock)
        # Re-initiate the stream.
        self.__stream = self.__create_stream()
        self.initiate()
        self.gen = self.__stream.generator()
        self.add_handler(FeaturesHandler(self))

    def auth(self, username, password=None, resource=None):
        """
        Authorize yourself with the server.

        :param username: The username.
        :param password: The password (almost optional).
        :param resource: The resource to bind (optional).
        """
        mechanisms = self.features.get_feature('mechanisms')
        if mechanisms is not None:
            mechanisms = [m.text for m in mechanisms]
            logging.info('SASL mechanisms: %s', mechanisms)
            sasl = SASLHandler(self, mechanisms, username, password)
            self.add_handler(sasl)
            self.add_handler(FeaturesHandler(self))
            self.add_handler(BindHandler(self, resource))
        else:
            nsasl = NON_SASLHandler(self, username, password, resource)
            self.add_handler(nsasl)

    def get_id(self):
        """
        :return: The ID of the XML document (of the stream).
        :rtype: string
        """
        return self.__stream.get_id()

    def write(self, s):
        """
        Writes the given object to the server.

        :param s: An XMLObject or a string.
        """
        return self.__stream.write(s)

    # Process a "message".
    def process(self):
        """
        Reads from the server. A popped XML stanza will be passed to the
        handlers if the (tag, namespace) combination matches.
        """
        # An XML element
        element = self.gen.next()
        tag = element.tag
        # Loop through the handlers
        for handler in self.__handlers:
            # The handler_type is the tag.
            handler_type, xmlns = self.handlers[handler]
            if xmlns is not None:
                if not tag == ('{%s}%s' % (xmlns, handler_type)):
                    continue
            elif not tag.endswith(handler_type):
                continue
            # Handle the element.
            ret = handler.handle(element)
            # The returned object is a post-process handler.
            # It is passed in the client and the handler itself.
            if ret is None:
                continue
            elif hasattr(ret, 'act'):
                ret.act(self, handler)

    def disconnect(self):
        """Close the stream."""
        self.__stream.close()


class JID(object):

    def __init__(self, node, domain, resource):
        """
        :param node: The name of the node (the username).
        :param domain: The name of the server.
        :param resource: The name of the resource.
        """
        self.node = node
        self.domain = domain
        self.resource = resource

    @classmethod
    def from_string(cls, jid):
        """
        :param jid: The JID string to parse.
        :rtype: `JID`
        :return: A JID.

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

    def get_stripped(self):
        """
        :rtype: :class:`string`
        :return: The JID string without the resource.
        """
        return '%s@%s' % (self.node, self.domain)

    def __str__(self):
        """
        >>> jid = JID('hello', 'example.com', 'xyz')
        >>> jid.__str__()
        'hello@example.com/xyz'
        """
        return '%s@%s/%s' % (self.node, self.domain, self.resource)

    def __repr__(self):
        return self.__str__()
