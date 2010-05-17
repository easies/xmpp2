import copy
import logging
from lxml import etree


class XMLStreamError(Exception):
    pass


class XMLStream(object):

    def __init__(self, sock):
        # file like IO
        self.sock = sock
        self.parser = etree.XMLParser()
        self.id = None
        self.root = None

    def read(self, *args, **kwargs):
        return self.sock.read()

    def write(self, s):
        return self.sock.write(s)

    def generator(self):
        if self.root is None:
            level = 0
        else:
            level = 1
        for event, element in etree.iterparse(self, events=('start', 'end')):
            if element.tag.endswith('stream'):
                self.id = element.attrib['id']
                self.root = element
                level = 1
                continue
            if event == 'start':
                level += 1
            else: # event == 'end':
                level -= 1
                if level == 1:
                    s = etree.tostring(element, pretty_print=True).strip()
                    logging.debug('\n' + s)
                    c = copy.deepcopy(element)
                    self.root.clear()
                    yield c

    def close(self):
        self.sock.close()
