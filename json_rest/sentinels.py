class _Sentinel(object):
    def __init__(self, name):
        super(_Sentinel, self).__init__()
        self._name = name
    def __repr__(self):
        return "<{}>".format(self._name)

NO_DATA = _Sentinel('NO_DATA')
