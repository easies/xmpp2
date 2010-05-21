import logging
from lxml import etree


class TLSHandler(object):

    def __init__(self, client):
        self.client = client

    def start(self):
        # Send starttls request
        logging.info('Sending starttls request')
        self.write('<starttls xmlns="urn:ietf:params:xml:ns:xmpp-tls"/>')

    def handle(self, element):
        if element.tag.endswith('proceed'):
            logging.info('Proceeding with TLS')
            # Upgrade to TLS
            self.client.upgrade_to_tls()
        else:
            logging.warn('Not proceeding with TLS')
            logging.debug(etree.tostring(element))
        return self.PlugOut()

    def write(self, x):
        self.client.write(x)

    class PlugOut(object):

        def act(self, client, handler):
            client.remove_handler(handler)
            client.process() # for the features
