# -*- coding: utf-8 -*-
from ..dataset.odict import ODict
from ..dataset.serializable import serialize
from ..dataset.classes import Classes
from .urn import Urn, parseUrn, parse_poolurl
from .versionable import Versionable
from .taggable import Taggable
from .definable import Definable
from ..utils.common import pathjoin, fullname
from .productref import ProductRef
from .query import AbstractQuery, MetaQuery

import logging
import filelock
from copy import deepcopy
import os
import sys
from functools import lru_cache

import pdb

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    from urllib.parse import urlparse
else:
    PY3 = False
    from urlparse import urlparse

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


lockpathbase = '/tmp/fdi_locks'  # + getpass.getuser()
# lock time-out
locktout = 10


class ProductPool(Definable, Taggable, Versionable):
    """ A mechanism that can store and retrieve Products.

A product pool should not be used directly by users. The general user should access data in a ProductPool through a ProductStorage instance.

When implementing a ProductPool, the following rules need to be applied:

    1. Pools must guarantee that a Product saved via the pool saveProduct(Product) method is stored persistently, and that method returns a unique identifier (URN). If it is not possible to save a Product, an IOException shall be raised.
    2. A saved Product can be retrieved using the loadProduct(Urn) method, using as the argument the same URN that assigned to that Product in the earlier saveProduct(Product) call. No other Product shall be retrievable by that same URN. If this is not possible, an IOException or GeneralSecurityException is raised.
    3. Pools should not implement functionality currently implemented in the core package. Specifically, it should not address functionality provided in the Context abstract class, and it should not implement versioning/cloning support.

    """

    def __init__(self, poolname=None, poolurl=None, **kwds):
        """
        Creates and initializes a productpool.

        * poolname: if provided will override that in poolurl.
        * poolurl: needed to initialize.

        """
        super(ProductPool, self).__init__(**kwds)

        self._poolname = poolname

        self._poolpath, self._scheme, self._place, nm = \
            parse_poolurl(poolurl)
        self._poolurl = poolurl
        # self._pathurl = pr.netloc + pr.path
        # self._pathurl = None
        # {type|classname -> {'sn:[sn]'}}
        self._classes = ODict()

    def lockpath(self, op='w'):
        """ returns the appropriate path.

        creats the path if non-existing. Set lockpath-base permission to all-modify so other fdi users can use.
        op: 'r' for readlock no-reading) 'w' for writelock (no-writing)
        """
        if not os.path.exists(lockpathbase):
            os.makedirs(lockpathbase, mode=0o777)

        #from .httppool import HttpPool
        #from .httpclientpool import HttpClientPool

        p = self.transformpath(self._poolname)
        lp = pathjoin(lockpathbase, p.replace('/', '_'))

        if 1:
            return lp+'.read' if op == 'r' else lp+'.write'
        else:
            if not os.path.exists(lp):
                os.makedirs(lp)
                lf = pathjoin(lp, 'lock')
            return lf+'.read' if op == 'r' else lf+'.write'

    @lru_cache(maxsize=5)
    def transformpath(self, path):
        """ override this to changes the output from the input one (default) to something else.

        """
        base = self._poolpath
        if base != '':
            if path[0] == '/':
                path = base + path
            else:
                path = base + '/' + path
        return path

    def accept(self, visitor):
        """ Hook for adding functionality to object
        through visitor pattern."""
        visitor.visit(self)

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
        return self._classes.keys()

    def getReferenceCount(self, ref):
        """
        Returns the reference count of a ProductRef.
        """
        return self._urns[ref.urn]['refcnt']

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
        return len(self._urns) == 0

    def loadDescriptors(self, urn):
        """
        Loads the descriptors belonging to specified URN.
        """
        return self._urns[urn]

    def schematicLoadProduct(self, resourcetype, index, serialized):
        """ to be implemented by subclasses to do the scheme-specific loading
        """
        raise(NotImplementedError)

    def loadProduct(self, urn, serialized=False):
        """
        Loads a Product belonging to specified URN.

        serialized: if True returns contents in serialized form.
        """
        poolname, resource, index = parseUrn(urn)
        if poolname != self._poolname:
            raise(ValueError('wrong pool: ' + poolname +
                             ' . This is ' + self._poolname))

        with filelock.FileLock(self.lockpath('w')):
            ret = self.schematicLoadProduct(
                resource, index, serialized=serialized)
        return ret

    def meta(self,  urn):
        """
        Loads the meta-data belonging to the product of specified URN.
        """
        return self._urns[urn]['meta']

    def reference(self,  ref):
        """
        Increment the reference count of a ProductRef.
        """
        self._urns[ref.urn]['refcnt'] += 1

    def schematicRemove(self, resourcetype, index):
        """ to be implemented by subclasses to do the scheme-specific removing
        """
        raise(NotImplementedError)

    def remove(self,  urn):
        """
        Removes a Product belonging to specified URN.
        """

        poolname, resource, index = parseUrn(urn)

        if self._poolname != poolname:
            raise ValueError(
                urn + ' is not from the pool ' + self._poolname)

        prod = resource
        sn = index

        self._classes, self._tags, self._urns = self.readHK()
        c, t, u = self._classes, self._tags, self._urns

        # save a copy for rolling back
        cs, ts, us = deepcopy(c), deepcopy(t), deepcopy(u)

        if urn not in u:
            raise ValueError(
                '%s not found in pool %s.' % (urn, self.getId()))

        with filelock.FileLock(self.lockpath('w')),\
                filelock.FileLock(self.lockpath('r')):
            self.removeUrn(urn)
            c[prod]['sn'].remove(sn)
            if len(c[prod]['sn']) == 0:
                del c[prod]
            try:
                res = self.schematicRemove(resourcetype=prod,
                                           index=sn)
            except Exception as e:
                msg = 'product ' + urn + ' removal failed'
                logger.debug(msg)
                # undo changes
                c, t, u = cs, ts, us
                raise e
        return res

    def removeAll(self):
        """
        Remove all pool data (self, products) and all pool meta data (self, descriptors, indices, etc.).
        """

        with filelock.FileLock(self.lockpath('w')),\
                filelock.FileLock(self.lockpath('r')):
            try:
                self.schematicWipe()
                self._classes.clear()
                self._tags.clear()
                self._urns.clear()
            except Exception as e:
                msg = self.getId() + 'wiping failed'
                logger.debug(msg)
                raise e
        logger.debug('Done.')

    def saveDescriptors(self,  urn,  desc):
        """
        Save/Update descriptors in pool.
        """

    def schematicSave(self, resourcetype, index, data, tag=None):
        """ to be implemented by subclasses to do the scheme-specific saving
        """
        raise(NotImplementedError)

    def saveProduct(self,  product, tag=None, geturnobjs=False, serialized=False):
        """
        Saves specified product and returns the designated ProductRefs or URNs.
        Saves a product or a list of products to the pool, possibly under the
        supplied tag, and return the reference (or a list of references is
        the input is a list of products), or Urns if geturnobjs is True.

        See pal document for pool structure.

        serialized: if True returns contents in serialized form.
        """
        c, t, u = self._classes, self._tags, self._urns
        # save a copy
        cs, ts, us = deepcopy(c), deepcopy(t), deepcopy(u)

        if not issubclass(product.__class__, list):
            prds = [product]
        else:
            prds = product
        res = []
        for prd in prds:
            pn = fullname(prd)
            with filelock.FileLock(self.lockpath('w')),\
                    filelock.FileLock(self.lockpath('r')):
                if pn in c:
                    sn = (c[pn]['currentSN'] + 1)
                else:
                    sn = 0
                    c[pn] = ODict(sn=[])

                c[pn]['currentSN'] = sn
                c[pn]['sn'].append(sn)

                urnobj = Urn(cls=prd.__class__,
                             poolname=self._poolname, index=sn)
                urn = urnobj.urn

                if urn not in u:
                    u[urn] = ODict(tags=[], meta=prd.meta)

                if tag is not None:
                    self.setTag(tag, urn)

                try:
                    self.schematicSave(resourcetype=pn,
                                       index=sn,
                                       data=prd,  tag=tag)
                except Exception as e:
                    msg = 'product ' + urn + ' saving failed'
                    logger.debug(msg)
                    # undo changes
                    c, t, u = cs, ts, us
                    raise e
            if geturnobjs:
                if serialized:
                    res.append(urn)
                else:
                    res.append(urnobj)
            else:
                rf = ProductRef(urn=urnobj)
                # it seems that there is no better way to set meta
                rf._meta = prd.getMeta()
                rf._poolname = self._poolname
                res.append(rf)
        logger.debug('generated ' + 'Urns ' if geturnobjs else 'prodRefs ' +
                     str(len(res)))
        if issubclass(product.__class__, list):
            return serialize(res) if serialized else res
        else:
            return serialize(res[0]) if serialized else res[0]

    def mfilter(self, q, cls=None, reflist=None, urnlist=None, snlist=None):
        """ returns filtered collection using the query.

        q is a MetaQuery
        valid inputs: cls and ns list; productref list; urn list
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
                    urno = Urn(cls=cls, poolname=self._poolname, index=n)
                    m = u[urno.urn]['meta']
                    if eval(code):
                        ret.append(ProductRef(urn=urno, meta=m))
                return ret
            else:
                for n in snlist:
                    urno = Urn(cls=cls, poolname=self._poolname, index=n)
                    m = u[urno.urn]['meta']
                    if qw(m):
                        ret.append(ProductRef(urn=urno, meta=m))
                return ret
        else:
            raise('Must give a list of ProductRef or urn or sn')

    def pfilter(self, q, cls=None, reflist=None, urnlist=None, snlist=None):
        """ returns filtered collection using the query.

        q is a AbstractQuery.
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

    def select(self,  query, results=None):
        """
        Returns a list of references to products that match the specified query.
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
                        ret += self.mfilter(q=query, cls=cls,
                                            snlist=self._classes[cname]['sn'])
                    else:
                        ret += self.pfilter(q=query, cls=cls,
                                            snlist=self._classes[cname]['sn'])

        return ret

    def __repr__(self):
        return self.__class__.__name__ + ' { pool= ' + str(self._poolname) + ' }'
