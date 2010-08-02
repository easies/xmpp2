import os
import copy
import logging
import libxml2
from constants import NS_STREAM, NS_CLIENT
from model import XMLObject


class XMLStream(object):

    def __init__(self, sock, ns=NS_STREAM, tag='stream', should_log=True):
        self.__sock = sock
        self.attrib = {}
        self.root = None
        self.should_log = should_log
        self.tag = tag
        if ns:
            self.tag = '{%s}%s' % (ns, tag)

    def read(self, *args, **kwargs):
        chunk = self.__sock.read()
        self.log('read: %s', chunk)
        return chunk

    def write(self, s):
        x = unicode(s)
        self.log('\n%s', s)
        return self.__sock.write(x)

    def fileno(self):
        return self.__sock.fileno()

    def initiate(self, host, xmlns_stream=NS_STREAM, xmlns=NS_CLIENT):
        self.write('''<?xml version="1.0" encoding="UTF-8"?>
            <stream:stream xmlns:stream="%s" to="%s" version="1.0"
            xmlns="%s">''' % (xmlns_stream, host, xmlns))

    def __getitem__(self, key):
        return self.attrib[key]

    def get_id(self):
        if self.attrib.has_key('id'):
            return self.attrib['id']

    def generator(self):
        # Create the handler.
        handler = Handler()
        # Create the parser context (this is a C library).
        context = libxml2.createPushParser(handler, '', 0, None)
        while True:
            # Read from the socket.
            chunk = self.read()
            # Parse the chunk that was read. This will trigger the handler,
            # which will put finished top-level nodes like presence and
            # message into its queue.
            context.parseChunk(chunk, len(chunk), 0)
            # Empty out the queue, so that we can act on it.
            for node in handler.empty_queue():
                yield node
                self.log('\n%s', node)

    def log(self, message, *args):
        if os.environ.has_key('TERM'):
            def do_log(message, *args):
                a = []
                for x in args:
                    if hasattr(x, 'pretty_print'):
                        x = '\x1b[36;1m%s\x1b[0m' % x.pretty_print()
                    a.append(x)
                logging.debug(message, *a)
        else:
            def do_log(message, *args):
                logging.debug(message, *args)
        if self.should_log:
            do_log(message, *args)

    def close(self):
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
