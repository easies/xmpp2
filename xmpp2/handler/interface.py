

class Handler(object):

    def handle(self, xml_obj):
        """
        Given an xml_obj, return None for a successful execution. Return an
        object which has the signature of an :class:`~ExitType` for a custom
        action.

        :param xml_obj: An :class:`~xmpp2.model.XMLObject` to be handled.
        :return: None for a successful execution.
        :return: A object that has the signature provided by
                 :class:`~ExitType`\ .
        """

    def get_type(self):
        """(optional) The type of this handler is one of:
        ('message', 'iq', 'presence')"""

    def get_ns(self):
        """(optional) The xml namespace for this handler."""
#
#    def get_scope(self):
#        """(optional) Not used yet."""


class ExitType(object):

    def act(self, client, handler):
        """
        Act on the handler.

        :param client: An :class:`~xmpp2.client.Client`\ .
        :param handler: The handler instance.
        """
