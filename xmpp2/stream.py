import logging
from lxml import etree


class XMLStreamError(Exception):
    pass


class XMLStream(object):

    def __init__(self, sock):
        # file like IO
        self.sock = sock
        self.parser = etree.XMLParser()

    def read(self, *args, **kwargs):
        return self.sock.read()

    def write(self, s):
        return self.sock.write(s)

    def generator(self):
        for event, element in etree.iterparse(self, events=('start', 'end')):
            logging.debug(str((event, element.tag, element.attrib)))
            if event == 'end':
                yield element

    def close(self):
        self.sock.close()
