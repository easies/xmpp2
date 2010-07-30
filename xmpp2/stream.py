import copy
import logging
import libxml2
from constants import NS_STREAM, NS_CLIENT
from model import Node


class XMLStreamError(Exception):
    pass


def log(message, *args):
    import os
    if os.environ.has_key('TERM'):
        message = '\x1b[36;1m%s\x1b[0m' % message
    logging.debug(message, *args)


class XMLStream(object):

    def __init__(self, sock, ns=NS_STREAM, tag='stream', should_log=True):
        self.__sock = sock
        self.attrib = {}
        self.root = None
        self.should_log = should_log
        if ns:
            self.tag = '{%s}%s' % (ns, tag)
        else:
            self.tag = tag

    def read(self, *args, **kwargs):
        return self.__sock.read()

    def write(self, s):
        x = unicode(s)
        if hasattr(s, 'pretty_print'):
            self.log('\n' + s.pretty_print())
        else:
            self.log(x)
        return self.__sock.write(x)

    def initiate(self, host, xmlns_stream=NS_STREAM, xmlns=NS_CLIENT):
        self.write('''<?xml version="1.0" encoding="UTF-8"?>
            <stream:stream xmlns:stream="%s" to="%s" version="1.0"
            xmlns="%s">''' % (xmlns_stream, host, xmlns))

    def __getitem__(self, key):
        return self.attrib[key]

    def get_id(self):
        if self.attrib.has_key('id'):
            return self.attrib['id']
        return None

    def generator(self):
        # Create the handler.
        handler = Handler()
        # Create the parser context (this is a C library).
        context = libxml2.createPushParser(handler, '', 0, None)
        while True:
            # Read from the socket.
            chunk = self.read()
            logging.debug('read: %s', chunk)
            # Parse the chunk that was read. This will trigger the handler,
            # which will put finished top-level nodes like presence and
            # message into its queue.
            context.parseChunk(chunk, len(chunk), 0)
            # Empty out the queue, so that we can act on it.
            for node in handler.empty_queue():
                logging.debug('yielding: %s %s', node.tag,
                              node.get_attributes())
                yield node

    def log(self, message, *args):
        if self.should_log:
            log(message, *args)

    def close(self):
        self.__sock.close()


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

    def startElement(self, tag, attrs):
        self.logger.debug('startElement: tag: %s depth: %d %s', tag,
                      len(self.stack), attrs)
        if not attrs:
            attrs = {}
        node = Node(tag, **attrs)
        self.stack.append(node)

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
