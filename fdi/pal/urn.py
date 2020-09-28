# -*- coding: utf-8 -*-
from .comparable import Comparable
from ..dataset.serializable import Serializable
from ..dataset.odict import ODict
from ..dataset.eq import DeepEqual
from ..utils.common import fullname
import sys
import os
from collections import OrderedDict

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    strset = str
    from urllib.parse import urlparse
else:
    PY3 = False
    strset = (str, unicode)
    from urlparse import urlparse


# from .common import getClass


def parseUrn(urn):
    """
    Checks the URN string is valid in its form and splits it.
    Pool URN is in the form of a URL that does not have ':' in its path part.
    Product URNs are more complicated. For example if the urn is ``urn:file://c:/tmp/mypool/proj1.product:322`` into poolname ``file://c:/tmp/mypool``, resource type (usually class) name ``proj1.product``, serial number in string ``'322'``, scheme ``file``, place ``c:`` (with ip and port if given), and poolpath ``c:/tmp/mypool``
    Poolname is also called poolURN or poolID.
    """
    if not issubclass(urn.__class__, strset):
        raise TypeError('a urn string needed')
    # is a urn?
    sp1 = urn.split(':', 1)
    if sp1[0] == 'urn':
        # this is a product URL
        if len(sp1) < 2:
            raise ValueError('bad urn: ' + sp1[1])
        # maxsplit=2 so that if netloc is e.g. c: or http: , the : in it is not parsed:
        sp2 = sp1[1].rsplit(':', 2)
        if len(sp2) < 3:
            raise ValueError('bad urn: ' + sp1[1])
        serialnumstr = sp2[2]
        resourceclass = sp2[1]
        poolname = sp2[0]
    elif len(sp1[1].split(':')) > 3:  # after scheme and a possible windows path
        raise ValueError(
            'a product urn string must start with \'urn:\'; a pool URN can have no more than 2 \':\'.')
    else:
        # a pool urn
        poolname = urn
        resourceclass = None
        serialnumstr = None

    pr = urlparse(poolname)
    scheme = pr.scheme
    place = pr.netloc
    # convenient access path
    poolpath = place + pr.path if scheme in ('file') else pr.path
    return poolname, resourceclass, serialnumstr, scheme, place, poolpath


def makeUrn(poolname, typename, index):
    """ assembles a URN with infos of the pool, the resource type, and the index
    """
    return 'urn:' + poolname + ':' + typename + ':' + str(index)


class Urn(DeepEqual, Serializable, Comparable):
    """ The object representation of the product URN string. The
    memory consumed by sets of this object are much less than sets
    of URN strings.

    Only when the class types in URN string are not in classpath,
    the urn object will consume equals or a little more than URN string
    as the object has to hold the original urn string. However this should
    be considered as exceptional cases.

    Using this object representation also help to avoid parsing cost of    URN string.
    mh:
    URN format::

       urn:poolname:resourceclass:serialnumber

    where

    :resourceclass: (fully qualified) class name of the resource (product)
    :poolname: scheme + ``://`` + place + directory
    :scheme: ``file``, ``mem``, ``http`` ... etc
    :place: ``192.168.5.6:8080``, ``c:``, an empty string ... etc
    :directory:
      A label for the pool that is by default used as the full path where the pool is stored. ProductPool.transformpath() can used to change the directory here to other meaning.
         * for ``file`` scheme: ``/`` + name + ``/`` + name + ... + ``/`` + name
         * for ``mem`` scheme: ``/`` + name
    :serialnumber: internal index. str(int).

    URN is immutable.
    """

    def __init__(self, urn=None, pool=None, cls=None, index=None, **kwds):
        """
        Creates the URN object with the urn string or components.
        if urn is given and pool, class, etc are also specified,
        the latter are ignored. else the URN is constructed from them.
        Urn(u) will make a Urn object out of u.
        """
        super(Urn, self).__init__(**kwds)

        if urn is None:
            if cls is None or pool is None or index is None:
                if cls is None and pool is None and index is None:
                    self._scheme = None
                    self._place = None
                    self._pool = None
                    self._class = None
                    self._index = None
                    self._resource = None
                    self._poolpath = None
                    self._urn = None
                    return
                else:
                    raise ValueError('give urn or all other arguments')
            urn = makeUrn(poolname=pool,
                          typename=fullname(cls),
                          index=index)
        self.setUrn(urn)

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

    def setUrn(self, urn):
        """ parse urn to get scheme, place, pool, resource, index.
        """
        if hasattr(self, '_urn') and self._urn and urn:
            raise TypeError('URN is immutable.')

        poolname, resourcecn, indexs, scheme, place, poolpath = \
            parseUrn(urn)

        cls = resourcecn  # getClass(resourcecn)

        self._scheme = scheme
        self._place = place
        self._pool = poolname
        self._class = cls
        self._index = int(indexs)
        self._resource = resourcecn + ':' + indexs
        self._poolpath = poolpath
        self._urn = urn
        # logger.debug(urn)

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
        return self._class  # .__qualname__

    def getIndex(self):
        """ Returns the product index.
        """
        return self._index

    def getScheme(self):
        """ Returns the urn scheme.
        """
        return self._scheme

    def getUrnWithoutPoolId(self):
        return self._resource

    @property
    def place(self):
        return self.getPlace()

    def getPlace(self):
        """ Returns the netloc in this """
        return self._place

    @staticmethod
    def getFullPath(urn):
        """ returns the place+poolname+resource directory of the urn
        """
        poolname, resourcecn, indexs, scheme, place, poolpath = parseUrn(
            urn)
        return poolpath + '/' + resourcecn + '_' + indexs

    @property
    def pool(self):
        """ returns the pool URN.
        """
        return self.getPoolId()

    def getPoolId(self):
        """ Returns the pool URN in this """
        return self._pool

    def getPool(self):
        """ Returns the pool name in this """
        return self.getPoolId()

    def hasData(self):
        """ Returns whether this data wrapper has data. """
        return len(self.getData()) > 0

    def a__eq__(self, o):
        """
        mh: compare  urn string  after the first 4 letters.
        """

        return self.getUrn()[4:] == o.getUrn()[4:]

    def __hash__(self):
        """ returns hash of the URN string after the first 4 letters.
        """
        if not hasattr(self, 'HASH') or self.HASH is None:
            self.HASH = hash(self.getUrn()[4:])
        return self.HASH

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(urn=self.urn,
                           classID=self.classID)

    def __repr__(self):
        return self.__class__.__name__ + ' ' + self._urn

    def toString(self):
        return self.__class__.__name__ + \
            '{ %s, scheme:%s, place:%s, pool:%s, type:%s, index:%d, poolpath: %s}' % (
                self._urn,
                self._scheme,
                self._place,
                self._pool,
                self._class,  # .__name__,
                self._index,
                self._poolpath
            )
