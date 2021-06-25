# -*- coding: utf-8 -*-

#from ..utils.common import fullname

import array
import binascii
# from .odict import ODict
import logging
import json
import copy
import codecs
from collections import ChainMap
from collections.abc import Collection, Mapping
import sys
if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    strset = (str, bytes)
else:
    PY3 = False
    strset = (str, unicode)

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class SerializableEncoderAll(json.JSONEncoder):
    """ can encode parameter and product etc such that they can be recovered
    with deserialize().
    Python 3 treats string and unicode as unicode, encoded with utf-8,
    byte blocks as bytes, encoded with utf-8.
    Python 2 treats string as str and unicode as unicode, encoded with utf-8,
    byte blocks as str, encoded with utf-8
    """

    def default(self, obj):
        # logger.debug
        # print('&&&& %s %s' % (str(obj.__class__), str(obj)))
        if PY3:
            if issubclass(obj.__class__, bytes):
                return dict(code=codecs.encode(obj, 'hex'), _STID='bytes')
            elif issubclass(obj.__class__, array.array):
                return dict(code=str(binascii.b2a_hex(obj), encoding='ascii'), _STID='array.array_'+obj.typecode)
        if not PY3 and issubclass(obj.__class__, str):
            return dict(code=codec.encode(obj, 'hex'), _STID='bytes')
        if obj is Ellipsis:
            return {'obj': '...', '_STID': 'ellipsis'}
        # print(obj.__getstate__())

        if issubclass(obj.__class__, Serializable):
            return obj.__getstate__()
        print('%%%' + str(obj.__class__))
        return

        # Let the base class default method raise the TypeError
        d = json.JSONEncoder.default(self, obj)
        print('encoded d=' + d)
        return d

    # https://stackoverflow.com/a/63455796/13472124
    base = (str, int, float, bool, type(None))

    def _preprocess(self, obj):
        """ this all only work on the first level of nested objects """
        oc = obj.__class__
        ocn = type(obj).__name__

        # print('%%%*****prepro ' + ocn)
        # pdb.set_trace()
        # if issubclass(oc, self.base):
        #     # mainly to process string which is a collections (bellow)
        #     return obj
        # elif 0 and issubclass(oc, (Serializable, bytes)):
        #     if issubclass(oc, dict):
        #         # if is both __Getstate__ and Mapping, insert _STID, to a copy
        #         o = copy.copy(obj)
        #         o['_STID'] = obj._STID
        #         return o
        #     return obj
        # elif isinstance(obj, list):
        #     return obj
        # elif issubclass(oc, (Mapping)):
        #     # if all((issubclass(k.__class__, self.base) for k in obj)):
        #     if True:
        #         # JSONEncoder can handle the keys
        #         if isinstance(obj, dict):
        #             return obj
        #         else:
        #             return {'obj': dict(obj), '_STID': ocn}
        #     else:
        #         # This handles the top-level dict keys
        #         return {'obj': [(k, v) for k, v in obj.items()], '_STID': ocn}
        if issubclass(oc, (Collection)):
            return {'obj': list(obj), '_STID': ocn}
        # elif obj is Ellipsis:
        #     return {'obj': '...', '_STID': ocn}

        else:
            return obj

    def iterencode(self, obj, **kwds):
        return super().iterencode(self._preprocess(obj), **kwds)


class SerializableEncoder(json.JSONEncoder):
    """ can encode parameter and product etc such that they can be recovered
    with deserialize().
    Python 3 treats string and unicode as unicode, encoded with utf-8,
    byte blocks as bytes, encoded with utf-8.
    Python 2 treats string as str and unicode as unicode, encoded with utf-8,
    byte blocks as str, encoded with utf-8
    """

    def default(self, obj):
        try:
            # print('%%%' + str(obj.__class__))
            # Let the base class default method raise the TypeError
            d = json.JSONEncoder.default(self, obj)
            # print('d=' + d)
        except TypeError as err:
            try:
                # logger.debug
                # print('&&&& %s %s' % (str(obj.__class__), str(obj)))
                if PY3:
                    if issubclass(obj.__class__, bytes):
                        return dict(code=str(codecs.encode(obj, 'hex'), encoding='ascii'), _STID='bytes')
                    elif issubclass(obj.__class__, array.array):
                        return dict(code=str(binascii.b2a_hex(obj), encoding='ascii'), _STID='array.array_'+obj.typecode)
                if not PY3 and issubclass(obj.__class__, str):
                    return dict(code=codec.encode(obj, 'hex'), _STID='bytes')
                if obj is Ellipsis:
                    return {'obj': '...', '_STID': 'ellipsis'}
                if issubclass(obj.__class__, type):
                    return {'obj': obj.__name__, '_STID': 'dtype'}
                if hasattr(obj, 'serializable'):
                    # print(obj.serializable())
                    return obj.serializable()
                try:
                    return dict(obj)
                except Exception:
                    return list(obj)
            except Exception as e:
                print('Serialization failed.' + str(e))
                raise


#    obj = json.loads(jstring)

def serialize(o, cls=None, **kwds):
    """ return JSON using special encoder SerializableEncoder """
    if not cls:
        cls = SerializableEncoder
    return json.dumps(o, cls=cls, **kwds)


class Serializable(object):
    """ mh: Can be serialized.
    Has a _STID  instance property to show its class information.
    """

    def __init__(self, **kwds):

        super(Serializable, self).__init__(**kwds)
        sc = self.__class__
        # print('@@@ ' + sc.__name__, str(issubclass(sc, dict)))
        if 0 and issubclass(sc, dict):
            self['_STID'] = sc.__name__
        else:
            self._STID = sc.__name__

    def serialized(self, indent=None):
        return serialize(self, indent=indent)

    def __repr__(self):

        co = ', '.join(str(k)+'=' + ('"'+v+'"'
                                     if issubclass(v.__class__, str)
                                     else str(v))
                       for k, v in self.__getstate__().items()
                       )
        return self.__class__.__name__ + '(' + co + ')'

    def __getstate__(self):
        """ returns an odict that has all state info of this object.
        Subclasses should override this function.
        """
        raise NotImplementedError()

    def __setstate__(self, state):
        for name in self.__getstate__().keys():
            self.__setattr__(name, state[name])

    def __reduce_ex__(self, protocol):
        def func(): return self.__class__()
        args = tuple()
        state = self.__getstate__()
        return func, args, state

    def __reduce__(self):
        return self.__reduce_ex__(4)

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        s = copy.copy(self.__getstate__())
        s.update({'_STID': self._STID})
        return s
