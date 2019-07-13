from collections import OrderedDict
#from dataset.serializable import Serializable


class ODict(OrderedDict):
    """ OrderedDict with a better __repre__.
    """

    def __repr__(self):

        def q(x): return "'" + x + \
            "'" if issubclass(x.__class__, str) else str(x)
        s = ''.join([q(k) + ':' + q(v) + ', ' for k, v in self.items()])
        return '{' + s[:-2] + '}'
