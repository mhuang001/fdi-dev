# -*- coding: utf-8 -*-

# from ..utils.common import fullname

import array
import binascii
import gzip
# from .odict import ODict
import logging
import json
import copy
import codecs
import urllib
from collections.abc import Collection, Mapping
from functools import lru_cache
import sys
import datetime
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
        """
        Parameters
        ----------

        Returns
        -------
        """
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
        """ this all only work on the first level of nested objects
        Parameters
        ----------

        Returns
        -------
        """
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
        """
        Parameters
        ----------

        Returns
        -------
        """
        return super().iterencode(self._preprocess(obj), **kwds)


GZIP = False
""" Use ```gzip``` (and ```Bae64``` if needed) to compress. """

SCHEMA = False
""" Output JSONschema instead of JSON erialization. """


class SerializableEncoder(json.JSONEncoder):
    """ can encode parameter and product etc such that they can be recovered
    with deserialize().
    Python 3 treats string and unicode as unicode, encoded with utf-8,
    byte blocks as bytes, encoded with utf-8.
    Python 2 treats string as str and unicode as unicode, encoded with utf-8,
    byte blocks as str, encoded with utf-8
    """

    def default(self, obj):
        """
        Parameters
        ----------

        Returns
        -------
        """
        try:
            # print('%%%' + str(obj.__class__))
            # Let the base class default method raise the TypeError
            d = json.JSONEncoder.default(self, obj)
            # print('d=' + d)
        except TypeError as err:
            try:
                # logger.debug
                # print('&&&& %s %s' % (str(obj.__class__), str(obj)))
                oc = obj.__class__
                if PY3:
                    if issubclass(oc, (datetime.datetime)):
                        if SCHEMA:
                            return '{"$ref": "%s"}' % oc.__name__
                        from ..dataset.finetime import FineTime
                        return dict(
                            code=FineTime.datetimeToFineTime(obj),
                            _STID=oc.__name__+',tai')
                    if issubclass(oc, (bytes, bytearray)):
                        if SCHEMA:
                            return '{"$ref": "bytes"}'
                        if GZIP:
                            r = dict(code=binascii.b2a_base64(
                                gzip.compress(obj, 5)).decode('ascii'),
                                _STID=oc.__name__ + ',gz,b64')
                        else:
                            r = dict(code=obj.hex(), _STID=oc.__name__)
                        return r
                    elif issubclass(oc, array.array):
                        if SCHEMA:
                            return '{"$ref": "%s"}' % oc.__name__
                        if GZIP:
                            r = dict(code=binascii.b2a_base64(
                                gzip.compress(obj, 5)).decode('ascii'),
                                _STID='a.array_%s,gz,b64' % obj.typecode)
                        else:
                            r = dict(code=str(codecs.encode(obj, 'hex'),
                                              encoding='ascii'),
                                     _STID='a.array_'+obj.typecode)
                        return r
                if not PY3 and issubclass(oc, str):
                    # return dict(code=codec.encode(obj, 'hex'), _STID='bytes')
                    assert False, lls(obj, 50)
                    if GZIP:
                        if SCHEMA:
                            return '{"$ref": "%s"}' % 'bytes'
                        return dict(code=gzip.compress(obj, 5),
                                    _STID='bytes,gz')
                    else:
                        return obj
                if obj is Ellipsis:
                    if SCHEMA:
                        return '{"$ref": "%s"}' % oc.__name__
                    return {'obj': '...', '_STID': 'ellipsis'}
                if issubclass(oc, type):
                    if SCHEMA:
                        return '{"$ref": "%s"}' % oc.__name__
                    return {'obj': obj.__name__, '_STID': 'dtype'}
                if hasattr(obj, 'serializable'):
                    if SCHEMA:
                        return '{%s}' % obj.schema()
                    try:
                        typ = obj.type
                    except (LookupError, AttributeError):
                        typ = None
                    if typ in ['image/svg']:
                        ser = obj.serializable()[ATTR+'data']
                        ser = urllib.parse.quote(ser)
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
    """ return JSON using special encoder SerializableEncoder

    Parameterts
    -----------

    Returns
    -------
    """
    if not cls:
        cls = SerializableEncoder
    return json.dumps(o, cls=cls, allow_nan=True, **kwds)


@lru_cache(maxsize=256)
def get_schema_with_classname(cls_name, store=None):
    if store is None:
        store = makeSchemeStore()
    for sch in store:
        if cls_name == 'array':
            n = 'a_array'
        else:
            n = cls_name
        if sch.endswith('/%s' % n):
            return sch, store[sch]
    # did not find.
    return None, None


ATTR = '_ATTR_'
LEN_ATTR = len(ATTR)


class Serializable():
    """ mh: Can be serialized.
    Has a _STID  instance property to show its class information. """

    def __init__(self, *args, **kwds):
        """

        Parameters
        ----------

        Returns
        -------
        """
        super().__init__(*args, **kwds)
        sc = self.__class__
        # print('@@@ ' + sc.__name__, str(issubclass(sc, dict)))

        self._STID = sc.__name__

    def serialized(self, indent=None):
        """
        Parameters
        ----------


        Returns
        -------
        """
        return serialize(self, indent=indent)

    def __repr__(self):

        co = ', '.join(str(k)+'=' + ('"'+v+'"'
                                     if issubclass(v.__class__, str)
                                     else str(v))
                       for k, v in self.__getstate__().items()
                       )
        return self.__class__.__name__ + '(' + co + ')'

    def __getstate__(self):
        """ returns an ordered ddict that has all state info of this object.
        Subclasses should override this function.
        Parameters
        ----------

        Returns
        -------
        """
        raise NotImplementedError()

    def __setstate__(self, state):
        """
        Parameters
        ----------

        Returns
        -------
        """
        for name in state.keys():
            if name.startswith(ATTR):
                k2 = name[LEN_ATTR:]
                self.__setattr__(k2, state[name])
            elif name == '_STID':
                pass
            elif hasattr(self, '__setitem__'):
                self[name] = state[name]
            else:
                self.__setattr__(name, state[name])

    def __reduce_ex__(self, protocol):
        """
        Parameters
        ----------

        Returns
        -------
        """
        def func(): return self.__class__()
        args = tuple()
        state = self.__getstate__()
        return func, args, state

    def __reduce__(self):
        """
        Parameters
        ----------

        Returns
        -------
        """
        return self.__reduce_ex__(4)

    def serializable(self):
        """ Can be encoded with serializableEncoder.

        Return
        ------
        dict
             The state variables plus the Serialization Type ID with ```_STID``` as uts key.
        """
        s = copy.copy(self.__getstate__())
        # make sure _STID is the last, for pools to ID data.
        if '_STID' in s:
            del s['_STID']
        s.update({'_STID': self._STID})
        return s

    def schema(self):
        """ Get schema definition using the FDI standard schema set in `FDI_SCHEMA_STORE`. Subclassing to add more schemas.
        """
        sid, sch = get_schema_with_classname(self.__class__.__name__)
        return sch

    def yaml(self, *args, **kwds):
        """ Get a YAML representation. """
        from ..utils.ydump import ydump, yinit
        yinit()
        return ydump(self, *args, **kwds)

    def tree(self, *args, **kwds):
        """ Get a directory-tree-like representation. """
        from ..utils.tree import tree

        return '\n'.join(tree(self, *args, **kwds))

    def fits(self, *args, **kwds):
        """ Get a FITS representation. """
        from ..utils.tofits import toFits, FITS_INSTALLED

        if not FITS_INSTALLED:
            raise NotImplemented(
                'Astropy not installed. Include SCI in extra-dependency when installing FDI.')

        return toFits(self, *args, **kwds)

    def html(self, extra=False, param_widths=-1, **kwds):
        """ Get a HTML representation. """

        return self.toString(level=0,
                             tablefmt='unsafehtml',
                             tablefmt1='unsafehtml',
                             tablefmt2='unsafehtml',
                             extra=extra,
                             param_widths=param_widths, **kwds)

    def jsonPath(self, expr, val='simple', sep='/', indent=None, *args, **kwds):
        from ..utils.jsonpath import jsonPath

        return jsonPath(self.data, expr=expr, val=val, indent=indent, *args, **kwds)

    def fetch(self, paths, exe=['is'], not_quoted=True):
        from ..utils.fetch import fetch

        return fetch(paths, self, re='', exe=exe, not_quoted=not_quoted)
