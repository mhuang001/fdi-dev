# -*- coding: utf-8 -*-

from ..utils.getconfig import getConfig
from ..utils.common import lls
from .urn import parse_poolurl
from ..pns.fdi_requests import put_on_server, delete_from_server
from ..pal.productpool import ProductPool

from requests.exceptions import ConnectionError

import getpass
from weakref import WeakValueDictionary, getweakrefcount, finalize, getweakrefs
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

pc = getConfig()

DEFAULT_MEM_POOL = 'defaultmem'
# localpool
DEFAULT_POOL = 'fdi_pool_' + __name__ + getpass.getuser()


def remoteRegister(p, poolurl):
    logger.debug('Register %s on the server', poolurl)
    try:
        res, msg = put_on_server('urn:::0', poolurl, 'pool')
    except ConnectionError as e:
        res, msg = 'FAILED', str(e)
    if res == 'FAILED':
        raise RuntimeError(
            'Registering ' + poolurl + ' failed.  ' + msg)
    return res, msg


def remoteUnregister(poolurl):
    """ this method does not reference pool object. """
    if not poolurl.lower().startswith('http'):
        logger.warning('Ignored: %s not for a remote pool.' % poolurl)
        return 1
    logger.debug('unregister %s on the server', poolurl)
    #url = api_baseurl + post_poolid
    #x = requests.delete(url, auth=HTTPBasicAuth(auth_user, auth_pass))
    #o = deserialize(x.text)
    urn = 'urn:::0'
    try:
        res, msg = delete_from_server(urn, poolurl, 'pool')
    except ConnectionError as e:
        res, msg = 'FAILED', str(e)
    if res == 'FAILED':
        logger.warning('Ignored: Unregisterinf ' +
                       poolurl + ' failed.  ' + msg)
        code = 2
    else:
        code = 0
    return code


class PoolManager(object):
    """
    This class provides the means to reference ProductPool objects without having to hard-code the type of pool. For example, it could be desired to easily switch from one pool type to another.

This is done by calling the getPool() method, which will return an existing pool or create a new one if necessary.
    """
    # Global centralized dict that returns singleton -- the same -- pool for the same ID.
    _GlobalPoolList = WeakValueDictionary()

    # maps scheme to default place/poolpath
    p = pc['node']['host']+':'+str(pc['node']['port'])+pc['baseurl']
    PlacePaths = {
        'file': pc['base_poolpath'],
        'mem': '/',
        'http': p,
        'https': p,
        'server': pc['server_poolpath'],
    }
    del p

    @classmethod
    def getPool(cls, poolname=None, poolurl=None, pool=None, **kwds):
        """ returns an instance of pool according to name or path of the pool.

        Returns the pool object if the pool is registered. Creates the pool if it does not already exist. the same poolname-path always get the same pool. Http pools will be registered on the sserver side.

Pools registered are kept as long as the last reference remains. When the last is gone the pool gets :meth;`removed` d.

        poolname: name of the pool.
        poolurl: if given the poolpath, scheme, place will be derived from it. if not given for making a new pool (i.e. when poolname is not a registered pool name.. 
If poolname is missing it is derived from poolurl; if poolurl is also absent, ValueError will be raised.
        kwds: passed to pool instanciation arg-list.

        """
        # logger.debug('GPL ' + str(id(cls._GlobalPoolList)) +
        #             str(cls._GlobalPoolList) + ' PConf ' + str(cls.PlacePaths))

        if pool:
            if poolname:
                raise ValueError(
                    'Pool name %s and pool object cannot be both given.' % poolname)
            poolname, poolurl, p = pool._poolname, pool._poolurl, pool
            if poolurl.lower().startswith('http'):
                res, msg = remoteRegister(p, poolurl)
        else:
            # find out the poolname first
            if poolname is None:
                if poolurl:
                    # the last segment will be the poolname
                    pp, schm, pl, poolname = parse_poolurl(poolurl)
            if cls.isLoaded(poolname):
                return cls._GlobalPoolList[poolname]

            if poolurl:
                # poolname use the one comes above
                pp, schm, pl, pn = parse_poolurl(poolurl)
            else:
                raise ValueError(
                    'A new pool %s cannot be created without a pool url.' % poolname)
            # now we have scheme, poolname, poolurl
            if schm == 'file':
                from . import localpool
                p = localpool.LocalPool(
                    poolname=poolname, poolurl=poolurl, **kwds)
            elif schm == 'mem':
                from . import mempool
                p = mempool.MemPool(poolname=poolname, poolurl=poolurl, **kwds)
            elif schm == 'server':
                from . import httppool
                p = httppool.HttpPool(
                    poolname=poolname, poolurl=poolurl, **kwds)
            elif schm in ('http', 'https'):
                from . import httpclientpool
                p = httpclientpool.HttpClientPool(
                    poolname=poolname, poolurl=poolurl, **kwds)
                res, msg = remoteRegister(p, poolurl)
            else:
                raise NotImplementedError(schm + ':// is not supported')
        #print(getweakrefs(p), id(p), '////')
        cls.save(poolname, p)
        #print(getweakrefs(p), id(p))

        # Pass poolurl to PoolManager.remove() for remote pools
        # finalize(p, print, poolname, poolurl)
        logger.debug('made pool ' + lls(p, 900))
        return p

    @ classmethod
    def getMap(cls):
        """
        Returns a poolname - poolobject map.
        """
        return cls._GlobalPoolList

    @ classmethod
    def isLoaded(cls, poolname):
        """
        Whether an item with the given id has been loaded (cached).

        returns the number of remaining week references if the pool is loaded.
        """
        if poolname in cls._GlobalPoolList:
            # print(poolname, getweakrefcount(cls._GlobalPoolList[poolname]))
            return getweakrefcount(cls._GlobalPoolList[poolname])
        else:
            return False

    @ classmethod
    def removeAll(cls):
        """ deletes all pools from the pool list, pools unwiped
        """
        nl = list(cls._GlobalPoolList)
        for pool in nl:
            cls.remove(pool)

    @ classmethod
    def save(cls, poolname, poolobj):
        """
        """
        cls._GlobalPoolList[poolname] = poolobj

    @ classmethod
    def remove(cls, poolname):
        """ Remove from list and unregister remote pools.

        returns 0 for successful removal, 1 for poolname not registered so no need, 2 for remove with warning.
        """
        l = cls.isLoaded(poolname)
        # print(getweakrefs(cls._GlobalPoolList[poolname]), id(
        #    cls._GlobalPoolList[poolname]), '......', l)
        if l is False:
            return 1
        code = 0
        if l == 1:
            # this is the only reference. unregister remote first.
            poolurl = cls._GlobalPoolList[poolname]._poolurl
            if poolurl.lower().startswith('http'):
                code = remoteUnregister(poolurl)
        del cls._GlobalPoolList[poolname]
        return code

    @ classmethod
    def getPoolurlMap(cls):
        """
        Gives the default poolurls of PoolManager.
        """
        return cls.PlacePaths

    @ classmethod
    def setPoolurlMap(cls, new):
        """
        Sets the default poolurls of PoolManager.
        """
        cls.PlacePaths.clear()
        cls.PlacePaths.update(new)

    @ classmethod
    def size(cls):
        """
        Gives the number of entries in this manager.
        """
        return len(cls._GlobalPoolList)

    def items(self):
        """
        Returns map's items
        """
        return self._GlobalPoolList.items()

    def __setitem__(self, *args, **kwargs):
        """ sets value at key.
        """
        self._GlobalPoolList.__setitem__(*args, **kwargs)

    def __getitem__(self, *args, **kwargs):
        """ returns value at key.
        """
        return self._GlobalPoolList.__getitem__(*args, **kwargs)

    def __delitem__(self, *args, **kwargs):
        """ removes value and its key.
        """
        self._GlobalPoolList.__delitem__(*args, **kwargs)

    def __len__(self, *args, **kwargs):
        """ size of data
        """
        return self._GlobalPoolList.__len__(*args, **kwargs)

    def __iter__(self, *args, **kwargs):
        """ returns an iterator
        """
        return self._GlobalPoolList.__iter__(*args, **kwargs)

    def __repr__(self):
        return self.__class__.__name__ + '(' + str(self._GlobalPoolList) + ')'
