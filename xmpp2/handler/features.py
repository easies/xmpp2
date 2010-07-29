from common import PlugOut


class FeaturesHandler(object):

    def __init__(self, client):
        self.client = client

    def start(self):
        self.client.process()

    def handle(self, node):
        if self.client.features is None:
            self.client.features = Features(node)
        else:
            self.client.features.append(Features(node))
        return PlugOut()


class Features(object):

    def __init__(self, node):
        self.attrib = node.attributes
        self.elements = node[:]
        self.others = []

    def append(self, feature):
        self.others.append(feature)

    def has_feature(self, feature):
        for element in self.elements:
            if element.tag.endswith(feature):
                return True
        for features in self.others:
            if features.has_feature(self, feature):
                return True
        return False

    def get_feature(self, feature):
        for element in self.elements:
            if element.tag.endswith(feature):
                return element
        for features in self.others:
            feat = features.get_feature(self, feature)
            if feat is not None:
                return feat
