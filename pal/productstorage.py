# -*- coding: utf-8 -*-
import filelock
from copy import deepcopy
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

from pns.common import getJsonObj
from dataset.serializable import serializeClassID
from dataset.dataset import TableDataset
from dataset.odict import ODict

# Global centralized dict that returns the same ProductStorage+pool.
PoolStorageList = []


class ProductStorage():
    """
    """

    def __init__(self, pool='file:///tmp/pool', **kwds):
        super().__init__(**kwds)
        self._pool = collections.OrderedDict()  # dict of pool-urn keys
        self.register(pool)

    def readHK(self, poolpath):
        """
        loads and returns the housekeeping data
        """
        classespath, tagspath = 'file://' + poolpath + \
            '/classes.jsn', 'file://' + poolpath + '/tags.jsn'
        with filelock.FileLock(poolpath + '/lock'):
            try:
                c = getJsonObj(classespath)
                t = getJsonObj(tagspath)
                print(c)
                print(t)
                if c is None or t is None:
                    raise Exception('reading classes and tags')
            except Exception as e:
                logging.error('Error in HK reading')
                raise e
        logger.debug('ProdStorage HK read from ' +
                     str(classespath) + ' ' + str(tagspath))
        return c, t

    def register(self, pool):
        """ Registers the given pools to the storage.
        """

        sp = pool.split('://')
        if sp[0] != 'file':
            raise ValueError(sp[0] + ':// is not supported')
        poolpath = sp[1]
        logger.debug(poolpath)
        p = Path(poolpath)
        # check duplicated case
        # if pool in PoolStorageList:
        #    return

        # check if pool is part of an existing storage
        for ex in self._pool:
            lex = ex.split('/')
            lu = pool.split('/')
            ml = min(len(lex), len(lu))
            if lex[:ml] == lu[:ml]:
                raise ValueError(
                    'pool ' + pool + ' and existing ' + ex + ' overlap.')

        if not p.exists():
            p.mkdir()
        pc = p.joinpath('classes.jsn')
        pt = p.joinpath('tags.jsn')
        logger.debug(str(pc) + str(pc.exists()))
        logger.debug(str(pt) + str(pt.exists()))
        if pc.exists() and pt.exists():
            c, t = self.readHK(poolpath)
            logger.debug('pool ' + pool + ' HK read')
        else:
            c, t = ODict(), ODict()
        self._pool.update({pool: {'classes': c, 'tags': t}})
        logger.debug('registered pool ' + str(self._pool))
        PoolStorageList.append(pool)

    def writeHK(self, fp0, poolpath):
        """
           save the housekeeping data
        """

        for hkdata in ['classes', 'tags']:
            fp = fp0.joinpath(hkdata + '.jsn')
            if fp.exists():
                fp.rename(str(fp) + '.old')
            with fp.open(mode="w+") as f:
                js = serializeClassID(self._pool['file://' + poolpath][hkdata])
                f.write(js)

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

    def save(self, product, tag=None, pool=None):
        """ Save a product or a list of products to the storage, possibly under the supplied tag, and return the reference (or a list of references if the input is a list of products).
        """

        if pool == None:
            if len(self._pool) > 0:
                pool = self.getWritablePool()
            else:
                raise ValueError('no pool registered')
        elif pool not in self._pool:
            self.register(pool)

        logger.debug('saving product:' + str(product) +
                     ' to pool ' + str(pool) + ' with tag ' + str(tag))

        c = self._pool[pool]['classes']
        t = self._pool[pool]['tags']
        # save a copy
        cl = deepcopy(c)
        ta = deepcopy(t)

        sp = pool.split('://')
        if sp[0] != 'file':
            raise ValueError(sp[0] + ':// is not supported')
        poolpath = sp[1]

        if not issubclass(product.__class__, list):
            prds = [product]
        else:
            prds = product
        rfs = []
        for prd in prds:
            pn = prd.__class__.__qualname__

            with filelock.FileLock(poolpath + '/lock'):
                if pn in c:
                    sn = (c[pn]['currentSN'] + 1)
                else:
                    sn = 0
                    c[pn] = ODict({'sn': ODict()})
                if tag is not None:
                    if tag not in t:
                        t[tag] = ODict({pn: []})

                c[pn]['currentSN'] = sn
                s2t = c[pn]['sn']
                if sn in s2t:
                    s2t[sn]['meta'] = prd.meta
                    s2t[sn]['tags'].append(tag)
                else:
                    s2t[sn] = ODict(meta=prd.meta, tags=[tag])

                if tag is not None:
                    t[tag][pn].append(sn)

                try:
                    self.doSaving(poolpath, typename=pn,
                                  serialnum=sn, data=prd)
                except Exception as e:
                    # undo changes
                    c = cl
                    t = ta
                    raise e
            u = Urn(cls=prd.__class__, pool=pool, index=sn)
            rf = ProductRef(urnobj=u)
            rfs.append(rf)
        if not issubclass(product.__class__, list):
            return rfs[0]
        else:
            return rfs

    def load(self, urn):
        """ Loads a product from the ProductStorage. returns productref.
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
        cs, ts = deepcopy(c), deepcopy(t)

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
                self.writeHK(sp0, poolpath)
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

    def getPools(self):
        """  Returns the set of ProductPools registered.
        mh: in a list of (pool, {'classes','tags'})
        """
        return list(self._pool.keys())

    def getPool(self, pool):
        """ mh: returns  {'classes','tags'}
        """
        if pool not in self._pool:
            raise ValueError('pool ' + pool + ' not found')
        return self._pool[pool]

    def getWritablePool(self):
        return self.getPools()[0]

    def getAllTags(self):
        """ Get all tags defined in the writable pool.
        """
        return self._pool[self.getWritablePool()]['tags'].keys()

    def getProductClasses(self, pool):
        """  Yields all Product classes found in this pool.
        mh: which pool
        """
        return self.getPool(pool)['classes'].keys()

    def getTags(self, urn):
        """  Get the tags belonging to the writable pool that associated to a given URN.
        returns a list.
        """
        uobj = Urn(urn=urn)
        return self._pool[uobj.pool]['classes'][uobj.getTypeName()]['sn'][uobj.getIndex()]['tags']

    def getMeta(self, urn):
        """  Get the metadata belonging to the writable pool that associated to a given URN.
        returns a dict.
        """
        if issubclass(urn.__class__, str):
            uobj = Urn(urn=urn)
        else:
            uobj = urn
        try:
            r = self._pool[uobj.pool]['classes'][uobj.getTypeName(
            )]['sn'][uobj.getIndex()]['meta']
        except KeyError as e:
            msg = 'pool does not have %s . %s' % (uobj.urn, str(e))
            raise ValueError(msg)
        return r

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
