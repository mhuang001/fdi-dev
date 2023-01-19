# -*- coding: utf-8 -*-

from ..dataset.baseproduct import BaseProduct
from ..dataset.classes import Classes
from ..dataset.product import Product
from ..dataset.serializable import serialize
from ..dataset.deserialize import deserialize, Class_Look_Up
from .urn import Urn, parseUrn, parse_poolurl, makeUrn
from .versionable import Versionable
from .taggable import Taggable
from . import dicthk
from .definable import Definable
from ..utils.common import pathjoin, fullname, lls, trbk
from .productref import ProductRef
from .query import AbstractQuery, MetaQuery, StorageQuery

from collections import OrderedDict, ChainMap
from functools import lru_cache
import logging
import filelock
import getpass
import functools
import os
import sys
import builtins

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    from urllib.parse import urlparse
else:
    PY3 = False
    from urlparse import urlparse

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

Lock_Path_Base = '/tmp/fdi_locks_' + getpass.getuser()
# lock time-out
locktout = 10


def makeLockpath(direc, op='w'):
    """ returns the appropriate path to put lock file.

    creats the path if non-existing. Set lockpath-base permission to all-modify so other fdi users can use.
    op: 'r' for readlock no-reading) 'w' for writelock (no-writing)
    """
    if not os.path.exists(Lock_Path_Base):
        os.makedirs(Lock_Path_Base, mode=0o777)

    lp = pathjoin(Lock_Path_Base, direc.replace('/', '_'))

    return lp+'.read' if op == 'r' else lp+'.write'


class ProductPool(Definable, Taggable, Versionable):
    """ A mechanism that can store and retrieve Products.

A product pool should not be used directly by users. The general user should access data in a ProductPool through a ProductStorage instance.

When implementing a ProductPool, the following rules need to be applied:

    1. Pools must guarantee that a Product saved via the pool saveProduct(Product) method is stored persistently, and that method returns a unique identifier (URN). If it is not possible to save a Product, an IOException shall be raised.
    2. A saved Product can be retrieved using the loadProduct(Urn) method, using as the argument the same URN that assigned to that Product in the earlier saveProduct(Product) call. No other Product shall be retrievable by that same URN. If this is not possible, an IOException or GeneralSecurityException is raised.
    3. Pools should not implement functionality currently implemented in the core package. Specifically, it should not address functionality provided in the Context abstract class, and it should not implement versioning/cloning support.

    """

    def __init__(self, poolname='', poolurl='', **kwds):
        """
        Creates and initializes a productpool.

        * poolname: if provided will override that in poolurl.
        * poolurl: needed to initialize.

        """
        super().__init__(**kwds)

        self.setPoolname(poolname)
        self.setPoolurl(poolurl)
        # self._pathurl = pr.netloc + pr.path
        # self._pathurl = None
        self._poolmanager = None

    class ParametersIncommpleteError(Exception):
        pass

    def setup(self):
        """ Sets up interal machiney of this Pool,
        but only if self._poolname and self._poolurl are present,
        and other pre-requisits are met.

        Subclasses should implement own setup(), and
        make sure that self._poolname and self._poolurl are present with ``

        if <pre-requisit not met>: return True
        if super().setup(): return True

        # super().setup() has done its things by now.
        <do setup>
        return False
``
        returns: True if not both  self._poolname and self._poolurl are present.

        """

        if not hasattr(self, '_poolurl') or not self._poolurl:
            return True

        return False

    @property
    def poolname(self):
        """ for property getter
        """
        return self.getPoolname()

    @poolname.setter
    def poolname(self, poolname):
        """ for property setter
        """
        self.setPoolname(poolname)

    def getPoolname(self):
        """ Gets the poolname of this pool as an Object. """
        return self._poolname

    def setPoolname(self, poolname):
        """ Replaces the current poolname of this pool.
        """
        self._poolname = poolname

    @property
    def poolurl(self):
        """ for property getter
        """
        return self.getPoolurl()

    @poolurl.setter
    def poolurl(self, poolurl):
        """ for property setter
        """
        self.setPoolurl(poolurl)

    def getPoolurl(self):
        """ Gets the poolurl of this pool as an Object. """
        return self._poolurl

    def setPoolurl(self, poolurl):
        """ Replaces the current poolurl of this pool.
        """
        s = (not hasattr(self, '_poolurl') or not self._poolurl)
        self._poolpath, self._scheme, self._place, \
            self._poolname, self._username, self._password = \
            parse_poolurl(poolurl)
        self._poolurl = poolurl
        # call setup only if poolurl was None
        if s:
            self.setup()

    def accept(self, visitor):
        """ Hook for adding functionality to object
        through visitor pattern."""
        visitor.visit(self)

    def getPoolManager(self):
        """
        """
        return self._poolmanager

    def setPoolManager(self, pm):
        """
        """
        self._poolmanager = pm

    def dereference(self, ref):
        """
        Decrement the reference count of a ProductRef.

        XXX TODO
        """

        raise (NotImplementedError)

    def exists(self, urn):
        """
        Determines the existence of a product with specified URN.
        """

        raise (NotImplementedError)

    def getDefinition(self):
        """
        Returns pool definition info which contains pool type and other pool specific configuration parameters
        """
        return super().getDefinition()

    def getId(self):
        """
        Gets the identifier of this pool.
        """
        return self._poolname

    def getPoolurl(self):
        """
        Gets the pool URL of this pool.
        """
        return self._poolurl

    def getPlace(self):
        """
        Gets the place of this pool.
        """
        return self._place

    def getProductClasses(self):
        """
        Returns all Product classes found in this pool.
        mh: returns an iterator.
        """
        raise (NotImplementedError)

    def getReferenceCount(self, ref):
        """
        Returns the reference count of a ProductRef.
        """
        raise (NotImplementedError)

    def getScheme(self):
        """
        Gets the scheme of this pool.
        """
        return self._scheme

    def getUrnId(self):
        """
        Get the identifier of this pool used to build URN, usually it's same as id returned by getId().
        """
        return self.getId()

    def isAlive(self):
        """
        Test if the pool is capable of responding to commands.
        """
        return True

    def isEmpty(self):
        """
        Determines if the pool is empty.
        """

        raise NotImplementedError

    def schematicSave(self, products, tag=None, geturnobjs=False, serialize_in=True, serialize_out=False, **kwds):
        """ to be implemented by subclasses to do the scheme-specific saving
        """
        raise (NotImplementedError)

    def saveProduct(self, product, tag=None, geturnobjs=False, serialize_in=True, serialize_out=False, **kwds):
        """
        Saves specified product and returns the designated ProductRefs or URNs.

        Saves a product or a list of products to the pool, possibly under the
        supplied tag(s), and returns the reference (or a list of references if
        the input is a list of products), or Urns if geturnobjs is True.

        See pal document for pool structure.


        tag: a tag if given as a string type; a list of tags if given a list.
        serialize_out: if True returns contents in serialized form.
        """

        res = self.schematicSave(product, tag=tag,
                                 geturnobjs=geturnobjs,
                                 serialize_in=serialize_in,
                                 serialize_out=serialize_out, **kwds)
        if issubclass(product.__class__, str) or isinstance(product, list) and \
           issubclass(product[0].__class__, str):
            # p is urn string from server-side LocalPool
            return res

        if isinstance(res, list):
            for p, u in zip(product, res):
                p._urn = u if geturnobjs else u.getUrnObj()
        else:
            product._urn = res if geturnobjs else res.getUrnObj()
        return res

    def loadDescriptors(self, urn):
        """
        Loads the descriptors belonging to specified URN.
        """

        raise (NotImplementedError)

    def schematicLoad(self, resourcetype, index,
                      start=None, end=None, serialize_out=False):
        """ to be implemented by subclasses to do the scheme-specific loading
        """
        raise (NotImplementedError)

    def loadProduct(self, urn, serialize_out=False):
        """
        Loads a Product belonging to specified URN.

        serialize_out: if True returns contents in serialized form.
        """
        poolname, resource, index = parseUrn(urn)
        if poolname != self._poolname:
            raise (ValueError('wrong pool: ' + poolname +
                              ' . This is ' + self._poolname))
        ret = self.schematicLoad(
            resourcetype=resource, index=index, serialize_out=serialize_out)

        if issubclass(ret.__class__, str) or isinstance(ret, list) and \
           issubclass(ret[0].__class__, str):
            # ret is a urn string from server-side LocalPool
            return ret

        if isinstance(ret, list):
            logger.warning('TODO: unexpected')
            for x, u in zip(ret, urn):
                x._urn = u
        else:
            ret._urn = urn

        return ret

    def meta(self, urn):
        """
        Loads the meta-data belonging to the product of specified URN.
        """

        raise (NotImplementedError)

    @property
    def count(self):
        """ for property getter
        """
        return self.getCount()

    @count.setter
    def count(self, count):
        """ for property setter
        """
        raise ValueError('Pool.count is read-only.')

    def getCount(self, typename=None):
        """
        Return the number of URNs for the product type.
        """

        raise (NotImplementedError)

    def reference(self, ref):
        """
        Increment the reference count of a ProductRef.
        """

        raise (NotImplementedError)

    def schematicRemove(self, urn=None, resourcetype=None, index=None):
        """ to be implemented by subclasses to do the scheme-specific removing
        """
        raise (NotImplementedError)

    def remove(self, urn=None, resourcetype=None, index=None,
               ignore_error=False):
        """
        Removes a Product belonging to specified URN or a pair of data type and serial number.
        """
        self.ignore_error_when_delete = ignore_error
        res = self.schematicRemove(urn, resourcetype=resourcetype, index=index)
        return res

    def schematicWipe(self):
        """ to be implemented by subclasses to do the scheme-specific wiping.
        """
        raise (NotImplementedError)

    def removeAll(self, ignore_error=False):
        """
        Remove all pool data (self, products) and all pool meta data (self, descriptors, indices, etc.).
        """
        self.ignore_error_when_delete = ignore_error
        return self.schematicWipe()

    def saveDescriptors(self,  urn,  desc):
        """
        Save/Update descriptors in pool.
        """
        raise (NotImplementedError)

    def schematicSelect(self,  query, previous=None):
        """
        to be implemented by subclasses to do the scheme-specific querying.
        """
        raise (NotImplementedError)

    def select(self,  query, variable='m', ptype=Product,
               previous=None):
        """Returns a list of references to products that match the specified query.

        Parameters
        ----------
        query : str
            the 'where' query string to make a query object.
        variable : str
            name of the dummy variable in the query string.
            if `variable` is 'm', query goes via `MetaQuery(ptype, query)` ; else by `AbstractQuery(ptype, variable, query)` .
        ptype : class
            The class object whose instances are to be queried. Or
            fragment of the name of such classes.
        previous : list or str
            of urns, possibly from previous search. or a string of comma-separated urns, e.g. `'urn:a:foo:12,urn:b:bar:9'`

        Returns
        -------
        list
            of found URNs.

        """
        if issubclass(previous.__class__, str):
            previous = previous.split(',')
        if issubclass(query.__class__, StorageQuery):
            res = self.schematicSelect(query, previous)
            return res
        if issubclass(ptype.__class__, str):
            for cn, cls in Classes.mapping.items():
                if ptype in cn and issubclass(cls, BaseProduct):
                    break
            else:
                raise (ValueError(ptype + ' is not a product type.'))
            ptype = cls
        if variable == 'm':
            res = self.schematicSelect(MetaQuery(ptype, where=query), previous)
        else:
            res = self.schematicSelect(AbstractQuery(
                ptype, where=query, variable=variable), previous)
        return res

    def qm(self, qw, prod='BaseProduct', urns=None):
        """ short-hand method for `select(qw, variable'm', ptype=prod, previous=urns`.

        example:
        ..code:
        curl http://foo.edu:23456/data/pool/api/qm__m["age"]>66 and m["name"]=="Bob"'
        """
        return self.select(qw, variable='m', ptype=prod, previous=urns)

    def __repr__(self):
        co = ', '.join(str(k) + '=' + lls(v, 40)
                       for k, v in self.__getstate__().items())
        # co = ', '.join(str(k)+'=' + (v if issubclass(v.__class__, str) else
        #                              '<' + v.__class__.__name__+'>') \
        #                for k, v in self.__getstate__().items())
        return '<'+self.__class__.__name__ + ' ' + co + '>'

    def __getstate__(self):
        """ returns an odict that has all state info of this object.
        Subclasses should override this function.
        """
        return OrderedDict(
            poolurl=self._poolurl if hasattr(self, '_poolurl') else None,
        )

###########################


class PoolNotFoundError(Exception):
    pass


def _eval(code='', m='', **kwds):
    """ evaluate compiled code with given local vars. """
    try:
        res = eval(code)
    except NameError:
        res = False
        logger.debug("Evaluation error: %s. Traceback %s" %
                     (str(e), trbk(e)))

    return res


def populate_pool2(tags, pn, dTypes=None, dTags=None):
    """
    tags : list
        The tags in a list.
    pn : str
        The product name / datatype / class name of the data item, new or existing.

    Returns
    -------
    tuple
        dTypes and dTags with updates, and the index/serial number
    """

    # new ###
    if dTypes is None:
        dTypes = {}
    if dTags is None:
        dTags = {}

    if pn in dTypes:
        int_sn = dTypes[pn]['currentSN'] + 1
    else:
        int_sn = 0
        dTypes[pn] = {
            'currentSN': int_sn,
            'sn': {}
        }

    snd = dTypes[pn]['sn']
    _sn = str(int_sn)
    if int_sn not in snd:
        snd[int_sn] = {
            'tags': [],
            'meta': []
        }

    dTypes[pn]['currentSN'] = int_sn

    # /new #####
    for t in tags:
        dicthk.add_tag_datatype_sn(t, pn, int_sn, dTypes, dTags)

    return dTypes, dTags, _sn


# Do not include leading or trailing whitespace as they are not guarantteed.
MetaData_Json_Start = '{"_ATTR_meta":'
MetaData_Json_End = '"_STID": "MetaData"}'


class ManagedPool(ProductPool, dicthk.DictHk):
    """ A ProductPool that manages its internal house keeping. """

    def __init__(self, **kwds):
        super().__init__(**kwds)
        # {type|classname -> {'sn:[sn]'}}

    def setup(self):
        """ Sets up interal machiney of this Pool,
        but only if self._poolname and self._poolurl are present,
        and other pre-requisits are met.

        Subclasses should implement own setup(), and
        make sure that self._poolname and self._poolurl are present with ``

        if <pre-requisit not met>: return True
        if super().setup(): return True

        # super().setup() has done its things by now.
        <do setup>
        return False
``
        returns: True if not both  self._poolname and self._poolurl are present.

        """

        if super().setup():
            return True
        self._classes = dict()
        # new ##
        self._dTypes = dict()
        return False

    def getPoolpath(self):
        """
        Gets the poolpath of this pool.

        poolpath is usually derived from poolurl received from ``PoolManager`` during initialization.
        """
        return self._poolpath

    def lockpath(self, op='w'):
        """ Make lock path using transformed poolname as name.

        """
        return makeLockpath(self.transformpath(self._poolname), op)

    @ lru_cache(maxsize=32)
    def transformpath(self, path):
        """ override this to changes the output from the input one (default) to something else.

        """
        if path is None:
            return None
        base = self._poolpath
        if base != '':
            if path[0] == '/':
                path = base + path
            else:
                path = base + '/' + path
        return path

    def getCacheInfo(self):
        info = {}
        for i in ['transformpath']:
            info[i] = getattr(self, i).cache_info()

        return info

    def dereference(self, ref):
        """
        Decrement the reference count of a ProductRef.
        """
        # new ###
        poolname, dt, sn = parseUrn(urn, int_index=True)
        # assert self._urns[ref.urn]['refcnt'] == self._dType[dt]['sn'][sn]['refcnt']
        r = self._dType[dt]['sn'][sn]
        if r['refcnt'] == 0:
            raise ValueError('Cannot deref below 0.')
        else:
            r['refcnt'] -= 1
        # /new ###
        # self._urns[ref.urn]['refcnt'] -= 1

    def exists(self, urn, resourcetype=None, index=None):
        """
        Determines the existence of a product with specified URN.
        """
        # new ###
        try:
            urn, datatype, sn = self.get_missing(urn, resourcetype, index)
        except KeyError:
            return False
        # return True
        # /new#
        return urn in self._urns

    def getProductClasses(self):
        """
        Returns all Product classes found in this pool.
        mh: returns an iterator.
        """
        # new ###
        assert list(self._classes.keys()) == list(self._dTypes.keys())

        return self._classes.keys()

    def getCount(self, typename=None):
        """
        Return the number of URNs for the product type.
        """
        try:
            # new ###
            # assert len(self._classes[typename]['sn']) == len(
            # self._dTypes[typename]['sn'])
            if typename:
                return len(self._dTypes[typename]['sn'])
            else:
                return sum(len(dt['sn']) for dt in self._dTypes.values())
        except KeyError:
            return 0

    def doSave(self, resourcetype, index, data, tags=None, serialize_in=True, **kwds):
        """ to be implemented by subclasses to do the action of saving
        """
        raise (NotImplementedError)

    def getReferenceCount(self, ref):
        """
        Returns the reference count of a ProductRef.
        """
        # new ###
        poolname, dt, sn = parseUrn(urn, int_index=False)
        _snd = self._dType[dt]['sn'][sn]
        # assert self._urns[ref.urn]['refcnt'] == _snd['refcnt']
        return _snd['refcnt']
        # /new ###
        # return self._urns[ref.urn]['refcnt']

    def isEmpty(self):
        """
        Determines if the pool is empty.
        """
        # new ###
        # assert len(self._urns) == len(self._dTypes)
        # return len(self._urns) == 0
        return len(self._dTypes) == 0

    def loadDescriptors(self, urn, resourcetype=None, index=None):
        """
        Loads the descriptors belonging to specified URN.
        """
        # new ###
        urn, datatype, sn = self.get_missing(urn, resourcetype, index)
        return self._dTypes
        # return self._urns[urn]

    def setMetaByUrn(self, start, end, urn=None, datatype=None, sn=None):
        """
        Sets the location of the meta data of the specified data to the given URN or a pair of data type and serial number.

        :data: usually un/serialized Product.

        Return
        :urn: stirng
        :datatype: class name
        :sn: serial number in string.
        """

        raise NotImplemented

    def getMetaByUrn(self, urn=None, resourcetype=None, index=None):
        """
        Get all of the meta data belonging to a product of a given URN.

        mh: returns an iterator.
        """
        raise NotImplemented

    def meta(self, *args, **kwds):
        """
        Loads the meta-data info belonging to the product of specified URN.
        """
        return self.getMetaByUrn(*args, **kwds)

    def reference(self, ref):
        """
        Increment the reference count of a ProductRef.
        """
        # new ###
        poolname, dt, sn = parseUrn(ref.urn, int_index=True)
        _snd = self._dType[dt]['sn'][sn]
        if 'refcnt' not in _snd:
            _snd['refcnt'] = 0
        ####assert self._urns[ref.urn]['refcnt'] == _snd['refcnt']
        _snd['refcnt'] += 1
        # /new ###
        if 0:
            if 'refcnt' not in self._urns:
                self._urns['refcnt'] = 0
            self._urns[ref.urn]['refcnt'] += 1

    def saveOne(self, prd, tag, geturnobjs, serialize_in, serialize_out, res, kwds):
        """
        Save one product.

            # get the latest HK

            the new classes and tags.
               dTypes combines old classes and urns, is defined as::
                     $class_name0:
                            'currentSN': $sn
                            'sn':
                                $sn0:
                                   tags: [$tag1, $tag2, ...
                                   meta: [$start, $end]
                                   refcnt: $count
                                $sn1:
                                   tags: [$tag1, $tag2, ...
                                   meta: [$start, $end]
                                   refcnt: $count
               example::
                    'foo.bar.Bar':
                            'currentSN': 1
                            0:
                               'tags': ['cat', 'white']
                               'meta': [123, 456]
                               'refcnt': 0
                            1:
                               'tags': ['dog', 'white']
                               'meta': [321, 765]
                               'refcnt': 0
                    'foo.baz.Baz':
                            'currentSN': 34
                            34:
                               'tags': ['tree', 'green']
                               'meta': [100, 654]
                               'refcnt': 1
     `dTags` differs from `tag` 1. uses dType:[sn], instead of urn, so there is no poolname anywhere, 2. simplify by removing second level dict::
                     $tag_name0:
                           $class_name1:[$sn1, $sn2...]
                           $class_name2:[$sn3, ...]
               example::
                     'cat': { 'foo.bar.Bar':[0] }
                     'white': { 'foo.bar.Bar'; [0, 1] }
                     'dog': ...

        :res: list of result.
        :serialize_out: if True returns contents in serialized form.

        Return
        ------
        `list` of the following:
        `ProductRef`. `Urn` if `geturnobjs` is set. if`serialze_out` is set for `ProductRef` no product metadata is stored in the returned instance.
        The result is also stored in the `re` parameter.
        """
        if serialize_in:
            pn = fullname(prd)
            cls = prd.__class__
        else:
            # prd is json. extract prod name
            # '... "_STID": "Product"}]'
            pn = prd.rsplit('"', 2)[1]
            cls = Class_Look_Up[pn]
            pn = fullname(cls)
        with filelock.FileLock(self.lockpath('w')), \
                filelock.FileLock(self.lockpath('r')):
            # some new ####
            self._classes, self._tags, self._urns, \
                self._dTypes, self._dTags = tuple(
                    self.readHK().values())
            # /some new ####
            if 0:
                c, t, u = self._classes, self._tags, self._urns

                if pn in c:
                    sn = (c[pn]['currentSN'] + 1)
                else:
                    sn = 0
                    c[pn] = dict(sn=[])

                c[pn]['currentSN'] = sn
                c[pn]['sn'].append(sn)

                urn = makeUrn(poolname=self._poolname, typename=pn, index=sn)

                if urn not in u:
                    u[urn] = {'tags': []}

            # new+old ###
            if tag is None:
                tags = []
            elif issubclass(tag.__class__, str):
                tags = [tag]
            elif issubclass(tag.__class__, list):
                tags = tag
            else:
                raise TypeError('Bad type for tag: %s.' %
                                tag.__class__.__name__)
            # new ####
            self._dTypes, self._dTags, _sn = populate_pool2(tags, pn,
                                                            self._dTypes,
                                                            self._dTags)

            if 0:
                if tag is None:
                    tags = []
                elif issubclass(tag.__class__, str):
                    tags = [tag]
                elif issubclass(tag.__class__, list):
                    tags = tag
                else:
                    raise TypeError('Bad type for tag: %s.' %
                                    tag.__class__.__name__)
                # new ####
                dTypes, dTags = self._dTypes, self._dTags

                if pn in dTypes:
                    _sn = dTypes[pn]['currentSN'] + 1
                else:
                    _sn = 0
                    dTypes[pn] = {
                        'currentSN': _sn,
                        'sn': {}
                    }

                snd = dTypes[pn]['sn']
                if _sn not in snd:
                    snd[_sn] = {
                        'tags': [],
                        'meta': []
                    }

                dTypes[pn]['currentSN'] = _sn
                urn = makeUrn(poolname=self._poolname, typename=pn, index=_sn)
                # /new #####

                for t in tags:
                    self.setTag(t, urn)
            urn = makeUrn(poolname=self._poolname, typename=pn, index=_sn)
            try:
                # save prod and HK
                self.doSave(resourcetype=pn,
                            index=_sn,
                            data=prd,
                            tags=tags,
                            serialize_in=serialize_in,
                            serialize_out=serialize_out,
                            **kwds)
            except ValueError as e:
                msg = 'product ' + urn + ' saving failed.' + str(e) + trbk(e)
                logger.debug(msg)
                # some new ##
                self._classes, self._tags, self._urns, \
                    self._dTypes, self._dTags = tuple(
                        self.readHK().values())
                raise e

        if geturnobjs:
            if serialize_out:
                # return the URN string.
                res.append(urn)
            else:
                res.append(Urn(urn, poolurl=self._poolurl))
        else:
            rf = ProductRef(urn=Urn(urn, poolurl=self._poolurl),
                            poolmanager=self._poolmanager)
            if serialize_out:
                # return without meta
                res.append(rf)
            else:
                # it seems that there is no better way to set meta
                rf._meta = prd.getMeta()
                res.append(rf)

    def schematicSave(self, products, tag=None, geturnobjs=False, serialize_in=True, serialize_out=False, **kwds):
        """ do the scheme-specific saving.
        :product:  product or '[ size1, prd, size2, prd2, ...]'.
        :serialize_out: if True returns contents in serialized form.
        :serialize_in: if set, product input is seriaized.

        Return
        ------
        `ProductRef`. `Urn` if `geturnobjs` is set. If `serialze_out` is set `str` of serialized form of `ProductRef` or `URN`.

        `list` of the above of input is a list.
        """
        res = []

        if serialize_in:
            alist = issubclass(products.__class__, list)
            if not alist:
                prd = products
                self.saveOne(prd, tag, geturnobjs,
                             serialize_in, serialize_out, res, kwds)
            else:
                for prd in products:
                    # result is in res
                    self.saveOne(prd, tag, geturnobjs,
                                 serialize_in, serialize_out, res, kwds)
        else:
            alist = products.lstrip().startswith('[')
            if not alist:
                prd = products
                self.saveOne(prd, tag, geturnobjs,
                             serialize_in, serialize_out, res, kwds)
            else:
                # parse '[ size1, prd, size2, prd2, ...]'

                last_end = 1
                productlist = []
                comma = products.find(',', last_end)
                while comma > 0:
                    length = int(products[last_end: comma])
                    productlist.append(length)
                    last_end = comma + 1 + length
                    prd = products[comma + 2: last_end+1]
                    self.saveOne(prd, tag, geturnobjs,
                                 serialize_in, serialize_out, res, kwds)
                    # +2 to skip the following ', '
                    last_end += 2
                    comma = products.find(',', last_end)
        sz = 1 if not alist else len(
            products) if serialize_in else len(productlist)
        logger.debug('%d product(s) generated %d %s: %s.' %
                     (sz, len(res), 'Urns ' if geturnobjs else 'prodRefs', lls(res, 200)))
        if alist:
            return serialize(res) if serialize_out else res
        else:
            return serialize(res[0]) if serialize_out else res[0]

    def doLoad(self, resourcetype, index, start=None, end=None, serialize_out=False):
        """ to be implemented by subclasses to do the action of loading
        """
        raise (NotImplementedError)

    def schematicLoad(self, resourcetype, index, start=None, end=None,
                      serialize_out=False):
        """ do the scheme-specific loading
        """

        with filelock.FileLock(self.lockpath('w')):
            ret = self.doLoad(resourcetype=resourcetype,
                              index=index, start=start, end=end,
                              serialize_out=serialize_out)
        return ret

    def doRemove(self, resourcetype, index):
        """ to be implemented by subclasses to do the action of reemoving
        """
        raise (NotImplementedError)

    def schematicRemove(self, urn=None, resourcetype=None, index=None):
        """ do the scheme-specific removing
        """

        urn, datatype, sn = self.get_missing(urn, resourcetype, index)

        with filelock.FileLock(self.lockpath('w')),\
                filelock.FileLock(self.lockpath('r')):

            # get the latest HK
            # some new ####
            self._classes, self._tags, self._urns, \
                self._dTypes, self._dTags = tuple(
                    self.readHK().values())
            if 0:
                c, t, u = self._classes, self._tags, self._urns
                if urn not in u:
                    raise ValueError(
                        '%s not found in pool %s.' % (urn, self.getId()))

            # new ####
            dTypes, dTags = self._dTypes, self._dTags

            if sn not in dTypes[datatype]['sn']:
                raise ValueError(
                    '%d not found in pool %s.' % (sn, self.getId()))
            # /new ####

            self.removeUrn(urn, datatype=datatype, sn=sn)

            if 0:
                c[datatype]['sn'].remove(sn)

                if len(c[datatype]['sn']) == 0:
                    del c[datatype]
            # new ####
            if len(dTypes[datatype]['sn']) == 0:
                del dTypes[datatype]
            else:
                ####assert list(dTypes[datatype]['sn']) == list(c[datatype]['sn'])
                pass
            # /new ####
            try:
                self.doRemove(resourcetype=datatype, index=sn)
            except Exception as e:
                msg = 'product ' + urn + ' removal failed'
                logger.debug(msg)
                self._classes, self._tags, self._urns, \
                    self._dTypes, self._dTags = tuple(
                        self.readHK().values())
                raise e
        return 0

    def doWipe(self):
        """ to be implemented by subclasses to do the action of wiping.
        """
        raise (NotImplementedError)

    def schematicWipe(self):
        """ do the scheme-specific wiping
        """
        with filelock.FileLock(self.lockpath('w')),\
                filelock.FileLock(self.lockpath('r')):
            try:
                if 0:
                    self._classes.clear()
                    self._tags.clear()
                    self._urns.clear()
                # new ##
                self._dTypes.clear()
                self._dTags.clear()
                # /new ##
                self.doWipe()
            except Exception as e:
                msg = self.getId() + 'wiping failed'
                logger.debug(msg)
                raise e
        logger.debug('Done.')
        return 0

    def meta_filter(self, q, typename=None, reflist=None, urnlist=None, snlist=None, datatypes=None):
        """ returns filtered collection using the query.

        q is a MetaQuery
        valid inputs: typename and ns list; productref list; urn list; datatypes dict.

        :typename: data type (class name)
        :reflist: list of ProductRefs
        :urnlist: list of URNs
        :datatypes:  dict of {typename:sn_list}
        """

        ret = []
        qw = q.getWhere()

        if reflist:
            if isinstance(qw, str):
                code = compile(qw, 'qw.py', 'eval')
                for ref in reflist:
                    refmet = ref.getMeta()
                    m = refmet if refmet else self.getMetaByUrn(ref.urn)
                    if _eval(code=code, m=m):
                        ret.append(ref)
                return ret
            else:
                for ref in reflist:
                    refmet = ref.getMeta()
                    m = refmet if refmet else self.getMetaByUrn(ref.urn)
                    if qw(m):
                        ret.append(ref)
                return ret
        elif urnlist:
            if isinstance(qw, str):
                code = compile(qw, 'qw.py', 'eval')
                for urn in urnlist:
                    m = self.getMetaByUrn(urn)
                    if _eval(code=code, m=m):
                        ret.append(ProductRef(urn=urn, meta=m,
                                   poolmanager=self._poolmanager))
                return ret
            else:
                for urn in urnlist:
                    m = self.getMetaByUrn(urn)
                    if qw(m):
                        ret.append(ProductRef(urn=urn, meta=m,
                                   poolmanager=self._poolmanager))
                return ret
        elif snlist or datatypes:
            if isinstance(qw, str):
                code = compile(qw, 'qw.py', 'eval')
                if snlist:
                    datatypes = {typename: snlist}
                for cls in datatypes:
                    snlist = datatypes[cls]
                    for n in snlist:
                        urn = makeUrn(poolname=self._poolname,
                                      typename=typename, index=n)
                        m = self.getMetaByUrn(urn)
                        if _eval(code=code, m=m):
                            ret.append(ProductRef(urn=urn, meta=m,
                                       poolmanager=self._poolmanager))
                return ret
            else:
                if snlist:
                    datatypes = {typename: snlist}
                for cls in datatypes:
                    snlist = datatypes[cls]
                    for n in snlist:
                        urn = makeUrn(poolname=self._poolname,
                                      typename=typename, index=n)
                        m = self.getMetaByUrn(urn)
                        if qw(m):
                            ret.append(ProductRef(urn=urn, meta=m,
                                       poolmanager=self._poolmanager))
                return ret
        else:
            raise ('Must give a list of ProductRef or urn or sn')

    def prod_filter(self, q, cls=None, reflist=None, urnlist=None, snlist=None, datatypes=None):
        """ returns filtered collection using the query.

        q: an AbstractQuery.
        valid inputs: cls and ns list; productref list; urn list; datatypes dict.

        :cls: type. data type
        :reflist: list of ProductRefs
        :urnlist: list of URNs
        :datatypes:  dict of {cls:sn_list}
        """

        ret = []
        # will add query variable (e.g. 'p') to Global name space
        glbs = globals()
        qw = q.getWhere()
        var = q.getVariable()
        if var in glbs:
            savevar = glbs[var]
        else:
            savevar = 'not in glbs'

        if reflist:
            if isinstance(qw, str):
                code = compile(qw, 'qw.py', 'eval')
                for ref in reflist:
                    glbs[var] = pref.getProduct()
                    if _eval(code=code, m=m):
                        ret.append(ref)
                if savevar != 'not in glbs':
                    glbs[var] = savevar
                return ret
            else:
                for ref in reflist:
                    glbs[var] = pref.getProduct()
                    if qw(m):
                        ret.append(ref)
                if savevar != 'not in glbs':
                    glbs[var] = savevar
                return ret
        elif urnlist:
            if isinstance(qw, str):
                code = compile(qw, 'qw.py', 'eval')
                for urn in urnlist:
                    pref = ProductRef(urn=urn, poolmanager=self._poolmanager)
                    glbs[var] = pref.getProduct()
                    if _eval(code=code):
                        ret.append(pref)
                if savevar != 'not in glbs':
                    glbs[var] = savevar
                return ret
            else:
                for urn in urnlist:
                    pref = ProductRef(urn=urn, poolmanager=self._poolmanager)
                    glbs[var] = pref.getProduct()
                    if qw(glbs[var]):
                        ret.append(pref)
                if savevar != 'not in glbs':
                    glbs[var] = savevar
                return ret
        elif snlist or datatypes:
            if isinstance(qw, str):
                code = compile(qw, 'qw.py', 'eval')
                if snlist:
                    datatypes = {cls.__name__: snlist}
                for typename in datatypes:
                    snlist = datatypes[typename]
                    cls = Class_Look_Up[typename.rsplit('.', 1)[-1]]
                    for n in snlist:
                        urno = Urn(cls=cls, poolname=self._poolname, index=n)
                        pref = ProductRef(
                            urn=urno, poolmanager=self._poolmanager)
                        glbs[var] = pref.getProduct()
                        if _eval(code=code):
                            ret.append(pref)
                    if savevar != 'not in glbs':
                        glbs[var] = savevar
                return ret
            else:
                if snlist:
                    datatypes = {cls.__name__: snlist}
                for typename in datatypes:
                    snlist = datatypes[typename]
                    cls = glbs[typename]
                    for n in snlist:
                        urno = Urn(cls=cls, poolname=self._poolname, index=n)
                        pref = ProductRef(
                            urn=urno, poolmanager=self._poolmanager)
                        glbs[var] = pref.getProduct()
                        if qw(glbs[var]):
                            ret.append(pref)
                    if savevar != 'not in glbs':
                        glbs[var] = savevar
                return ret
        else:
            raise ('Must give a list of ProductRef or urn or sn')

    def where(self, qw, prod='BaseProduct', urns=None):
        q = AbstractQuery(prod, 'p', qw)
        # if urns is None:
        # new ###
        datatypes = dict((k, list(v['sn'].keys()))
                         for k, v in self._dTypes.items())
        if 0:
            urns = self._urns.keys()
            res = self.prod_filter(q, prod, urnlist=urns)
        # new ###
        res2 = self.prod_filter(q, prod, datatypes=datatypes)

        #### assert [r.urn for r in res] == [r.urn for r in res2]
        return [r.urn for r in res2]

    def doSelect(self, query, previous=None):
        """
        to be implemented by subclasses to do the action of querying.
        """
        raise (NotImplementedError)

    def schematicSelect(self,  query, previous=None):
        """
        do the scheme-specific querying.
        """
        is_MetaQ = issubclass(query.__class__, MetaQuery)
        is_AbstQ = issubclass(query.__class__, AbstractQuery)
        if not is_MetaQ and not is_AbstQ:
            raise TypeError('not a Query')
        lgb = Classes.mapping
        t, v, w, a = query.getType(), query.getVariable(
        ), query.getWhere(), query.retrieveAllVersions()
        ret = []
        if previous:
            this = (x for x in previous if x.urnobj.getPoolId()
                    == self._poolname)
            if is_MetaQ:
                ret += self.meta_filter(q=query, reflist=this)
            else:
                ret += self.prod_filter(q=query, reflist=this)
        else:
            # new ##
            #### assert list(self._dTypes) == list(self._classes)
            for cname in self._dTypes:
                cls = lgb[cname.rsplit('.', 1)[-1]]
                if issubclass(cls, t):
                    ###snlist = self._classes[cname]['sn']
                    # new ###
                    ####assert snlist == list(self._dTypes[cname]['sn'])
                    snlist = list(self._dTypes[cname]['sn'])
                    if is_MetaQ:
                        ret += self.meta_filter(q=query, typename=cname,
                                                snlist=snlist)
                    else:
                        ret += self.prod_filter(q=query, cls=cls,
                                                snlist=snlist)

        return ret

    def __repr__(self):
        # co = ', '.join(str(k) + '=' + lls(v, 40)
        #               for k, v in self.__getstate__().items())
        co = ', '.join(str(k)+'=' + (v if issubclass(v.__class__, str) else
                                     f'< {v.__class__.__name__} {len(v)} >')
                       for k, v in self.__getstate__().items())
        return '<'+self.__class__.__name__ + ' ' + co + '>'

    def __getstate__(self):
        """ returns an odict that has all state info of this object.
        Subclasses should override this function.
        """
        return OrderedDict(
            poolname=getattr(self, '_poolname', 'unknown'),
            poolurl=getattr(self, '_poolurl', 'unknown'),
            _dTypes=self._dTypes,
            _dTags=self._dTags,
        )
