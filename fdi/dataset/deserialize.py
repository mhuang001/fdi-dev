# -*- coding: utf-8 -*-

from .serializable import serialize, ATTR, LEN_ATTR
from .odict import ODict
from .classes import Classes
from ..utils.common import lls, trbk, guess_value

import logging
import json
import codecs
import binascii
import array
import mmap
from collections import ChainMap
import builtins
import urllib
from collections import UserDict
from collections.abc import MutableMapping as MM, MutableSequence as MS, MutableSet as MSe
import sys
if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    strset = (str, bytes, bytearray)
else:
    PY3 = False
    strset = (str, unicode)

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

''' Note: this has to be in a different file where other interface
classes are defined to avoid circular dependency (such as ,
Serializable.
'''


def constructSerializable(obj, lookup=None, debug=False):
    """ mh: reconstruct object from the output of jason.loads().
    Recursively goes into nested class instances that are not
    encoded by default by JSONEncoder, instantiate and fill in
    variables.
    Objects to be deserialized must have their classes loaded.
    _STID cannot have module names in it (e.g.  dataset.Product)
    or locals()[classname] or globals()[classname] will not work.

    Parameters
    ----------

    Returns
    -------
    """
    global indent
    indent += 1
    spaces = '  ' * indent

    classname = obj.__class__.__name__
    if debug:
        print(spaces + '===OBJECT %s ===' % lls(obj, 150))
    if not hasattr(obj, '__iter__') or issubclass(obj.__class__, strset):
        if debug:
            print(spaces + 'Find non-iter <%s>' % classname)
        indent -= 1
        return obj

    # process list first
    if isinstance(obj, list):
        if debug:
            print(spaces + 'Find list <%s>' % classname)
        inst = []
        # loop i to preserve order
        for i in range(len(obj)):
            x = obj[i]
            xc = x.__class__
            if debug:
                print(spaces + 'looping through list %d <%s>' %
                      (i, xc.__name__))
            if issubclass(xc, (list, dict)):
                des = constructSerializable(x, lookup=lookup, debug=debug)
            else:
                des = x
            inst.append(des)
        if debug:
            print(spaces + 'Done with list <%s>' % (classname))
        indent -= 1
        return inst

    if not '_STID' in obj:
        """ This object is supported by JSON encoder """
        if debug:
            print(spaces + 'Find non-_STID. <%s>' % classname)
        inst = obj
    else:
        ostid = obj['_STID']
        # check escape case
        if ostid.startswith('0'):
            # escape
            inst = obj
            # classname = ostid[1:]
            # inst['_STID'] = classname
            if debug:
                print(spaces + 'Find _STID <%s>. Take as <%s>.' %
                      (ostid, classname))
            indent -= 1
            return inst
        else:
            classname = ostid
            if debug:
                print(spaces + 'Find _STID <%s>.' % (ostid))
        # process types wrapped in a dict
        if PY3:
            if classname == 'bytes':
                inst = codecs.decode(obj['code'], 'hex')
                if debug:
                    print(spaces + 'Instanciate hex')
                indent -= 1
                return inst
            elif classname.startswith('array.array'):
                tcode = classname.rsplit('_', 1)[1]
                inst = array.array(tcode, binascii.a2b_hex(obj['code']))
                if debug:
                    print(spaces + 'Instanciate array.array')
                indent -= 1
                return inst
        if classname in lookup:
            # Now we have a blank instance.
            inst = lookup[classname]()
            if debug:
                print(spaces + 'Instanciate custom obj <%s>' % classname)
        elif classname == 'ellipsis':
            if debug:
                print(spaces + 'Instanciate Ellipsis')
            indent -= 1
            return Ellipsis
        elif classname in lookup and 'obj' in obj:
            o = constructSerializable(obj['obj'], lookup=lookup, debug=debug)
            inst = lookup[classname](o)
            if debug:
                print(spaces + 'Instanciate defined %s' % obj['obj'])
            indent -= 1
            return inst
        elif classname == 'dtype':
            if debug:
                print(spaces + 'Instanciate type %s' % obj['obj'])
            inst = lookup[obj['obj']]
            indent -= 1
            return inst
        else:
            raise ValueError('Class %s is not known.' % classname)
    if debug:
        print(spaces + 'Go through properties of instance')
    for (k, v) in obj.items():
        """ loop through all key-value pairs. """
        if k == '_STID':
            continue
        # deserialize v
        # should be object_pairs_hook in the following if... line
        if issubclass(v.__class__, (dict, list)):
            if debug:
                print(spaces + '[%s]value(dict/list) <%s>: %s' %
                      (k, v.__class__.__qualname__,
                       lls(list(iter(v)), 70)))
            desv = constructSerializable(v, lookup=lookup, debug=debug)
        else:
            if debug:
                print(spaces + '[%s]value(simple) <%s>: %s' %
                      (k, v.__class__.__name__, lls(v, 70)))
            if 1:
                desv = v
            else:
                if isinstance(v, str) or isinstance(v, bytes):
                    try:
                        desv = int(v)
                    except ValueError:
                        desv = v

        # set k with desv
        icn = inst.__class__.__name__
        dcn = desv.__class__.__name__
        if issubclass(inst.__class__, (MM)):    # should be object_pairs_hook
            if k.startswith(ATTR):
                k2 = k[LEN_ATTR:]
                setattr(inst, k2, desv)
                if debug:
                    print(spaces + 'Set attrbute to dict/usrd <%s>.%s = %s <%s>' %
                          (icn, str(k2), lls(desv, 70), dcn))
            else:
                inst[k] = desv
                if debug:
                    print(spaces + 'Set member to dict/usrd <%s>[%s] = %s <%s>' %
                          (icn, str(k), lls(desv, 70), dcn))
        else:
            if k.startswith(ATTR):
                k2 = k[LEN_ATTR:]
                setattr(inst, k2, desv)
                if debug:
                    print(spaces + 'set attribute to non-dict <%s>.%s = %s <%s>' %
                          (icn, str(k2), lls(desv, 70), dcn))
            else:
                setattr(inst, k, desv)
                if debug:
                    print(spaces + 'set attribute to non-dict <%s>.%s = %s <%s>' %
                          (icn, str(k), lls(desv, 70), dcn))
    indent -= 1
    return inst


class IntDecoder(json.JSONDecoder):
    """ adapted from https://stackoverflow.com/questions/45068797/how-to-convert-string-int-json-into-real-int-with-json-loads
    modified to also convert keys in dictionaries.
    """

    def decode(self, s):
        """
        Parameters
        ----------

        Returns
        -------
        """
        # result = super(Decoder, self).decode(s) for Python 2.x
        result = super(IntDecoder, self).decode(s)
        return self._decode(result)

    def _decode(self, o):
        """
        Parameters
        ----------

        Returns
        -------
        """
        if isinstance(o, str) or isinstance(o, bytes):
            try:
                return int(o)
            except ValueError:
                return o
        elif isinstance(o, dict):
            return dict({self._decode(k): self._decode(v) for k, v in o.items()})
        elif isinstance(o, list):
            return [self._decode(v) for v in o]
        else:
            return o


class IntDecoderOD(IntDecoder):
    def _decode(self, o):
        """ Uses ODict
        Parameters
        ----------

        Returns
        -------
        """
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


def deserialize(js, lookup=None, debug=False, usedict=True):
    """ Loads classes with _STID from the results of serialize.

    if usedict is True dict insted of ODict will be used.
    Parameters
    ----------

    Returns
    -------
    """

    lookup = Class_Look_Up

    if not isinstance(js, strset) or len(js) == 0:
        return None
    # debug = False  # True if issubclass(obj.__class__, list) else False
    try:
        if usedict:
            obj = json.loads(js)  # , cls=IntDecoder)
        else:
            # , cls=IntDecoderOD)
            obj = json.loads(js, object_pairs_hook=ODict)
    except json.decoder.JSONDecodeError as e:
        msg = '\nBad string to decode as JSON=====>\n%s\n<======\n%s' % (
            lls(js, 500), str(e))
        logging.error(msg)
        obj = msg
    if debug:
        # print('load-str ' + str(o) + ' class ' + str(o.__class__))
        print('-------- json loads returns: --------\n' + str(obj))

    global indent
    indent = -1
    return constructSerializable(obj, lookup=lookup, debug=debug)


Class_Look_Up = ChainMap(Classes._classes, globals(), vars(builtins))

Serialize_Args_Sep = '__'
SAS_Avatar = '~'


def encode_str(a0):
    """ quote to remove general url offenders then use a mostly harmless str to substitute Serialize_Args_Sep.
    """
    return urllib.parse.quote(a0).replace(Serialize_Args_Sep, SAS_Avatar)


def serialize_args(*args, not_quoted=False, **kwds):
    """
    Serialize all positional and keywords arguements as they would appear in a function call.
    Arguements are assumed to have been placed in the same order of a valid function/method call. They are scanned from left to right from `args[i]` i = 0, 1,... to `kwds[j]` j = 0, 1, ...

* Scan args from i=0. if is of args[i] is of `bool`, `int`, `float` types, convert with `str`, if `str()`, convert with `encode_str()`, if `bytes` or `bytearray' types, with ```0x```+`hex()`, save to the convered-list, and move on to the next element.
* else if finding a segment not of any of the above types,
** put this and the rest of ```args``` as the ```value``` in ```{'apiargs':value}```,
** and append `kwds` key-val pairs after this pair,
** serialize the disctionary with `serialize()` and encode_str()
** append the result to the converted-list.
** break from the args scan loop.
* if args scan loop reaches its end, if `kwds` is not empty, serialize it with `serialize()` and encode_str(),
or scanning reaches the end of args.
* append the result to the converted-list.
* join the converted-list with `Serialize_Args_Sep`.
* return the result string

    """
    noseriargs = []
    i = 0
    # print('AR ', args, ' KW ', kwds)
    # from ..pal.query import AbstractQuery
    # if len(args) and issubclass(args[0].__class__, AbstractQuery):
    #    __import__('pdb').set_trace()

    for i, a0 in enumerate(args):
        # a string or number or boolean
        a0c = a0.__class__
        if a0 is None or issubclass(a0c, (bool, int, float)):
            noseriargs.append(str(a0))
        elif issubclass(a0c, (str)):
            noseriargs.append(a0 if not_quoted else encode_str(a0))
        elif issubclass(a0c, (bytes, bytearray)):
            noseriargs.append('0x'+a0.hex())
        else:
            seri = serialize(dict(apiargs=args[i:], **kwds))
            noseriargs.append(seri if not_quoted else encode_str(seri))
            break
    else:
        # loop ended w/ break
        if kwds:
            seri = serialize(kwds)
            noseriargs.append(seri if not_quoted else encode_str(seri))
    # print(noseriargs)
    despaced = Serialize_Args_Sep.join(noseriargs)

    return despaced


def decode_str(a0):
    """
    """
    return urllib.parse.unquote(a0.replace(SAS_Avatar, Serialize_Args_Sep))


def deserialize_args(all_args, not_quoted=False, first_string=True, serialize_out=False):
    """ parse the command path to get positional and keywords arguments.

    1. if `not_quoted` is `True`, split everythine to the left of first `{` with `Serialize_Args_Sep` append the part startin from the `{`. `mark='{'`
    2. else after splitting all_args  with `Serialize_Args_Sep`: `mark='%7B%22'` (`quote('{')`)

    Scan from left. if all_args[i] not start with `mark`

    Conversion rules:
    |all_args[i]| converted to |
    | else | convert (case insensitive) and move on to the next segment |
    | string not starting with ```'0x'``` | `quote` |

    * else `decode_str()` if ```not_quoted==False``` else only substitute SAS_Avatar with Serialize_Args_Sep. Then `deserialize()` this segment to become ```{'apiargs':list, 'foo':bar ...}```, append value of ```apiargs``` to the converted-list above, remove the ```apiargs```-```val``` pair.
    * return 200 as the reurn code followed by the converted-list and the deserialized ```dict```.

    :all_args: a list of path segments for the args list.
    :first_string: Do not try to change the type of the first arg (assumed to be the function/method name).
    """
    args, kwds = [], {}

    if not_quoted:
        mark = '{'
        ar = all_args.split(mark, 1)
        qulist = ar[0].split(Serialize_Args_Sep)
        if len(ar) > 1:
            if len(qulist):
                # the last ',' was for mark so should be removed,
                qulist = qulist[:-1]
            qulist.append(mark + ar[1])
    else:
        mark = '%7B%22'
        qulist = all_args.split(Serialize_Args_Sep)
    # print(qulist)

    for a0 in qulist:
        if not a0.startswith(mark):
            # guess and change type
            # a string, bytes or number or boolean
            # if int(a0l.lstrip('+-').split('0x',1)[-1].isnumeric():
            # this covers '-/+0x34'
            if first_string:
                # do not try to change type
                arg = decode_str(a0)
                first_string = False  # do not come back here
            else:
                arg = guess_value(a0, last=decode_str)
            args.append(arg)
            # print(args)
        else:
            # quoted serialized dict
            readable = a0.replace(
                SAS_Avatar, Serialize_Args_Sep) if not_quoted else decode_str(a0)
            dese = deserialize(readable)
            if 'apiargs' in dese:
                args += dese['apiargs']
                del dese['apiargs']
            kwds = dese
            break
    return 200, args, kwds
