# -*- coding: utf-8 -*-
import filelock
import os
from pathlib import Path
import collections
import shutil
from urllib.parse import urlparse

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

from .urn import Urn
from .productref import ProductRef
from .comparable import Comparable
from .common import getJsonObj
from .productpool import ProductPool

from dataset.serializable import serializeClassID
from dataset.dataset import TableDataset
from dataset.odict import ODict


class LocalPool(ProductPool):
    """ the pool will save all products in local computer.
    """

    def __init__(self, **kwds):
        """ creates file structure if there isn't one. if there is, read and populate ouse-keeping records
        """
        super().__init__(**kwds)

        p = Path(self._poolpath)
        if not p.exists():
            p.mkdir()
        c, t, u = self.readHK(self._poolpath)
        logger.debug('pool ' + self._poolurn + ' HK read.')

        self._classes.update(c)
        self._tags.update(t)
        self._urns.update(u)

    def readHK(self, poolpath):
        """
        loads and returns the housekeeping data
        """
        with filelock.FileLock(poolpath + '/lock'):
            for hkdata in ['classes', 'tags', 'urn']:
                hk = {}
                fp = fp0.joinpath(hkdata + '.jsn')
                if fp.exists():
                    r = getJsonObj(str(fp))
                    if r is None:
                        msg = 'Error in HK reading ' + str(fp)
                        logging.error(msg)
                        raise Exception(msg)
                else:
                    r = ODict()
                hk[hkdata] = r
        logger.debug('LocalPool HK read from ' + poolpath)
        return hk['classes'], hk['tags'], hk['urns']

    def writeHK(self, fp0, poolpath):
        """
           save the housekeeping data
        """

        for hkdata in ['classes', 'tags', 'urn']:
            fp = fp0.joinpath(hkdata + '.jsn')
            if fp.exists():
                fp.rename(str(fp) + '.old')
            with fp.open(mode="w+") as f:
                #js = serializeClassID(self._pool['file://' + poolpath][hkdata])
                js = serializeClassID(self.__getattribute__('_' + hkdata))                f.write(js)

    def doSaving(self, poolpath, typename, serialnum, data):
        """ do the media-specific saving
        """
        fp0 = Path(poolpath)
        fp = fp0.joinpath(typename + '_' + str(serialnum))
        try:
            if fp.exists():
                fp.rename(str(fp) + '.old')
            with fp.open(mode="w+") as f:
                js = serializeClassID(data)
                f.write(js)

            self.writeHK(fp0, poolpath)
        except IOError as e:
            logger.debug(str(
                fp) + str(e) + ' '.join([x for x in traceback.extract_tb(e.__traceback__).format()]))

    def save(self, product, tag=None, poolurn=None):
        """ saves to the writable pool if it has been registered, if not registers and saves.
        """

        if poolurn == None:
            if len(self._pool) > 0:
                poolurn = self.getWritablePool()
            else:
                raise ValueError('no pool registered')
        elif poolurn not in self._pool:
            self.register(poolurn)

        logger.debug('saving product:' + str(product) +
                     ' to pool ' + str(poolurn) + ' with tag ' + str(tag))

        ret = self._pool[poolurn].saveProduct(product, tag=tag)

        return ret

    def ZZregister(self, pool):
        """ Registers the given pools to the storage.
        """
        # check duplicated case
        # if pool in PoolStorageList:
        #    return

        # check if pool is part of an existing one
        for ex in self._pool:
            lex = ex.split('/')
            lu = pool.split('/')
            ml = min(len(lex), len(lu))
            if lex[:ml] == lu[:ml]:
                raise ValueError(
                    'pool ' + pool + ' and existing ' + ex + ' overlap.')

        self._pool[pool] = ProductPool.getPool(pool)

        logger.debug('registered pool ' + str(self._pool))
        PoolStorageList.append(pool)

    def load(self, urn):
        """ Loads a product from the pool. returns productref.
        """

        # get a nominal urn object. the pool name may be wrong but good enough for making a prod reference
        uobj = Urn(urn=urn) if issubclass(urn.__class__, str) else urn
        return ProductRef(uobj)

    def remove(self, urn):
        """ removes product of urn from the writeable pool
        """
        pool = self.getWritablePool()
        pprop = self._pool[pool]
        sr = urn.rsplit(pool, maxsplit=1)
        if len(sr) < 2:
            raise Exception(
                urn + ' does not contain the writeable pool ' + pool)
        resource = sr[1].lstrip(':')
        sr1 = resource.split(':')
        prod = sr1[0]
        sn = int(sr1[1])
        c, t = pprop['classes'], pprop['tags']
        if prod not in c or sn not in c[prod]['sn']:
            raise ValueError(
                'product %s or index %d not in pool db %s %s.' % (str(prod), sn, c, t))
        # save for rolling back
        cs, ts = c.copy(), t.copy()

        poolpath = pool.split('://')[1]
        sp0 = Path(poolpath)
        sp1 = sp0.joinpath(resource.replace(':', '_'))

        with filelock.FileLock(poolpath + '/lock'):
            try:
                del c[prod]['sn'][sn]
                if len(c[prod]['sn']) == 0:
                    del c[prod]
                if prod in t:
                    if sn in t[prod]:
                        t[prod].remove(sn)
                        if len(t[prod]) == 0:
                            del t[prod]

                sp1.unlink()
                self.writeHK(pool)
            except Exception as e:
                msg = 'product ' + urn + ' removal failed'
                logger.debug(msg)
                c = cs
                t = ts
                raise e

    def accept(self, visitor):
        """ Hook for adding functionality to object
        through visitor pattern."""
        visitor.visit(self)

    def getHead(self, ref):
        """ Returns the latest version of a given product, belonging
        to the first pool where the same track id is found.
        """

    def ZZgetPools(self):
        """  Returns the set of ProductPools registered.
        mh: in a list of (pool, {'classes','tags'})
        """
        return list(self._pool.keys())

    def ZZgetPool(self, pool):
        """ mh: returns  {'classes','tags'}
        """
        if pool not in self._pool:
            raise ValueError('pool ' + pool + ' not found')
        return self._pool[pool]

    def ZZgetWritablePool(self):
        return self.getPools()[0]

    def ZZgetAllTags(self):
        """ Get all tags defined in the writable pool.
        """
        return self._pool[self.getWritablePool()]['tags'].keys()

    def ZZgetProductClasses(self, pool):
        """  Yields all Product classes found in this pool.
        """
        return self._pool[pool].getProductClasses()

    def getTags(self, urn):
        """  Get the tags belonging to the writable pool that associated to a given URN.
        returns an iterator.
        """
        return self.getWritablePool().getTags(urn)

    def getMeta(self, urn):
        """  Get the metadata belonging to the writable pool that associated to a given URN.
        returns a dict.
        """
        if issubclass(urn.__class__, str):
            uobj = Urn(urn=urn)
        else:
            uobj = urn
        return self._pool[uobj.pool]['classes'][uobj.getTypeName()]['sn'][uobj.getIndex()]['meta']

    def getUrnFromTag(self, tag):
        """ Get the URN belonging to the writable pool that is associated
        to a given tag.
        """
        pool = self.getWritablePool()
        poolurn = 'urn:' + pool + ':'
        u = []
        for (p, lsn) in self._pool[pool]['tags'][tag].items():
            for sn in lsn:
                u.append(poolurn + p + ':' + str(sn))
        print(u)
        return u

    def wipePool(self, pool):
        """
        """
        if pool not in self._pool:
            raise ValueError('pool ' + pool + ' not found')
        sp = pool.split('://')
        if sp[0] != 'file':
            raise ValueError(sp[0] + ':// is not supported')
        poolpath = sp[1]

        with filelock.FileLock(poolpath + '/lock'):
            try:
                shutil.rmtree(poolpath)
                pp = Path(poolpath)
                pp.mkdir()
            except Exception as e:
                msg = 'remove-mkdir ' + poolpath + ' failed'
                logger.error(msg)
                raise e
        self._pool[pool]['classes'] = ODict()
        self._pool[pool]['tags'] = ODict()

    def __repr__(self):
        return self.__class__.__name__ + ' { pool= ' + str(self._pool) + ' }'
