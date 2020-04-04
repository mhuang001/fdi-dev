# -*- coding: utf-8 -*-
import json
import codecs

import sys
if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    strset = (str, bytes)
else:
    PY3 = False
    strset = (str, unicode)

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))

from .odict import ODict


class SerializableEncoder(json.JSONEncoder):
    """ can encode parameter and product etc such that they can be recovered
    with deserializeClassID.
    Python 3 treats string and unicode as unicode, encoded with utf-8, 
    byte blocks as bytes, encoded with utf-8.
    Python 2 treats string as str and unicode as unicode, encoded with utf-8, 
    byte blocks as str, encoded with utf-8
    """

    def default(self, obj):
        try:
            #print('%%%' + str(obj.__class__))
            # Let the base class default method raise the TypeError
            d = json.JSONEncoder.default(self, obj)
            #print('d=' + d)
        except TypeError as err:
            try:
                # logger.debug
                #print('&&&& %s %s' % (str(obj.__class__), str(obj)))
                if PY3 and issubclass(obj.__class__, bytes):
                    return dict(code=codecs.encode(obj, 'hex'), classID='bytes', version='')
                if not PY3 and issubclass(obj.__class__, str):
                    return dict(code=codec.encode(obj, 'hex'), classID='bytes', version='')
                # print(obj.serializable())
                return obj.serializable()
            except Exception as e:
                print('Ser ' + str(err))
                raise e


#    obj = json.loads(jstring)

def serializeClassID(o, indent=None):
    """ return JSON using special encoder SerializableEncoder """
    return json.dumps(o, cls=SerializableEncoder, indent=indent)


def serializeHipe(o):
    """ return JSON using special encoder SerializableHipeEncoder """
    return json.dumps(o, cls=SerializableHipeEncoder, indent=None)


class Serializable(object):
    """ mh: Can be serialized.
    Has a ClassID and version instance property to show its class
    and version information.
    """

    def __init__(self, **kwds):
        super(Serializable, self).__init__(**kwds)
        sc = self.__class__
        #print('@@@ ' + sc.__name__ + str(issubclass(sc, dict)))
        if issubclass(sc, dict):
            self['classID'] = sc.__name__
            self['version'] = ''
        else:
            self.classID = sc.__name__
            self.version = ''

    def serialized(self, indent=None):
        return serializeClassID(self, indent=indent)

    def serializable(self):
        """ returns an odict that has all state info of this object.
        Subclasses should override this function.
        """
        return ODict()
