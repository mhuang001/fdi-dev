# -*- coding: utf-8 -*-

from . import productref
from .poolmanager import PoolManager
from .productpool import ProductPool
from .managedpool import makeLockpath
from .urn import Urn
from ..dataset.odict import ODict

import filelock
import copy
from weakref import finalize

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class ProductStorage(object):
    """ Logical store created from a pool or a poolURL.

    Every instanciation with the same pool will  result in a new instance of ProdStorage.

    """

    def __init__(self, pool=None, poolurl=None, poolmanager=None,
                 **kwds):
        """ Gets the storage "control pannel" for pool with specifed name.

        `auth` with `client`, can be given here to be passed to `PoolManager.getPool`.
        `client` how to call remote api if poolurl indicates a remote pool. Default is `None` for using the configured host/port/credentials. If doing a mocked server test, this needs to be set.
        :pool: can be given as the only pramemter. If `auth` and `client` are given they will substitute those of  `pool`. If `pool` is not given, those will need to be given.
        :poolname: if is a string will be taken as a poolname. if is a pool object will be registered with its name,
        :poolurl: is sent to the PoolManager with poolname to get the pool object.

        """
        if issubclass(pool.__class__, str) and ':' in pool:
            raise TypeError(
                'First argument must be a poolname or a pool object, not ' + str(pool))
        super(ProductStorage, self).__init__()

        if poolmanager:
            # poolservers have their own PoolManagers
            self.PM = poolmanager
        else:
            from .poolmanager import PoolManager
            self.PM = PoolManager

        self._pools = ODict()  # dict of poolname - poolobj pairs
        self.register(pool=pool, poolurl=poolurl, **kwds)

    def register(self,  poolname=None, poolurl=None, pool=None,
                 **kwds):
        """ Registers the given pools to the storage.

        :client: passed to `PoolManager.getPool`.
        :auth: passed to `PoolManager.getPool`.
        """

        if issubclass(pool.__class__, str) and poolname is None:
            pool, poolname = poolname, pool
        with filelock.FileLock(makeLockpath('ProdStorage', 'w')), \
                filelock.FileLock(makeLockpath('ProdStorage', 'r')):
            if pool and issubclass(pool.__class__, ProductPool):
                _p = self.PM.getPool(pool=pool, **kwds)
                from fdi.pal.publicclientpool import PublicClientPool
                if issubclass(pool.__class__, PublicClientPool):
                    pe = _p.poolExists()
                    if not pe:
                        __import__("pdb").set_trace()
            elif poolurl is None and poolname is None:
                # quietly return for no-arg construction case
                return
            else:
                if poolname is not None and not issubclass(poolname.__class__, str):
                    raise TypeError('Poolname must be a string, not ' +
                                    poolname.__class__.__name__)
                if poolurl is not None and not issubclass(poolurl.__class__, str):
                    raise TypeError('Poolurl must be a string, not ' +
                                    poolurl.__class__.__name__)
                _p = self.PM.getPool(
                    poolname=poolname, poolurl=poolurl, **kwds)
                #########
                if 0:
                    cr = _p.client.get(
                        f'http://123.56.102.90:31702/csdb/v1/pool/info?storagePoolName={_p._poolname}', headers={'User-Agent': 'python-requests/2.26.0', 'Accept-Encoding': 'gzip, deflate', 'Accept': '*/*', 'Connection': 'keep-alive', 'X-AUTH-TOKEN': 'eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJtaCIsInVzZXJJZCI6IjM2MzEiLCJuYW1lIjoiTWFvaGFpSHVhbmciLCJleHAiOjE2Nzc3MzE2MTJ9.UChjZJsnzfHXJeeVUVNxShL7zssejkR17LcOZXwOK6auHNIOXTbhc_pKUEpvJ_h2m5H3UOVAwVKTcQWI9kw-9ul-5YduG5yv9HaqzA0s7fxISbIjFL3vR6hHP4wU7xWtwAy8RwGNL6XqcplxexZ1FWDNawijqVVWfKId_JeWkGA'}).text
                    _ = _p.log()
                    if _:
                        logger.info(_)
                    if not cr[8] == '0':
                        __import__("pdb").set_trace()
                    else:
                        logger.info(f'Pool {_p.poolname} exists.')

            self._pools[_p._poolname] = _p

        logger.debug('registered pool %s -> %s.' %
                     (str(_p), str(self._pools)))

    def unregister(self, pool=None, ignore_error=False, **kwds):
        """ Unregisters the given pools to the storage.

        In the process the pool is also unregistered from the `PoolManager`.
        """

        with filelock.FileLock(makeLockpath('ProdStorage', 'w')):
            if issubclass(pool.__class__, ProductPool):
                poolname = pool.getId()
            else:
                poolname = pool
            if self.PM.isLoaded(poolname):
                # remove from pool manager
                # TODO i dentify self
                res = self.PM.remove(poolname, ignore_error=ignore_error)
                # do this after del above
                del self._pools[poolname]
                logger.debug('unregistered pool %s -> %s.' %
                             (str(pool), str(self._pools)))
            else:
                logger.info('Pool %s is not registered.' % poolname)
        return

    def unregisterAll(self, ignore_error=False):
        self.PM.removeAll(ignore_error=ignore_error)
        self._pools.clear()

    def load(self, urnortag):
        """ Loads a product with a URN or a list of products with a tag, from the (writeable) pool.

        It always creates new ProductRefs.
        :return: productref if there is only one. A ```list``` of ```ProductRefs```.
        urnortag: urn or tag
        """
        poolname = self.getWritablePool()

        def runner(urnortag):
            if issubclass(urnortag.__class__, list):
                ulist = list(map(runner, urnortag))
                return ulist
            else:
                if issubclass(urnortag.__class__, str):
                    if len(urnortag) > 3 and urnortag[0:4].lower() == 'urn:':
                        urns = urnortag
                    else:
                        urns = self.getUrnFromTag(urnortag)
                        ret = []
                        for x in urns:
                            pr = productref.ProductRef(
                                urn=x, poolname=poolname)
                            ret.append(pr)
                        return ret
                elif issubclass(urnortag.__class__, Urn):
                    urns = urnortag.urn
                else:
                    raise ValueError(
                        'must provide urn, urnobj, tags, or lists of them')
                return productref.ProductRef(urn=urns, poolname=poolname)
        ls = runner(urnortag=urnortag)
        # return a list only when more than one refs
        return ls  # if len(ls) > 1 else ls[0]

    def save(self, product, tag=None, poolname=None, geturnobjs=False, asyn=False, **kwds):
        """ saves to the writable pool if it has been registered.

        Parameters
        ----------
        product : BaseProduct, list
            Product or a list of them or '[ size1, prd, size2, prd2, ...]'.
        tag : str, list
            If given a tag, all products will be having this tag.
        If a list tags are given to every one product then the
        number of tags must not be the same to that of `product`. If
        they are equal, each tag is goven to the product at the same
        index in the `product` list.
        serialize_out : bool
            if `True` returns contents in serialized form.
        serialize_in : bool
            If set, product input is serialized.
        poolName: str
            If the named pool is not registered, registers and saves.
        geturnobjs : bool
            returns UrnObjs if geturnobjs is True.
        kwds: options passed to json.dump() for subclasses.

        Returns
        -------
        ProductRef: Product reference.
        Urn: If `geturnobjs` is set.
        str: If `serialze_out` is set, serialized form of `ProductRef` or `URN`.
        list: `list` of the above of input is a list.
        """

        if poolname is None:
            if len(self._pools) > 0:
                poolname = self.getWritablePool()
            else:
                raise ValueError('no pool registered')
        elif poolname not in self._pools:
            self.register(poolname)

        if logger.getEffectiveLevel() <= logging.DEBUG:
            desc = [x.description[-6:] for x in product] if issubclass(
                product.__class__, list) else product.description[-6:]
            logger.debug('saving product:' + str(desc) +
                         ' to pool ' + str(poolname) + ' with tag ' + str(tag))

        try:
            ret = self._pools[poolname].saveProduct(
                product, tag=tag, geturnobjs=geturnobjs,
                asyn=asyn, **kwds)
        except Exception as e:
            logger.error('unable to save to the writable pool.')
            raise
        from fdi.pal.productref import ProductRef
        if issubclass(ret.__class__, list):
            if ret and issubclass(ret[0].__class__, ProductRef):
                for r in ret:
                    r.setStorage(self)
        return ret

    def remove(self, urn, datatype=None, index=None, ignore_error=False):
        """ removes product of urn from the writeable pool
        """
        poolname = self.getWritablePool()
        logger.debug('removing product:' + str(urn) +
                     ' from pool ' + str(poolname))
        try:
            pool = self._pools[poolname]
            pool.ignore_error_when_delete = ignore_error
            res = pool.remove(urn, resourcetype=datatype, index=index)
            return res
        except Exception as e:
            msg = 'unable to remove from the writable pool.'
            if ignore_error:
                logger.error(msg)
                return None
            else:
                raise

    def accept(self, visitor):
        """ Hook for adding functionality to object
        through visitor pattern."""
        visitor.visit(self)

    def getHead(self, ref):
        """ Returns the latest version of a given product, belonging
        to the first pool where the same track id is found.
        """
        raise NotImplementedError()

    def getPools(self):
        """  Returns the set of ProductPools registered.
        mh: in a list of poolnames
        XXX TODO: getPoolnames
        """
        return list(self._pools.keys())

    def getPool(self, poolname):
        """ returns the pool object from this storage

        Parameters
        ----------
        poolname : str, int
            The poolname or index.

        Returns
        -------
        ProductPool
            The pool object.

        Raises
        ------
        ValueError, IndexError, TypeError
            wrong poolname / index.

        Examples
        --------
        FIXME: Add docs.

        """

        if isinstance(poolname, str):
            if poolname not in self._pools:
                msg = 'pool ' + poolname + ' not found'
                logger.error(msg)
                raise ValueError(msg)
            return self._pools[poolname]
        try:
            return list(self._pools.values())[poolname]
        except (IndexError, TypeError) as e:
            msg = 'pool ' + poolname + ' not found'
            logger.error(msg)
            raise ValueError(msg)

    def getWritablePool(self, obj=False):
        """ returns the poolname of the first pool, which is the only writeable pool.

        :obj: (bool) return the pool objject instead of the name.
        """
        l = list(self._pools.items())

        return l[0][1] if obj else l[0][0]

    def getAllTags(self):
        """ Get all tags defined in the writable pool.
        """
        return self._pools[self.getWritablePool()].getTags()

    def getProductClasses(self, poolname):
        """  Yields all Product classes found in this pool.
        """
        return self._pools[poolname].getProductClasses()

    def getTags(self, urn):
        """  Get the tags belonging to the writable pool that associated to a given URN.
        returns an iterator.
        """
        return self._pools[self.getWritablePool()].getTags(urn)

    def getMeta(self, urn):
        """  Get the metadata belonging to the writable pool that associated to a given URN.
        returns an ODict.
        """
        if not issubclass(urn.__class__, str):
            urn = urn.urn

        return self._pools[self.getWritablePool()].meta(urn)

    def getUrnFromTag(self, tag):
        """ Get the URN belonging to the writable pool that is associated
        to a given tag.
        """

        return self._pools[self.getWritablePool()].getUrn(tag)

    def wipePool(self, ignore_error=False, asyn=False, **kwds):
        """ Clear all data and meta data of the writable pool.

        Keep it registered.
        """

        self.ignore_error_when_delete = ignore_error
        pool = self.getWritablePool(obj=True)
        pool.ignore_error_when_delete = ignore_error
        pool.wipe(
            ignore_error=ignore_error, asyn=asyn, **kwds)

    def isEmpty(self):
        """ Returns whether all pools are empty or there is no pool. """

        return len(self._pools) == 0 or all(p.isEmpty() for p in self._pools.values())

    def select(self, query, variable=None, ptype=None, previous=None):
        """ Returns a list of URNs to products that match the specified query.

        Parameters
        ----------
        query : the query object, or str
            The Query instances or
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
        the set of return eferences to products matching the supplied query.
        """
        ret = []
        if issubclass(previous.__class__, str):
            previous = previous.split(',')
        if issubclass(query.__class__, str) and ptype and variable:
            # search all registered pools
            for poolnm, pool in self._pools.items():
                ret += pool.select(query, variable, ptype, previous)
            return ret

        # search all registered pools
        for poolnm, pool in self._pools.items():
            ret += pool.select(query, previous)
        return ret

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(writablePool=self.getWritablePool())

    def __repr__(self):
        return self.__class__.__name__ + '( pool= ' + str(self._pools if hasattr(self, '_pools') else None) + ' )'
