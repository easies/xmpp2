import copy
import logging
from lxml import etree
from constants import NS_STREAM


class XMLStreamError(Exception):
    pass


class XMLStream(object):

    def __init__(self, sock, ns=NS_STREAM, tag='stream'):
        # file like IO
        self.sock = sock
        self.attrib = {}
        self.root = None
        if ns:
            self.tag = '{%s}%s' % (ns, tag)
        else:
            self.tag = tag

    def read(self, *args, **kwargs):
        return self.sock.read()

    def write(self, s):
        return self.sock.write(s)

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
                logging.debug(etree.tostring(element))
                self.root = element
                self.attrib.update(element.attrib)
                level = 1
                continue
            if event == 'start':
                level += 1
            else: # event == 'end':
                level -= 1
                if level == 1:
                    s = etree.tostring(element, pretty_print=True).strip()
                    logging.debug('\n' + s)
                    yield copy.deepcopy(element)
                    self.root.clear()

    def close(self):
        self.sock.close()
