

def dict_to_xml(attrs):
    return ' '.join(['%s="%s"' % x for x in attrs.iteritems()])


class Node(list):

    def __init__(self, tag, *args, **kwargs):
        super(self.__class__, self).__init__(args)
        self.tag = tag
        self.attributes = dict(kwargs)

    def get_attributes(self):
        return self.attributes

    def __getattr__(self, name):
        if name == 'text':
            return ''.join([str(x) for x in self])
        return super(self.__class__, self).__getattribute__(name)

    def __str__(self):
        s = '<%s' % self.tag
        attrs = dict_to_xml(self.attributes)
        if attrs:
            s += ' ' + attrs
        if not len(self):
            return s + '/>'
        else:
            return s + '>' + self.text + ('</%s>' % self.tag)

    def pretty_print(self, level=0):
        """
        >>> x = Node('a', Node('b'), Node('c'))
        >>> x.pretty_print()
        '<a>\\n    <b/>\\n    <c/>\\n</a>'
        """
        if not len(self):
            text = self.text
            if not text:
                return '<%s/>' % self.tag
            return '<%s %s/>' % (self.tag, self.text)
        else:
            s = '<%s>\n' % self.tag
            prefix = '    ' * (level + 1)
            for x in self:
                if hasattr(x, 'pretty_print'):
                    s += '%s%s\n' % (prefix, x.pretty_print(level + 1))
                else:
                    s += '%s%s\n' % (prefix, x)
            s += '</%s>' % self.tag
            return s

    __repr__ = __str__
