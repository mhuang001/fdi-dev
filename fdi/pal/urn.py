# -*- coding: utf-8 -*-
from .comparable import Comparable
from ..dataset.serializable import Serializable
from ..dataset.odict import ODict
from ..dataset.eq import DeepEqual
from ..dataset.classes import Classes
from ..utils.common import fullname
import sys
import os
import builtins
from collections import OrderedDict, ChainMap

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

# + 0.1 * sys.version_info[1] >= 3.3:
if sys.version_info[0] >= 3:
    PY3 = True
    strset = str
    from urllib.parse import urlparse
else:
    PY3 = False
    strset = (str, unicode)
    from urlparse import urlparse


def makeUrn(poolname, typename, index):
    """ assembles a URN with infos of the pool, the resource type, and the index

    index: int or string
    """
    return 'urn:' + poolname + ':' + typename + ':' + str(index)


class Urn(DeepEqual, Serializable, Comparable):
    """ The object representation of the product URN string.

    The memory consumed by sets of this object are much less than sets
    of URN strings.

    Only when the class types in URN string are not in classpath,
    the urn object will consume equals or a little more than URN string
    as the object has to hold the original urn string. However this should
    be considered as exceptional cases.

    Using this object representation also help to avoid parsing cost of URN string.
    URN string should be immutable.

    About_URN

The Universial Resource Name (**URN**) string has this format:

        urn:<poolname>:<resourcetype>:<serialnumber>

where

:<poolname>: Also called poolID. Its requirements is like that to a file name and a URL segment, having only printable characters excluding `` ``, ``%``, ``?``, ``*``, ``=``, ``/``.
:<resourcetype>: class name of the data item (usually :class:`Product`)
:<serialnumber>: internal index for a certain <resourcetype>.

The ``poolname`` in a URN is a label. Some examples:

-  urn:pool_mh:fdi.dataset.product.Product:2
-  urn:20.20:svom.products.SVOMMapContext:0

Storage Pools (subclasses of :class:`ProductPool`) are where data item reside. The **PoolURL** is used to give practical information of a pool, such as a poolname, its location, and its access scheme. It is designed to be a local set-up detail that is supposed to be hidden from pool users. Data processing software use ``URN``s to refer to products, without specifying pool location. The poolID in a URN could be a :class:`LocalPool` on the development laptop and a :class:`HTTPClientPool` on the production cloud.

    """

    def __init__(self, urn=None, poolname=None, cls=None, index=None, poolurl=None, **kwds):
        """
        Creates the URN object with the urn string or components.

        give urn and optional poolurl, or all poolname, cls, index arguments.
        if urn is given and pool, class, etc are also specified,
        the latter are ignored. else the URN object is constructed from them. 
        Urn(u) will make a Urn object out of u.

        All arguements are None by default.
        """
        super(Urn, self).__init__(**kwds)

        if urn is None:
            if cls is None or poolname is None or index is None:
                if cls is None and poolname is None and index is None:
                    self._scheme = None
                    self._place = None
                    self._poolname = None
                    self._class = None
                    self._index = None
                    self._poolpath = None
                    self._urn = None
                    return
                else:
                    raise ValueError(
                        'give urn and optional poolurl, or all poolname, cls, index arguments')
            urn = makeUrn(poolname=poolname,
                          typename=fullname(cls),
                          index=index)
        self.setUrn(urn, poolurl=poolurl)

    @property
    def urn(self):
        """ property
        """
        return self.getUrn()

    @urn.setter
    def urn(self, urn):
        """ property
        """
        self.setUrn(urn)

    def setUrn(self, urn, poolurl=None):
        """ parse urn to get poolname, resource, index.
        """
        if hasattr(self, '_urn') and self._urn and urn:
            raise TypeError('URN is immutable.')

        poolname, resourcetype, index = parseUrn(urn)

        Class_Look_Up = ChainMap(Classes.mapping, globals(), vars(builtins))
        cls = Class_Look_Up[resourcetype.split('.')[-1]]

        self._poolname = poolname
        self._class = cls
        self._index = index
        self._urn = urn

        if poolurl:
            poolpath, scheme, place, poolname = parse_poolurl(
                poolurl, poolname)
            self._poolpath = poolpath
            self._scheme = scheme
            self._place = place
        else:
            self._poolpath = None
            self._scheme = None
            self._place = None

    def getUrn(self):
        """ Returns the urn in this """
        return self._urn

    def getType(self):
        """ Returns class type of Urn
        """
        return self._class

    def getTypeName(self):
        """ Returns class type name of Urn.
        """
        return fullname(self._class)

    def getIndex(self):
        """ Returns the product index.
        """
        return self._index

    def getScheme(self):
        """ Returns the urn scheme.
        """
        return self._scheme

    def getUrnWithoutPoolId(self):
        return fullname(self._class) + ':' + str(self._index)

    @ property
    def place(self):
        return self.getPlace()

    def getPlace(self):
        """ Returns the netloc in this """
        return self._place

    def getPoolpath(self):
        """ returns the poolpath stored
        """
        return self._poolpath

    @ property
    def pool(self):
        """ returns the poolname.
        """
        return self.getPoolId()

    def getPoolId(self):
        """ Returns the pool URN in this """
        return self._poolname

    def getPool(self):
        """ Returns the pool name in this """
        return self.getPoolId()

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(urn=self._urn,
                           _STID=self._STID)

    def toString(self, level=0,
                 **kwds):
        return self.__class__.__name__ + \
            '(%s, scheme:%s, place:%s, pool:%s, type:%s, index:%d, poolpath: %s)' % (
                self._urn,
                self._scheme,
                self._place,
                self._poolname,
                self._class,  # .__name__,
                self._index,
                self._poolpath
            )


def parseUrn(urn):
    """
    Checks the URN string is valid in its form and splits it.

    A Product URN has several segment. For example if the urn is ``urn:mypool/v2:proj1.product:322``
    * poolname, also called poolURN or poolID, optionally path-like: ``mypool/v2``,
    * resource type (usually class) name ``proj1.product``,
    * index number  ``322``,

    returns poolname, resourceclass, index. if urn is None or empty returns (None,None,None) 

    """

    if urn is None or urn == '':
        return (None, None, None)
    if not issubclass(urn.__class__, strset):
        raise ValueError('a string is needed: ' + str(urn))
    # is a urn str?
    sp1 = urn.split(':')
    if sp1[0].lower() != 'urn':
        raise ValueError('Not a URN: ' + urn)
    # this is a product URN
    if len(sp1) != 4:
        # must have 4 segments
        raise ValueError('bad urn: ' + str(sp1))

    index = int(sp1[3])
    resourcetype = sp1[2]
    poolname = sp1[1]
    if len(poolname) == 0:
        poolname = None
    if len(resourcetype) == 0:
        resourcetype = None

    return poolname, resourcetype, index


def parse_poolurl(url, poolhint=None):
    """
    Disassambles a pool URL.

    A Pool URL is  It is generated to desribe . For example:

    input:
    * url: to be decomposed.
    * poolhint:  A urn or a poolname (the first distinctive substring) needs to be given if the poolname has more than one level.

    returns: poolpath, scheme, place, poolname.
    returns (None, None,None,None) if url is None or empty.


    About_poolURL

The ``PoolURL`` format is in the form of a URL that preceeds its poolname part:

                 <scheme>://<place><poolpath>/<poolname>

:<scheme>: Implementation protocol including ``file`` for :class:`LocalPool`, ``mem`` for :class:`MemPool`, ``http``, ``https`` for :class:`HttpclientPool`.
:<place>: IP:port such as``192.168.5.6:8080`` for ``http`` and ``https`` schemes, or an empty string for ``file`` and ``mem`` schemes.
:<poolname>: same as in URN.
:<poolpath>: The part between ``place`` and an optional ``poolhint``::

- For ``file`` or ``server`` schemes, e.g. poolpath is ``/c:/tmp`` in ``http://localhost:9000/c:/tmp/mypool/`` with ``poolhint`` keyword arguement of :func:`parse_poolurl` not given, or given as ``mypool`` (or ``myp`` or ``my`` ...).
- For ``http`` and ``https`` schemes, it is e.g. ``/0.6/tmp`` in ``https://10.0.0.114:5000/v0.6/tmp/mypool`` with ``poolhint`` keyword arguement not given, or given as ``mypool`` (or ``myp` or 'my' ...). The meaning of poolpath is subject to interpretation by the  server. In the preceeding example the poolpath has an API version.  :meth:`ProductPool.transformpath` is used to map it further. Note that trailing blank and ``/`` are ignored, and stripped in the output.

Examples:

-  file:///tmp/mydata for pool ```mydata```
-  file:///d:/data/test2--v2 for pool ``test2--v2``
-  mem:///dummy for pool ``dummy``
-  https://10.0.0.114:5000/v0.6/obs for a httpclientpool ``obs``
-  server:///tmp/data/0.4/test for a pool ``test`` used on a server.


    """

    if url is None or url == '':
        return (None, None, None, None)
    if not issubclass(url.__class__, strset):
        raise ValueError('a string is needed: ' + str(url))

    sp1 = url.split(':')
    if len(sp1) > 3:  # after scheme and a possible windows path
        raise ValueError(
            'a pool URN can have no more than 2 \':\'.')

    pr = urlparse(url)
    scheme = pr.scheme       # file
    place = pr.netloc
    # Note that trailing blank and ``/`` are ignored.
    path = pr.path.strip().rstrip('/')
    # convenient access path
    # get the poolname
    if poolhint:
        ps = poolhint.split(':')
        poolin = ps[1] if ps[0].lower() == 'urn' else ps[0]
        pind = path.index(poolin)
        poolname = path[pind:]
        poolpath = path[:pind].rstrip('/')
    else:
        # the last level is assumed to be the poolname
        sp = path.rsplit('/', 1)
        poolname = sp[1]
        poolpath = sp[0]

    poolpath = place + poolpath if scheme in ('file') else poolpath
    return poolpath, scheme, place, poolname


class UrnUtils():

    @ staticmethod
    def checkUrn(identifier):
        """ Throw a ValueError  if the identifier is not a legal URN."""
        if not issubclass(identifier.__class__, str):
            raise ValueError('Not a string: %s' % str(identifier))
        return parseUrn(identifier)

    @ staticmethod
    def containsUrn(poolobj,  urn):
        """ Informs whether a URN belongs to the given pool. """

        return poolobj.exists(urn)

    @ staticmethod
    def extractRecordIDs(urns):
        """ Extracts product IDs (serial numbers) from a set of urns. """
        ids = []
        for u in urns:
            pn, prod, sn = parseUrn(u)
            ids.append(sn)
        return ids

    @ staticmethod
    def getClass(urn):
        """ Get the class contained in a URN. """
        pn, prod, sn = parseUrn(urn)
        return Classes.mapping[prod.rsplit('.', 1)[1]]

    @ staticmethod
    def getClassName(urn):
        """ Get the class name contained in a URN. """
        pn, prod, sn = parseUrn(urn)
        return prod

    @ staticmethod
    def getLater(urn1, urn2):
        """ Returns the later of two urns. """
        pn1, prod1, sn1 = parseUrn(urn1)
        pn2, prod2, sn2 = parseUrn(urn2)
        return urn1 if sn1 > sn2 else urn2

    @ staticmethod
    def getPool(urn,  pools):
        """ Returns the pool corresponding to the pool id inside the given urn. 

        pools: ProductPool or subclass
        """
        if issubclass(urn.__class__, Urn):
            urn = urn.urn
        pn, prod, sn = parseUrn(urn)
        for p in pools:
            if pn == p.getId():
                return p
        raise KeyError(pn + ' not found in pools')

    @ staticmethod
    def getPoolId(urn):
        """ Returns the pool id part of the URN. """
        pn, prod, sn = parseUrn(urn)
        return pn

    @ staticmethod
    def getProductId(urn):
        """ Returns the product id part of the URN, that is, the last token. """
        pn, prod, sn = parseUrn(urn)
        return sn

    @ staticmethod
    def isUrn(identifier):
        """ Informs whether the given identifier corresponds to a URN. """

        try:
            UrnUtils.checkUrn(identifier)
        except ValueError:
            return False
        return True
