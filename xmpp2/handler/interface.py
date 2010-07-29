

class Handler(object):

    def handle(self, xml_obj):
        """Given an xml_obj, return None for a successful execution. Return an
        ExitType for a custom action."""

    def get_type(self):
        """(optional) The type of this handler is one of:
        ('message', 'iq', 'presence')"""

    def get_ns(self):
        """(optional) The xml namespace for this handler."""

    def get_scope(self):
        """(optional)"""


class ExitType(object):

    def act(self, client, handler):
        """Act on the handler."""
