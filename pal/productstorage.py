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

from pal.urn import Urn
from pal.productref import ProductRef
from pal.comparable import Comparable
from .common import getJsonObj

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
        classespath, tagspath = poolpath + '/classes.jsn', poolpath + '/tags.jsn'
        lock = filelock.FileLock(poolpath + '/lock')
        lock.acquire()
        try:
            c = getJsonObj(classespath)
            t = getJsonObj(tagspath)
            if c is None or t is None:
                raise Exception('reading classes and tags')
        except Exception as e:
            logging.error('Error in HK reading')
            raise e
        finally:
            lock.release()
        logging.debug('ProdStorage HK read from ' +
                      str(classespath) + ' ' + str(tagspath))
        return c, t

    def register(self, pool):
        """ Registers the given pools to the storage.
        """

        sp = pool.split('://')
        if sp[0] != 'file':
            raise ValueError(sp[0] + ':// is not supported')
        poolpath = sp[1]
        logging.debug(poolpath)
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
        if pc.exists() and pt.exists():
            c, t = self.readHK(poolpath)
            logging.debug('pool ' + pool + ' HK read')
        else:
            c, t = ODict(), ODict()
        self._pool.update({pool: {'classes': c, 'tags': t}})
        logging.debug('registered pool ' + str(self._pool))
        PoolStorageList.append(pool)

    def writeHK(self, pool):
        """
           save the housekeeping data
        """
        sp = pool.split('://')
        if sp[0] != 'file':
            raise ValueError(sp[0] + ':// is not supported')
        poolpath = sp[1]

        fp0 = Path(poolpath)
        fp = fp0.joinpath('classes.jsn')
        if fp.exists():
            fp.rename(str(fp) + '.old')
        with fp.open(mode="w+") as f:
            js = serializeClassID(self._pool[pool]['classes'])
            f.write(js)

        fp = fp0.joinpath('tags.jsn')
        if fp.exists():
            fp.rename(str(fp) + '.old')
        with fp.open(mode="w+") as f:
            js = serializeClassID(self._pool[pool]['tags'])
            f.write(js)

    def save(self, product, tag=None, pool=None):
        """ Save a product to the storage, possibly under the supplied tag.
        """

        logging.debug('saving ' + str(product) +
                      ' to pool ' + str(pool) + ' with tag ' + str(tag) + ' pools ' + str(self._pool))
        if pool == None:
            if len(self._pool) > 0:
                pool = self.getWritablePool()
            else:
                raise ValueError('no pool registered')
        elif pool not in self._pool:
            self.register(pool)

        c = self._pool[pool]['classes']
        t = self._pool[pool]['tags']
        # save a copy
        cl = c.copy()
        ta = t.copy()

        sp = pool.split('://')
        if sp[0] != 'file':
            raise ValueError(sp[0] + ':// is not supported')
        poolpath = sp[1]
        fp0 = Path(poolpath)
        pn = product.__class__.__qualname__

        lock = filelock.FileLock(poolpath + '/lock')
        lock.acquire()
        if pn in c:
            sn = (c[pn]['currentSN'] + 1)
        else:
            sn = 0
            c[pn] = ODict({'sn2tag': ODict()})
        if tag is not None:
            if tag not in t:
                t[tag] = ODict({pn: []})
        fp = fp0.joinpath(pn + '_' + str(sn))

        try:
            if fp.exists():
                fp.rename(str(fp) + '.old')
            with fp.open(mode="w+") as f:
                js = serializeClassID(product)
                f.write(js)

            c[pn]['currentSN'] = sn
            s2t = c[pn]['sn2tag']
            if sn in s2t:
                s2t[sn].append(tag)
            else:
                s2t[sn] = [tag]

            if tag is not None:
                t[tag][pn].append(sn)

            self.writeHK(pool)
        except IOError as e:
            logging.debug(str(
                fp) + str(e) + ' '.join([x for x in traceback.extract_tb(e.__traceback__).format()]))
            # undo changes
            c = cl
            t = ta
            raise e
        finally:
            lock.release()

        u = Urn(cls=product.__class__, pool=pool, index=sn)
        return ProductRef(urnobj=u)

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
        if prod not in c or sn not in c[prod]['sn2tag']:
            raise ValueError(
                'product %s or index %d not in pool db %s %s.' % (str(prod), sn, c, t))
        # save for rolling back
        cs, ts = c.copy(), t.copy()

        poolpath = pool.split('://')[1]
        sp0 = Path(poolpath)
        sp1 = sp0.joinpath(resource.replace(':', '_'))

        lock = filelock.FileLock(poolpath + '/lock')
        lock.acquire()
        try:
            del c[prod]['sn2tag'][sn]
            if len(c[prod]['sn2tag']) == 0:
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
            logging.debug(msg)
            c = cs
            t = ts
            raise e
        finally:
            lock.release()

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
        return self._pool[uobj.pool]['classes'][uobj.getTypeName()]['sn2tag'][uobj.getIndex()]

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

        lock = filelock.FileLock(poolpath + '/lock')
        lock.acquire()
        try:
            shutil.rmtree(poolpath)
            pp = Path(poolpath)
            pp.mkdir()
        except Exception as e:
            msg = 'remove-mkdir ' + poolpath + ' failed'
            logging.error(msg)
            raise e
        finally:
            lock.release()
        self._pool[pool]['classes'] = ODict()
        self._pool[pool]['tags'] = ODict()

    def __repr__(self):
        return self.__class__.__name__ + ' { pool= ' + str(self._pool) + ' }'
