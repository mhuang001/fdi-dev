# -*- coding: utf-8 -*-
import json
from dataset.odict import ODict

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


''' Note: this has to be in a different file where other interface
classes are defined to avoid circular dependency (such as ,
Serializable.
'''


def constructSerializableClassID(obj, glbs=None, debug=False):
    """ mh: reconstruct object from the output of jason.loads().
    Recursively goes into nested class instances that are not
    encoded by default by JSONEncoder, instantiate and fill in
    variables.
    Objects to be deserialized must have their classes loaded.
    ClassID cannot have module names in it (e.g.  dataset.Product)
    or globals()[classname] will not work. See alternative in
    https://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname

    """

    if not hasattr(obj, '__iter__') or issubclass(obj.__class__, str):
        return obj

    classname = obj.__class__.__name__
    # process list first
    if issubclass(obj.__class__, list):
        if debug:
            print('lis ' + classname)
        inst = []
        # loop i to preserve order
        for i in range(len(obj)):
            x = obj[i]
            if issubclass(x.__class__, (list, dict)):
                des = constructSerializableClassID(x, glbs=glbs, debug=debug)
            else:
                des = x
            inst.append(des)
        return inst

    if 'classID' not in obj:
        """ This object is supported by JSONEncoder """
        if debug:
            print('No ClassID. ' + classname)
        inst = obj
    else:
        classname = obj['classID']
        if debug:
            print('ClassID ' + classname)
        # process types wrapped in a dict
        if classname == 'bytes':
            inst = bytes.fromhex(obj['hex'])
            return inst
        # inst = eval(classname + '()')
        inst = glbs[classname]()
    for (k, v) in obj.items():
        """ loop through all key-value pairs. """
        if k != 'classID' and k != 'version':
            # deserialize v
            if issubclass(v.__class__, (dict, list)):
                if debug:
                    print('+++ %s %s' % (str(v.__class__), str(v)))
                desv = constructSerializableClassID(v, glbs=glbs, debug=debug)
            else:
                if debug:
                    print('--- %s %s' % (str(v.__class__), str(v)))
                if 1:
                    desv = v
                else:
                    if isinstance(v, str) or isinstance(v, bytes):
                        try:
                            desv = int(v)
                        except ValueError:
                            desv = v

            # set k with desv
            if issubclass(inst.__class__, dict):
                inst[k] = desv
                if debug:
                    print('in %s key  %s found %s %s' %
                          (str(inst.__class__), str(k), str(desv), str(desv.__class__)))
            else:
                setattr(inst, k, desv)
                if debug:
                    print('in %s attr %s found %s %s' %
                          (str(inst.__class__), str(k), str(desv), str(desv.__class__)))
    return inst


class IntDecoder(json.JSONDecoder):
    """ adapted from https://stackoverflow.com/questions/45068797/how-to-convert-string-int-json-into-real-int-with-json-loads
    modified to also convert keys in dictionaries.
    """

    def decode(self, s):
        result = super().decode(s)  # result = super(Decoder, self).decode(s) for Python 2.x
        return self._decode(result)

    def _decode(self, o):
        if isinstance(o, str) or isinstance(o, bytes):
            try:
                return int(o)
            except ValueError:
                return o
        elif isinstance(o, dict):
            return ODict({self._decode(k): self._decode(v) for k, v in o.items()})
        elif isinstance(o, list):
            return [self._decode(v) for v in o]
        else:
            return o


def deserializeClassID(js, dglobals=None, debug=False, usedict=False):
    """ Loads classes with ClassID from the results of serializeClassID
    """
    if not isinstance(js, (str, bytes)) or len(js) == 0:
        return None
    # debug = False  # True if issubclass(obj.__class__, list) else False
    try:
        if usedict:
            obj = json.loads(js, cls=IntDecoder)
        else:
            obj = json.loads(js, object_pairs_hook=ODict, cls=IntDecoder)
    except json.decoder.JSONDecodeError as e:
        logging.error(' Bad string to decode:\n==============\n' +
                      js[:500] + '...\n==============')
        raise e
    if debug:
        # print('load-str ' + str(o) + ' class ' + str(o.__class__))
        print('-------- json loads returns: --------\n' + str(obj))
    return constructSerializableClassID(obj, glbs=dglobals, debug=debug)
