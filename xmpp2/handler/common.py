

class PlugOut(object):

    def act(self, client, handler):
        client.remove_handler(handler)
