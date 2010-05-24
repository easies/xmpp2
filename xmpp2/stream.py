import copy
import logging
from lxml import etree
from constants import NS_STREAM, NS_CLIENT


class XMLStreamError(Exception):
    pass


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
        if type(s) == str:
            x = unicode(s)
            self.log(x)
        else:
            x = etree.tostring(s, encoding=unicode)
            self.log('\n%s', x)
        return self.__sock.write(x)

    def initiate(self, host, xmlns_stream=NS_STREAM, xmlns=NS_CLIENT):
        self.write('''<?xml version="1.0" encoding="UTF-8">
            <stream:stream xmlns:stream="%s" to="%s" version="1.0"
            xmlns="%s">''' % (xmlns_stream, host, xmlns))

    def __getitem__(self, key):
        return self.attrib[key]

    def get_id(self):
        if self.attrib.has_key('id'):
            return self.attrib['id']
        return None

    def generator(self):
        if self.root is None:
            level = 0
        else:
            level = 1
        for event, element in etree.iterparse(self, events=('start', 'end')):
            if element.tag == self.tag:
                self.log('\n%s', element)
                self.root = element
                self.attrib.update(element.attrib)
                level = 1
                continue
            if event == 'start':
                level += 1
            else: # event == 'end':
                level -= 1
                if level == 1:
                    self.log('\n%s', element)
                    yield copy.deepcopy(element)
                    self.root.clear()

    def log(self, message, *args):
        if self.should_log:
            x = []
            for s in args:
                if isinstance(s, etree._Element):
                    s = etree.tostring(s, pretty_print=True).strip()
                x.append(s)
            import os
            if os.environ.has_key('TERM'):
                logging.debug('\x1b[36;1m%s\x1b[0m' % message, *x)
            else:
                logging.debug(message, *x)

    def close(self):
        self.__sock.close()
