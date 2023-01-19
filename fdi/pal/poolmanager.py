
# -*- coding: utf-8 -*-
import logging
from weakref import WeakValueDictionary, getweakrefcount
import getpass

from ..utils.getconfig import getConfig
from ..utils.common import lls
from .urn import parse_poolurl
from ..pal.httppool import HttpPool

from requests.exceptions import ConnectionError
import requests

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

pc = getConfig()

DEFAULT_MEM_POOL = 'defaultmem'
# localpool
DEFAULT_POOL = 'fdi_pool_' + __name__ + getpass.getuser()
Invalid_Pool_Names = ['pools', 'urn', 'URN', 'api']


def remoteRegister(pool):
    """ if registered a pool's auth and client will be used.

    Note that a new http/csdb pool gets remoteRegistered before locally registered.

    Parameter
    ---------
    pool : HttpClientPool, PublicClientPool
        Pool object to be registered on remote server and have client/session set.
    auth : object
        Authorization object for the client. If given will substitute that of pool, if pool has auth.
    client : flask.requests (testing), or requests.Session
        The client. If given will substitute that of pool, if pool is given

    """
    # pool object
    poolo = None
    from ..pal import httpclientpool, publicclientpool

    if issubclass(pool.__class__, httpclientpool.HttpClientPool):

        # HttpClientPool. Init the remote pool. If exists, load.d
        poolurl = pool._poolurl
        poolo = pool

        logger.debug('Register %s on the server', poolurl)
        if poolurl.endswith('/'):
            poolurl = poolurl[:-1]
        from ..pns.fdi_requests import put_on_server
        try:
            res, msg = put_on_server(
                'urn:::0', poolurl, 'register_pool', auth=poolo.auth, client=poolo.client)
        except ConnectionError as e:
            res, msg = 'FAILED', str(e)
            logger.error(poolurl + ' ' + msg)
            raise
        if res == 'FAILED':
            np = '<' + poolo.auth.username + ' ' + poolo.auth.password + \
                '>' if poolo.auth else '<no authorization>'
            raise RuntimeError(
                'Registering ' + poolurl + ' failed with auth ' + np + ' , ' + msg)
        return res, msg
    elif issubclass(pool.__class__, publicclientpool.PublicClientPool):

        # register csdb pool. If existing, load. IF not exists, create and initialize sn.
        status, poolres = pool.createPool2()

        if status:
            pool.getToken()
            pool.client.headers.update({'X-AUTH-TOKEN': pool.token})
            if poolres['code'] == 1:
                # exists
                pinfo = pool.getPoolInfo()
            res = 'OK'
        elif not status:
            msg = poolres['msg']
            logger.error(
                'Registering ' + poolurl + ' failed with auth ' + 'np' + ' , ' + msg)
            res = 'FAILED'
        return res, poolres['msg']
    else:
        return


def remoteUnregister(poolurl, auth=None, client=None):
    """ this method does not reference pool object. """

    if not poolurl.lower().startswith('http'):
        logger.warning('Ignored: %s not for a remote pool.' % poolurl)
        return 1
    logger.debug('unregister %s on the server', poolurl)

    # check if poolurl has been registered
    for pool, poolo in PoolManager._GlobalPoolList.items():
        if issubclass(poolo.__class__, HttpPool):
            continue
        if poolurl == poolo._poolurl:
            if client is None:
                client = poolo.client
            if auth is None:
                auth = poolo.auth
            break
    else:
        raise NameError(
            f'Remote Unregistering failed. {poolurl} not registered or not suitable.')
    from ..pns.fdi_requests import delete_from_server
    #url = api_baseurl + post_poolid
    #x = requests.delete(url, auth=HTTPBasicAuth(auth_user, auth_pass))
    #o = deserialize(x.text)
    urn = 'urn:::0'
    try:
        res, msg = delete_from_server(
            urn, poolurl, 'unregister_pool', auth=auth, client=client)
    except ConnectionError as e:
        res, msg = 'FAILED', str(e)
    if res == 'FAILED':
        logger.warning('Ignored: Unregistering ' +
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

    _GlobalPoolList = WeakValueDictionary()
    """ Global centralized dict that returns singleton -- the same -- pool for the same ID."""

    # maps scheme to default place/poolpath
    # pc['host']+':'+str(pc['port'])+pc['baseurl']
    p = getConfig('poolurl:').strip('/').split('://')[1]
    PlacePaths = {
        'file': pc['base_local_poolpath'],
        'mem': '/',
        'http': p,
        'https': p,
        'server': pc['server_local_poolpath'],
        'csdb': pc['cloud_api_version']
    }
    del p

    @classmethod
    def getPool(cls, poolname=None, poolurl=None, pool=None, makenew=True, auth=None, client=None, **kwds):
        """ returns an instance of pool according to name or path of the pool.

        Returns the pool object if the pool is registered. Creates the pool if it does not already exist. the same poolname-path always get the same pool. Http pools will be registered on the server side.

Pools registered are kept as long as the last reference remains. When the last is gone the pool gets :meth;`removed` d.

        Parameter
        ---------
        poolname : str
            name of the pool.
        poolurl : str
            If given the poolpath, scheme, place will be derived from it. if not given for making a new pool (i.e. when poolname is not a registered pool name. If poolname is missing it is derived from poolurl; if poolurl is also absent, ValueError will be raised.
        pool: ProductPool
            If `auth` and `client` are given they will substitute those of  `pool`. If `pool` is not given, those will need to be given.
        makenew : bool
            When the pool does not exist, make a new one (````True```; default) or throws `PoolNotFoundError` (```False```).
        auth : str
            For `remoteRegister`.
        client : default is `None`.
            For `remoteRegister`.
        kwds  : dict
            Passed to pool instanciation arg-list.

        Returns
        -------
        ProductPool:
            The pool object.
        """
        # logger.debug('GPL ' + str(id(cls._GlobalPoolList)) +
        #             str(cls._GlobalPoolList) + ' PConf ' + str(cls.PlacePaths))
        if pool:
            if poolname:
                raise ValueError(
                    'Pool name %s and pool object cannot be both given.' % poolname)
            poolname, poolurl = pool._poolname, pool._poolurl
            if cls.isLoaded(poolname):
                return cls._GlobalPoolList[poolname]
            if poolurl.lower()[:4] in ('http', 'csdb'):
                if auth is not None and getattr(pool, 'auth', None) is None:
                    pool.auth = auth
                if client is not None and getattr(pool, 'client', None) is None:
                    from ..httppool.session import requests_retry_session
                    pool.client = requests_retry_session()
                res, msg = remoteRegister(pool)
            p = pool
        else:
            # quick decisions can be made knowing poolname only
            if poolname == DEFAULT_MEM_POOL:
                if not poolurl:
                    poolurl = 'mem:///' + poolname
            if poolname is not None:
                if poolname in Invalid_Pool_Names:
                    raise ValueError(
                        'Cannot register invalid pool name: ' + poolname)
                if cls.isLoaded(poolname):
                    return cls._GlobalPoolList[poolname]

            # get poolname and scheme
            if not poolurl:
                poolurl = getConfig('poolurl:'+poolname)
            if poolurl:
                pp, schm, pl, pn, un, pw = parse_poolurl(poolurl)
            else:
                raise ValueError(
                    'A new pool %s cannot be created without a pool url. Maybe the pool needs to be registered?' % poolname)
            if poolname:
                if pn != poolname:
                    raise ValueError(
                        f'Poolname in poolurl {poolurl} is different from poolname {poolname}.')
            else:
                poolname = pn

            # now we have scheme, poolname, poolurl
            if poolname in Invalid_Pool_Names:
                raise ValueError(
                    'Cannot register invalid pool name: ' + poolname)
            if cls.isLoaded(poolname):
                return cls._GlobalPoolList[poolname]
            if schm == 'file':
                from . import localpool
                p = localpool.LocalPool(
                    poolname=poolname, poolurl=poolurl, makenew=makenew, **kwds)
            elif schm == 'mem':
                from . import mempool
                p = mempool.MemPool(poolname=poolname, poolurl=poolurl, **kwds)
            elif schm == 'server':
                from . import httppool
                p = httppool.HttpPool(
                    poolname=poolname, poolurl=poolurl, **kwds)
            elif schm in ('http', 'https', 'csdb'):
                if schm == 'csdb':
                    from . import publicclientpool
                    pooltype = publicclientpool.PublicClientPool
                    purl = pc['scheme'] + poolurl[4:]
                else:
                    from . import httpclientpool
                    pooltype = httpclientpool.HttpClientPool
                    purl = poolurl
                if auth is None:
                    from requests.auth import HTTPBasicAuth
                    auth = HTTPBasicAuth(pc['username'],
                                         pc['password'])
                if client is None:
                    from ..httppool.session import requests_retry_session
                    client = requests_retry_session()
                p = pooltype(poolname=poolname, poolurl=purl,
                             auth=auth, client=client, **kwds)
                res, msg = remoteRegister(p)
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

        :returns: the number of remaining week references if the pool is loaded. Returns 0 if poolname is not found in _GlobalPoolList or weakref count is 0.
        """
        if poolname in cls._GlobalPoolList:
            # print(poolname, getweakrefcount(cls._GlobalPoolList[poolname]))
            return getweakrefcount(cls._GlobalPoolList[poolname])
        else:
            return 0

    @ classmethod
    def removeAll(cls, ignore_error=False):
        """ deletes all pools from the pool list, pools not wiped
        """
        nl = list(cls._GlobalPoolList)
        for pool in nl:
            cls.remove(pool, ignore_error=ignore_error)

    @ classmethod
    def save(cls, poolname, poolobj):
        """
        """
        cls._GlobalPoolList[poolname] = poolobj
        poolobj.setPoolManager(cls)

    @ classmethod
    def remove(cls, poolname, ignore_error=False):
        """ Remove from list and unregister remote pools.

        returns 0 for successful removal, ``1`` for poolname not registered or referenced, still attempted to remove. ``> 1`` for the number of weakrefs the pool still have, and removing failed.
        """
        # number of weakrefs
        nwr = cls.isLoaded(poolname)
        # print(getweakrefs(cls._GlobalPoolList[poolname]), id(
        #    cls._GlobalPoolList[poolname]), '......', nwr)

        if nwr == 1:
            # this is the only reference. unregister remote first.
            thepool = cls._GlobalPoolList[poolname]
            poolurl = thepool._poolurl
            from ..pal.httpclientpool import HttpClientPool
            if issubclass(thepool.__class__, HttpClientPool):
                code = remoteUnregister(poolurl)
            else:
                code = 0
        elif nwr > 1:
            # nothing needs to be done. weakref number will decrement after Storage deletes ref
            return nwr
        else:
            # nwr <=  0
            code = 1
        try:
            pool = cls._GlobalPoolList.pop(poolname)
            pool.setPoolManager(None)
        except KeyError as e:
            if ignore_error:
                logger.info("Ignored: "+str(e))
            else:
                raise
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

    def __setitem__(self, poolname, poolobj):
        """ sets value at key.
        """
        self._GlobalPoolList.__setitem__(poolname, poolobj)
        poolobj.setPoolManager(None, self.__class__)

    def __getitem__(self, *args, **kwargs):
        """ returns value at key.
        """
        return self._GlobalPoolList.__getitem__(*args, **kwargs)

    def __delitem__(self, poolname):
        """ removes value and its key.
        """
        self._GlobalPoolList[poolname].setPoolManager(None)
        self._GlobalPoolList.__delitem__(poolname)

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
