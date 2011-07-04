class Raw(object):
    def __init__(self, data):
        super(Raw, self).__init__()
        self.data = data
    def __repr__(self):
        return "RAW(%r)" % (self.data,)
    def __eq__(self, other):
        return isinstance(other, Raw) and other.data == self.data
    def __ne__(self, other):
        return not (self == other)

