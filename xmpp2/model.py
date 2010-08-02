

class XMLObject(list):

    def __init__(self, tag):
        self.tag = tag
        self.attributes = {}

    def __call__(self, **kwargs):
        self.attributes = dict(kwargs)
        return self

    def add(self, *elements):
        self.extend(elements)
        return self

    def __getattr__(self, name):
        if name == 'text':
            return ''.join([str(x) for x in self])
        return super(self.__class__, self).__getattribute__(name)

    def __attr_str(self):
        return ' '.join(['%s="%s"' % x for x in self.attributes.iteritems()])

    def __str__(self):
        s = '<%s' % self.tag
        attrs = self.__attr_str()
        if attrs:
            s += ' ' + attrs
        if not len(self):
            return s + '/>'
        else:
            return s + '>' + self.text + ('</%s>' % self.tag)

    __repr__ = __str__

    def pretty_print(self, level=0):
        attrs = self.__attr_str()
        prefix = '    ' * level
        if not len(self):
            if not attrs:
                return '%s<%s/>' % (prefix, self.tag)
            return '%s<%s %s/>' % (prefix, self.tag, attrs)
        else:
            s = '%s<%s>\n' % (prefix, self.tag)
            if attrs:
                s = '%s<%s %s>\n' % (prefix, self.tag, attrs)
            prefix = '    ' * (level + 1)
            for x in self:
                if hasattr(x, 'pretty_print'):
                    for y in x.pretty_print(level + 1).split('\n'):
                        s += '%s\n' % y
                else:
                    s += '%s%s\n' % (prefix, x)
            prefix = '    ' * level
            s += '%s</%s>' % (prefix, self.tag)
            return s


class XMLWriter(object):

    def __getattribute__(self, name):
        return XMLObject(name)


XML = XMLWriter()
