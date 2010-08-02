

class XMLObject(list):

    def __init__(self, tag, *args, **kwargs):
        self.tag = tag
        self.attributes = dict(kwargs)
        self.extend(args)

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

    def pretty_print(self, level=0, tab='  '):
        attrs = self.__attr_str()
        prefix = tab * level
        # Check for no children.
        if not len(self):
            if not attrs:
                return '%s<%s/>' % (prefix, self.tag)
            return '%s<%s %s/>' % (prefix, self.tag, attrs)
        # Has children.
        end_tag = '</%s>' % self.tag
        if attrs:
            start_tag = '<%s %s>' % (self.tag, attrs)
        else:
            start_tag = '<%s>' % self.tag
        lines = []
        for x in self:
            if hasattr(x, 'pretty_print'):
                lines.extend(x.pretty_print(level + 1).split('\n'))
            else:
                lines.append(tab * (level + 1) + str(x))
        # Single child.
        if len(self) == 1:
            return prefix + start_tag + lines[0].strip() + end_tag
        # 2+ children.
        return '%s%s\n%s\n%s%s' % (prefix, start_tag, '\n'.join(lines),
                                   prefix, end_tag)


class XMLWriter(object):

    def __getattribute__(self, name):
        return XMLObject(name)


XML = XMLWriter()
