import logging
from common import PlugOut


class TLSHandler(object):

    def __init__(self, client):
        self.client = client
        self.handled = False

    def start(self):
        # Send starttls request
        logging.info('Sending starttls request')
        self.write('<starttls xmlns="urn:ietf:params:xml:ns:xmpp-tls"/>')
        self.client.process()

    def handle(self, element):
        if self.handled:
            return
        self.handled = True
        if element.tag.endswith('proceed'):
            logging.info('Proceeding with TLS')
            # Upgrade to TLS
            self.client.upgrade_to_tls()
        else:
            logging.warn('Not proceeding with TLS. Got: %s', element)
        return PlugOut()

    def write(self, x):
        self.client.write(x)
