

class Handler(object):

    def handle(self, xml_obj):
        """Given an xml_obj, return None for a successful execution. Return an
        ExitType for a custom action."""


class ExitType(object):

    def act(self, client, handler):
        """Act on the handler."""


class PlugOut(ExitType):

    def act(self, client, handler):
        client.remove_handler(handler)
