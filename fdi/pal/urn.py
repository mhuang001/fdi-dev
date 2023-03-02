# -*- coding: utf-8 -*-
from .comparable import Comparable
from ..dataset.serializable import Serializable
from ..dataset.odict import ODict
from ..dataset.eq import DeepEqual
from ..utils.common import fullname

import sys
import os
import functools
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


def is_urn(u):
    sp = u.split(':')
    return len(sp) == 4 and sp[0].lower() and sp[3].isdigit()


def makeUrn(poolname, typename, index):
    """ assembles a URN or a list of URNs with infos of the pool, the resource type, and the index.

    :poolname: str or list of them.
    :typename: str, name of data type. or list of them.
    index: int or string or list of them.
    If any two or more are lists, all have to be list of the same length.
    """
    lp = lt = li = 0

    lp = len(poolname) if isinstance(poolname, list) else 0
    lt = len(typename) if isinstance(typename, list) else 0
    li = len(index) if isinstance(index, list) else 0

    sz = max(lp, lt, li)
    if sz:
        if not ((lp == 0 or lp == sz) and (lt == 0 or lt == sz) and (li == 0 or li == sz)):
            raise TypeError(
                f'At least two args have different sizes {lp}, {ly}, {li}.')
        # at least one is a list. make them all lists of sz size.
        po = poolname if lp else [poolname]*sz
        ty = typename if lt else [typename]*sz
        sn = index if li else [index]*sz

        urns = [f'urn:{po[i]}:{ty[i]}:{sn[i]}' for i in range(sz)]
        return urns
    else:
        urns = f'urn:{poolname}:{typename}:{index}'
        return urns


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

The Universial Resource Name (**URN**, https://datatracker.ietf.org/doc/html/rfc2141 ) string has this format:

        urn:<poolname>:<resourcetype>:<serialnumber>

with modified rules desribed below.

:<poolname>: Also called poolID. It consists of 1-32 characters, is case-sensitive, which deviates from rfc2141. Character allowed are ``alpha``, ``digit``, ``safe``, defined in rfc1630 (https://datatracker.ietf.org/doc/html/rfc1630). These are excluded: `` ``, ``%``, ``?``, ``!``, ``*``,``'``, ``"``,  ``(``, ``)``, ``=``, ``/``, and what listed in ``mod:poolmanager:Invalid_Pool_Names``, e.g. ``pools``, ``urn``, ``URN``, ``api``.
:<resourcetype>: type name of the data item (usually class name of data products inheriting :class:`BaseProduct`)
:<serialnumber>: internal index for a certain <resourcetype>.

The ``poolname`` in a URN is a label. Some examples:

-  urn:pool_mh:fdi.dataset.product.Product:2
-  urn:20.20:svom.products.SVOMMapContext:0

URNs are used to to identify data be cause URNs are location agnostic. Storage Pools (subclasses of :class:`ProductPool`) are where data item reside. The **PoolURL** is used to give practical information of a pool, such as a poolname, its location, and its access scheme. PoolURL is designed to be a local set-up detail that is supposed to be hidden from pool users. Data processing software use ``URN``s to refer to products, without specifying pool location. The poolID in a URN could be a :class:`LocalPool` on the development laptop and a :class:`HTTPClientPool` on the production cloud.

    """

    def __init__(self, urn=None, poolname=None, cls=None, index=None, poolurl=None, **kwds):
        """
        Creates the URN object with the urn string or components.

        give urn and optional poolurl, or all poolname, cls, index arguments.
        if urn is given and pool, class, etc are also specified,
        the latter are ignored. else the URN object is constructed from them.
        Urn(u) will make a Urn object out of u.

        All arguements are None by default.

        Parameters
        urn: string. A URM string.
        poolname: string, provides pool name part of URN if URN is missing from input.
        cls: type. the full class name is used for datatype.
        index: int.
        poolurl: string. IF specified will provide info of the pool involved.

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
            if not issubclass(cls.__class__, type):
                raise TypeError('cls is a ' + cls.__class__ +
                                ', not a class type.')
            urn = makeUrn(poolname=poolname,
                          typename=fullname(cls),
                          index=index)
        self.setUrn(urn, poolurl=poolurl)

    @ property
    def urn(self):
        """ property
        """
        return self.getUrn()

    @ urn.setter
    def urn(self, urn):
        """ property
        """
        self.setUrn(urn)

    def setUrn(self, urn, poolurl=None):
        """ Set urn, poolname, resource, index attributes.
        """
        if hasattr(self, '_urn') and self._urn and urn:
            raise TypeError('URN is immutable.')

        poolname, resourcetype, index = parseUrn(urn)

        from ..dataset.classes import Class_Look_Up
        cls = Class_Look_Up[resourcetype.split('.')[-1]]

        self._poolname = poolname
        self._class = cls
        self._index = index
        self._urn = urn

        if poolurl:
            poolpath, scheme, place, poolname, self._username, self._password = parse_poolurl(
                poolurl, poolname)
            self._poolpath = poolpath
            self._scheme = scheme
            self._place = place
        else:
            self._poolpath = None
            self._scheme = None
            self._place = None
            self._username, self._password = None, None

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
        return OrderedDict(urn=self._urn if hasattr(self, '_urn') else None)

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

    string = toString
    txt = toString


def parseUrn(urn, int_index=True, check_poolename=None):
    """
    Checks the URN string is valid in its form and splits it.

    A Product URN has several segment. For example if the urn is ``urn:mypool/v2:proj1.product:322``
    * poolname, also called poolURN or poolID, optionally path-like: ``mypool/v2``,
    * resource type (usually class) name ``proj1.product``,
    * index number  ``322``,
    If urn is None or empty returns (None,None,None)

    Parameter
    ---------

    urn : str,list
        One or a list of URN strings to be decomposed.
    int_index : bool
        If `True` (default) returns integer index, else string index.
    check_poolename : str
        Raise `ValueError` is any `urn` has a poolname different from the value of `check_poolename`.

    Return
    ------

    tuple

    * If `urn` is `None` or a zero-length string, returns `(None, None, None)`.
    * If `urn` is a non-zero-length string, returns a tuple of

      :poolname: Name of the pool
      :resourceclass: type of resource/products
      :index: One or a list of (int) serial number of resourceclass in the pool.
    * If `urn` is a list URNs and all of them have identical poolname and identical resourceclasses, returns a tuple `(poolname, resourceclass, list-of-index])`
    * If `urn` is a list URNs and not all of them have identical poolname or not identical resourceclasses, returns a tuple `(list_of_poolname, list_of_resourceclass, list-of-index), ...)`

    """
    @functools.lru_cache(maxsize=512)
    def _parse(urn):
        if not issubclass(urn.__class__, strset):
            raise ValueError('a string is needed: ' + str(urn))
        # is a urn str?
        sp1 = urn.split(':')
        if sp1[0].lower() != 'urn':
            raise ValueError('Not a URN: ' + urn)
        # this is a product URN
        if len(sp1) != 4:
            # must have 4 segments
            raise ValueError(
                'Bad URN. Must have 4 ":"-separators: ' + str(sp1))

        i_index = int(sp1[3])
        resourcetype = sp1[2]
        poolname = sp1[1]
        if check_poolename and check_poolename != poolname:
            raise ValueError(
                urn + ' is not from the pool ' + self._poolname)
        if len(poolname) == 0:
            poolname = None
        if len(resourcetype) == 0:
            resourcetype = None
        return poolname, resourcetype, i_index
    if urn in [None, '', [], tuple()]:
        return (None, None, None)
    if issubclass(urn.__class__, (list, tuple)):
        urns = urn
        alist = True
    else:
        urns = [urn]
        alist = False
    res, pnames, ptypes, inds = [], [], [], []
    first = True
    same_pname, same_type = True, True
    for urn in urns:
        poolname, resourcetype, index = _parse(urn)
        if first:
            first_pname, first_type = poolname, resourcetype
            first = False
        else:
            if first_pname != poolname:
                same_pname = False
            if first_type != resourcetype:
                same_type = False
        pnames.append(poolname)
        ptypes.append(resourcetype)
        inds.append(index if int_index else str(index))
    if alist:
        if same_pname and same_type:
            return (first_pname, first_type, inds)
        # poolname and resourceclass not repeating
        return (pnames, ptypes, inds)
    else:
        return (first_pname, first_type, inds[0])


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
:<username>:
:<password>:

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
    if len(sp1) > 4:  # after scheme and a possible windows path, and one for user:pass
        raise ValueError(
            'a pool URN can have no more than 3 \':\'.')

    pr = urlparse(url.strip())
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
    return poolpath, scheme, place, poolname, pr.username, pr.password


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

        from ..dataset.classes import Class_Look_Up
        return Class_Look_Up[prod.rsplit('.', 1)[1]]

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
