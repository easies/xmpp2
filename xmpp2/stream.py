import os
import logging
import libxml2
from constants import NS_STREAM, NS_CLIENT, LOG_SOCKET, LOG_STREAM, LOG_NONE
from model import XMLObject


class XMLStream(object):
    """
    An XML stream is a proper XML document. In the context of core XMPP
    standards, it contains <message/>, <presence/>, or <iq/>, as stanzas.
    `RFC3920`_

    .. _RFC3920: http://www.ietf.org/rfc/rfc3920.txt
    """

    def __init__(self, sock, ns=NS_STREAM, tag='stream', log_level=LOG_NONE):
        self.__sock = sock
        self.__handler = None
        self.__log_level = log_level
        self.tag = tag
        self.block = True
        if ns:
            self.tag = '{%s}%s' % (ns, tag)
        if log_level == LOG_SOCKET:
            def logged_read():
                chunk = self.__sock.read()
                logging.debug('socket read:\n%s', chunk)
                return chunk
            def logged_write(s):
                chunk = unicode(s)
                logging.debug('socket write:\n%s', chunk)
                return self.__sock.write(chunk)
            self.read = logged_read
            self.write = logged_write
        elif log_level == LOG_STREAM:
            def logged_write_stream(s):
                chunk = unicode(s)
                self.__do_log('stream write:\n%s', s)
                return self.__sock.write(chunk)
            self.read = self.__sock.read
            self.write = logged_write_stream
        else:
            self.read = self.__sock.read
            self.write = lambda s: self.__sock.write(unicode(s))

    def setblocking(self, block):
        """
        Set the socket blocking flag.

        :param block: Either True or False.
        """
        self.block = block

    def __do_log(self, message, *args):
        if os.environ.has_key('TERM'):
            a = []
            for x in args:
                if hasattr(x, 'pretty_print'):
                    x = '\x1b[36;1m%s\x1b[0m' % x.pretty_print()
                a.append(x)
            logging.debug(message, *a)
        else:
            logging.debug(message, *args)

    def fileno(self):
        """Returns the file descriptor of the socket."""
        return self.__sock.fileno()

    def initiate(self, host, xmlns_stream=NS_STREAM, xmlns=NS_CLIENT):
        """Initiates the XML stream. Writes the start tag over the socket."""
        self.write('''<?xml version="1.0" encoding="UTF-8"?>
            <stream:stream xmlns:stream="%s" to="%s" version="1.0"
            xmlns="%s">''' % (xmlns_stream, host, xmlns))

    def __getitem__(self, key):
        return self.__handler.get_root().attributes[key]

    def get_id(self):
        """Returns the ID of the document. The ID is set by the server."""
        try:
            return self['id']
        except:
            pass

    def generator(self):
        """
        Creates the generator that yields :class:`~xmpp2.model.XMLObject`\ s from the
        stream.
        """
        # Create the handler.
        self.__handler = Handler()
        # Create the parser context (this is a C library).
        context = libxml2.createPushParser(self.__handler, '', 0, None)
        while True:
            # Read from the socket.
            try:
                chunk = self.read(block=self.block)
            except KeyboardInterrupt:
                # A SIGINT stops the show.
                raise StopIteration
            except:
                # Non-blocking read/recv threw an error
                yield None
                continue
            # Parse the chunk that was read. This will trigger the handler,
            # which will put finished top-level nodes like presence and
            # message into its queue.
            context.parseChunk(chunk, len(chunk), 0)
            # Empty out the queue, so that we can act on it.
            for node in self.__handler.empty_queue():
                if self.__log_level == LOG_STREAM:
                    self.__do_log('stream read:\n%s', node)
                yield node

    def close(self):
        """Closes the underlying socket."""
        self.__sock.close()


# The object for handling libxml2's event callbacks.
class Handler(object):

    def __init__(self, logger_name='xmpp2.xml.handler'):
        self.queue = []
        self.stack = []
        self.logger = logging.Logger(logger_name)

    def __getattr__(self, name):
        self.logger.debug('__getattr__ %s', name)
        return super(self.__class__, self).__getattr__(name)

    def empty_queue(self):
        ret = self.queue
        self.queue = []
        return ret

    def get_root(self):
        return self.stack[0]

    def startElement(self, tag, attrs):
        self.logger.debug('startElement: tag: %s depth: %d %s', tag,
                          len(self.stack), attrs)
        if not attrs:
            attrs = {}
        self.stack.append(XMLObject(tag)(**attrs))

    def has_stream(self):
        return self.stack and self.stack[0].tag == 'stream:stream'

    def endElement(self, tag):
        depth = len(self.stack)
        self.logger.debug('endElement  : tag: %s depth: %d', tag, depth)
        node = self.stack.pop()
        # Pop at 2.
        # The first element is the root (<stream:stream>).
        if depth == 2:
            self.queue.append(node)
            return
        last = self.stack[depth - 2]
        last.append(node)

    def characters(self, data):
        self.logger.debug('characters  : %s', data)
        last = self.stack[len(self.stack) - 1]
        last.append(data)

    def warning(self, msg):
        self.logger.warn('parser: %s', msg)

    def error(self, msg):
        self.logger.error('parser: %s', msg)

    def fatalError(self, msg):
        self.logger.fatal('parser: %s', msg)
