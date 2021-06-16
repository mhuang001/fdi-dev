# -*- coding: utf-8 -*-
from ..dataset.odict import ODict
from ..dataset.classes import Classes
from ..dataset.product import Product
from ..dataset.serializable import serialize
from ..dataset.deserialize import deserialize
from .urn import Urn, parseUrn, parse_poolurl, makeUrn
from .versionable import Versionable
from .taggable import Taggable
from .dicthk import DictHk
from .definable import Definable
from ..utils.common import pathjoin, fullname, lls
from .productref import ProductRef
from .query import AbstractQuery, MetaQuery, StorageQuery

import logging
import filelock
import getpass
import os
import sys
import builtins
from collections import OrderedDict, ChainMap
from functools import lru_cache

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    from urllib.parse import urlparse
else:
    PY3 = False
    from urlparse import urlparse

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

Class_Look_Up = ChainMap(Classes.mapping, globals(), vars(builtins))


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

    if 1:
        return lp+'.read' if op == 'r' else lp+'.write'
    else:
        if not os.path.exists(lp):
            os.makedirs(lp)
            lf = pathjoin(lp, 'lock')
        return lf+'.read' if op == 'r' else lf+'.write'


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
        super(ProductPool, self).__init__(**kwds)

        self.setPoolname(poolname)
        self.setPoolurl(poolurl)
        # self._pathurl = pr.netloc + pr.path
        # self._pathurl = None

    class ParameetersIncommpleteError(Exception):
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
        self._poolpath, self._scheme, self._place, self._poolname = \
            parse_poolurl(poolurl)
        self._poolurl = poolurl
        # call setup only if poolurl was None
        if s:
            self.setup()

    def accept(self, visitor):
        """ Hook for adding functionality to object
        through visitor pattern."""
        visitor.visit(self)

    def dereference(self, ref):
        """
        Decrement the reference count of a ProductRef.
        """

        raise(NotImplementedError)

    def exists(self, urn):
        """
        Determines the existence of a product with specified URN.
        """

        raise(NotImplementedError)

    def getDefinition(self):
        """
        Returns pool definition info which contains pool type and other pool specific configuration parameters
        """
        return super(ProductPool, self).getDefinition()

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
        raise(NotImplementedError)

    def getReferenceCount(self, ref):
        """
        Returns the reference count of a ProductRef.
        """
        raise(NotImplementedError)

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

        raise(NotImplementedError)

    def schematicSave(self, products, tag=None, geturnobjs=False, serialize_in=True, serialize_out=False, **kwds):
        """ to be implemented by subclasses to do the scheme-specific saving
        """
        raise(NotImplementedError)

    def saveProduct(self, product, tag=None, geturnobjs=False, serialize_in=True, serialize_out=False, **kwds):
        """
        Saves specified product and returns the designated ProductRefs or URNs.
        Saves a product or a list of products to the pool, possibly under the
        supplied tag, and return the reference (or a list of references is
        the input is a list of products), or Urns if geturnobjs is True.

        See pal document for pool structure.

        serialize_out: if True returns contents in serialized form.
        """

        res = self.schematicSave(product, tag=tag,
                                 geturnobjs=geturnobjs, serialize_in=serialize_in, serialize_out=serialize_out, **kwds)
        return res

    def loadDescriptors(self, urn):
        """
        Loads the descriptors belonging to specified URN.
        """

        raise(NotImplementedError)

    def schematicLoad(self, resourcetype, index, serialize_out=False):
        """ to be implemented by subclasses to do the scheme-specific loading
        """
        raise(NotImplementedError)

    def loadProduct(self, urn, serialize_out=False):
        """
        Loads a Product belonging to specified URN.

        serialize_out: if True returns contents in serialized form.
        """
        poolname, resource, index = parseUrn(urn)
        if poolname != self._poolname:
            raise(ValueError('wrong pool: ' + poolname +
                             ' . This is ' + self._poolname))
        ret = self.schematicLoad(
            resourcetype=resource, index=index, serialize_out=serialize_out)
        return ret

    def meta(self,  urn):
        """
        Loads the meta-data belonging to the product of specified URN.
        """

        raise(NotImplementedError)

    def getCount(self, typename):
        """
        Return the number of URNs for the product type.
        """

        raise(NotImplementedError)

    def reference(self, ref):
        """
        Increment the reference count of a ProductRef.
        """

        raise(NotImplementedError)

    def schematicRemove(self, urn=None, resourcetype=None, index=None):
        """ to be implemented by subclasses to do the scheme-specific removing
        """
        raise(NotImplementedError)

    def remove(self, urn):
        """
        Removes a Product belonging to specified URN.
        """
        poolname, resource, index = parseUrn(urn)

        if self._poolname != poolname:
            raise ValueError(
                urn + ' is not from the pool ' + self._poolname)

        res = self.schematicRemove(urn, resourcetype=resource, index=index)
        return res

    def schematicWipe(self):
        """ to be implemented by subclasses to do the scheme-specific wiping.
        """
        raise(NotImplementedError)

    def removeAll(self):
        """
        Remove all pool data (self, products) and all pool meta data (self, descriptors, indices, etc.).
        """

        self.schematicWipe()

    def saveDescriptors(self,  urn,  desc):
        """
        Save/Update descriptors in pool.
        """
        raise(NotImplementedError)

    def schematicSelect(self,  query, results=None):
        """
        to be implemented by subclasses to do the scheme-specific querying.
        """
        raise(NotImplementedError)

    def select(self,  query, variable='m', ptype=Product,
               results=None):
        """
        Returns a list of references to products that match the specified query.
        """
        if issubclass(query.__class__, StorageQuery):
            res = self.schematicSelect(query, results)
        elif variable == 'm':
            res = self.schematicSelect(MetaQuery(ptype, where=query), results)
        else:
            res = self.schematicSelect(AbstractQuery(
                ptype, where=query, variable=variable), results)
        return res

    def __repr__(self):

        co = ', '.join(str(k)+'=' + (v if issubclass(v.__class__, str) else '<' +
                                     v.__class__.__name__+'>') for k, v in self.__getstate__().items())
        return '<'+self.__class__.__name__ + ' ' + co + '>'

    def __getstate__(self):
        """ returns an odict that has all state info of this object.
        Subclasses should override this function.
        """
        return OrderedDict(
            poolurl=self._poolurl if hasattr(self, '_poolurl') else None,
        )

###########################


class ManagedPool(ProductPool, DictHk):
    """ A ProductPool that manages its internal house keeping. """

    def __init__(self, **kwds):
        super(ManagedPool, self).__init__(**kwds)
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
        self._classes = ODict()
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

    @ lru_cache(maxsize=5)
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

    def dereference(self, ref):
        """
        Decrement the reference count of a ProductRef.
        """

        self._urns[ref.urn]['refcnt'] -= 1

    def exists(self, urn):
        """
        Determines the existence of a product with specified URN.
        """
        return urn in self._urns

    def getProductClasses(self):
        """
        Returns all Product classes found in this pool.
        mh: returns an iterator.
        """
        return self._classes.keys()

    def getCount(self, typename):
        """
        Return the number of URNs for the product type.
        """
        try:
            return len(self._classes[typename]['sn'])
        except KeyError:
            return 0

    def doSave(self, resourcetype, index, data, tag=None, serialize_in=True, **kwds):
        """ to be implemented by subclasses to do the action of saving
        """
        raise(NotImplementedError)

    def getReferenceCount(self, ref):
        """
        Returns the reference count of a ProductRef.
        """
        return self._urns[ref.urn]['refcnt']

    def isEmpty(self):
        """
        Determines if the pool is empty.
        """
        return len(self._urns) == 0

    def loadDescriptors(self, urn):
        """
        Loads the descriptors belonging to specified URN.
        """
        return self._urns[urn]

    def meta(self,  urn):
        """
        Loads the meta-data belonging to the product of specified URN.
        """
        return self._urns[urn]['meta']

    def reference(self, ref):
        """
        Increment the reference count of a ProductRef.
        """
        self._urns[ref.urn]['refcnt'] += 1

    def saveOne(self, prd, tag, geturnobjs, serialize_in, serialize_out, res, kwds):
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

            # get the latest HK
            self._classes, self._tags, self._urns = tuple(
                self.readHK().values())
            c, t, u = self._classes, self._tags, self._urns

            if pn in c:
                sn = (c[pn]['currentSN'] + 1)
            else:
                sn = 0
                c[pn] = ODict(sn=[])

            c[pn]['currentSN'] = sn
            c[pn]['sn'].append(sn)

            urn = makeUrn(poolname=self._poolname, typename=pn, index=sn)

            if urn not in u:
                if serialize_in and hasattr(prd, 'meta'):
                    mt = prd.meta
                else:
                    strs, stre = '{"meta": ', '"_STID": "MetaData"}'
                    start = prd.find(strs, 0)
                    end = prd.find(stre, start)
                    if start >= 0 and end > 0:
                        mt = deserialize(prd[start+len(strs):end+len(stre)])
                    else:
                        mt = ODict()
                u[urn] = ODict(tags=[], meta=mt)

            if tag is not None:
                self.setTag(tag, urn)
            try:
                # save prod and HK
                self.doSave(resourcetype=pn,
                            index=sn,
                            data=prd,
                            tag=tag,
                            serialize_in=serialize_in,
                            serialize_out=serialize_out,
                            **kwds)
            except Exception as e:
                msg = 'product ' + urn + ' saving failed.'
                self._classes, self._tags, self._urns = tuple(
                    self.readHK().values())
                logger.debug(msg)
                raise e

        if geturnobjs:
            if serialize_out:
                # return the URN string.
                res.append(urn)
            else:
                res.append(Urn(urn, poolurl=self._poolurl))
        else:
            rf = ProductRef(urn=Urn(urn, poolurl=self._poolurl))
            if serialize_out:
                # return without meta
                res.append(rf)
            else:
                # it seems that there is no better way to set meta
                rf._meta = prd.getMeta()
                res.append(rf)

    def schematicSave(self, products, tag=None, geturnobjs=False, serialize_in=True, serialize_out=False, **kwds):
        """ do the scheme-specific saving """
        res = []

        if serialize_in:
            alist = issubclass(products.__class__, list)
            if not alist:
                prd = products
                self.saveOne(prd, tag, geturnobjs,
                             serialize_in, serialize_out, res, kwds)
            else:
                for prd in products:
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

    def doLoad(self, resourcetype, index, serialize_out=False):
        """ to be implemented by subclasses to do the action of loading
        """
        raise(NotImplementedError)

    def schematicLoad(self, resourcetype, index, serialize_out=False):
        """ do the scheme-specific loading
        """

        with filelock.FileLock(self.lockpath('w')):
            ret = self.doLoad(resourcetype=resourcetype,
                              index=index, serialize_out=serialize_out)
        return ret

    def doRemove(self, resourcetype, index):
        """ to be implemented by subclasses to do the action of reemoving
        """
        raise(NotImplementedError)

    def schematicRemove(self, urn=None, resourcetype=None, index=None):
        """ do the scheme-specific removing
        """

        prod = resourcetype
        sn = index

        with filelock.FileLock(self.lockpath('w')),\
                filelock.FileLock(self.lockpath('r')):

            # get the latest HK
            self._classes, self._tags, self._urns = tuple(
                self.readHK().values())
            c, t, u = self._classes, self._tags, self._urns

            if urn not in u:
                raise ValueError(
                    '%s not found in pool %s.' % (urn, self.getId()))

            self.removeUrn(urn)
            c[prod]['sn'].remove(sn)

            if len(c[prod]['sn']) == 0:
                del c[prod]
            try:
                res = self.doRemove(resourcetype=prod, index=sn)
            except Exception as e:
                msg = 'product ' + urn + ' removal failed'
                logger.debug(msg)
                self._classes, self._tags, self._urns = tuple(
                    self.readHK().values())
                raise e

    def doWipe(self):
        """ to be implemented by subclasses to do the action of wiping.
        """
        raise(NotImplementedError)

    def schematicWipe(self):
        """ do the scheme-specific wiping
        """
        with filelock.FileLock(self.lockpath('w')),\
                filelock.FileLock(self.lockpath('r')):
            try:
                self.doWipe()
                self._classes.clear()
                self._tags.clear()
                self._urns.clear()
            except Exception as e:
                msg = self.getId() + 'wiping failed'
                logger.debug(msg)
                raise e
        logger.debug('Done.')

    def mfilter(self, q, typename=None, reflist=None, urnlist=None, snlist=None):
        """ returns filtered collection using the query.

        q is a MetaQuery
        valid inputs: typename and ns list; productref list; urn list
        """

        ret = []
        u = self._urns
        qw = q.getWhere()

        if reflist:
            if isinstance(qw, str):
                code = compile(qw, 'py', 'eval')
                for ref in reflist:
                    refmet = ref.getMeta()
                    m = refmet if refmet else u[ref.urn]['meta']
                    if eval(code):
                        ret.append(ref)
                return ret
            else:
                for ref in reflist:
                    refmet = ref.getMeta()
                    m = refmet if refmet else u[ref.urn]['meta']
                    if qw(m):
                        ret.append(ref)
                return ret
        elif urnlist:
            if isinstance(qw, str):
                code = compile(qw, 'py', 'eval')
                for urn in urnlist:
                    m = u[urn]['meta']
                    if eval(code):
                        ret.append(ProductRef(urn=urn, meta=m))
                return ret
            else:
                for urn in urnlist:
                    m = u[urn]['meta']
                    if qw(m):
                        ret.append(ProductRef(urn=urn, meta=m))
                return ret
        elif snlist:
            if isinstance(qw, str):
                code = compile(qw, 'py', 'eval')
                for n in snlist:
                    urn = makeUrn(poolname=self._poolname,
                                  typename=typename, index=n)
                    m = u[urn]['meta']
                    if eval(code):
                        ret.append(ProductRef(urn=urn, meta=m))
                return ret
            else:
                for n in snlist:
                    urn = makeUrn(poolname=self._poolname,
                                  typename=typename, index=n)
                    m = u[urn]['meta']
                    if qw(m):
                        ret.append(ProductRef(urn=urn, meta=m))
                return ret
        else:
            raise('Must give a list of ProductRef or urn or sn')

    def pfilter(self, q, cls=None, reflist=None, urnlist=None, snlist=None):
        """ returns filtered collection using the query.

        q: an AbstractQuery.
        valid inputs: cls and ns list; productref list; urn list
        """

        ret = []
        glbs = globals()
        u = self._urns
        qw = q.getWhere()
        var = q.getVariable()
        if var in glbs:
            savevar = glbs[var]
        else:
            savevar = 'not in glbs'

        if reflist:
            if isinstance(qw, str):
                code = compile(qw, 'py', 'eval')
                for ref in reflist:
                    glbs[var] = pref.getProduct()
                    if eval(code):
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
                code = compile(qw, 'py', 'eval')
                for urn in urnlist:
                    pref = ProductRef(urn=urn)
                    glbs[var] = pref.getProduct()
                    if eval(code):
                        ret.append(pref)
                if savevar != 'not in glbs':
                    glbs[var] = savevar
                return ret
            else:
                for urn in urnlist:
                    pref = ProductRef(urn=urn)
                    glbs[var] = pref.getProduct()
                    if qw(glbs[var]):
                        ret.append(pref)
                if savevar != 'not in glbs':
                    glbs[var] = savevar
                return ret
        elif snlist:
            if isinstance(qw, str):
                code = compile(qw, 'py', 'eval')
                for n in snlist:
                    urno = Urn(cls=cls, poolname=self._poolname, index=n)
                    pref = ProductRef(urn=urno)
                    glbs[var] = pref.getProduct()
                    if eval(code):
                        ret.append(pref)
                if savevar != 'not in glbs':
                    glbs[var] = savevar
                return ret
            else:
                for n in snlist:
                    urno = Urn(cls=cls, poolname=self._poolname, index=n)
                    pref = ProductRef(urn=urno)
                    glbs[var] = pref.getProduct()
                    if qw(glbs[var]):
                        ret.append(pref)
                if savevar != 'not in glbs':
                    glbs[var] = savevar
                return ret
        else:
            raise('Must give a list of ProductRef or urn or sn')

    def doSelect(self, query, results=None):
        """
        to be implemented by subclasses to do the action of querying.
        """
        raise(NotImplementedError)

    def schematicSelect(self,  query, results=None):
        """
        do the scheme-specific querying.
        """
        isMQ = issubclass(query.__class__, MetaQuery)
        isAQ = issubclass(query.__class__, AbstractQuery)
        if not isMQ and not isAQ:
            raise TypeError('not a Query')
        lgb = Classes.mapping
        t, v, w, a = query.getType(), query.getVariable(
        ), query.getWhere(), query.retrieveAllVersions()
        ret = []
        if results:
            this = (x for x in results if x.urnobj.getPoolId()
                    == self._poolname)
            if isMQ:
                ret += self.mfilter(q=query, reflist=this)
            else:
                ret += self.pfilter(q=query, reflist=this)
        else:
            for cname in self._classes:
                cls = lgb[cname.split('.')[-1]]
                if issubclass(cls, t):
                    if isMQ:
                        ret += self.mfilter(q=query, typename=cname,
                                            snlist=self._classes[cname]['sn'])
                    else:
                        ret += self.pfilter(q=query, cls=cls,
                                            snlist=self._classes[cname]['sn'])

        return ret

    def __getstate__(self):
        """ returns an odict that has all state info of this object.
        Subclasses should override this function.
        """
        return OrderedDict(
            poolname=self._poolname,
            poolurl=self._poolurl,
            _classes=self._classes,
            _urns=self._urns,
            _tags=self._tags,
        )
