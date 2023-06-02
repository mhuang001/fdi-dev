# -*- coding: utf-8 -*-


from ..utils.common import (lls,
                            logging_ERROR,
                            logging_WARNING,
                            logging_INFO,
                            logging_DEBUG
                            )

from ..utils.getconfig import getConfig
from .urn import parse_poolurl
from ..pal.httppool import HttpPool
from ..pal.managedpool import ManagedPool, makeLock

from requests.auth import HTTPBasicAuth
from http.cookiejar import MozillaCookieJar as CookieJar

import weakref
from weakref import WeakValueDictionary, getweakrefcount
import getpass
from collections import UserDict
import json
import os
import time
import logging
from requests.exceptions import ConnectionError
from requests.utils import cookiejar_from_dict, dict_from_cookiejar
# create logger
logger = logging.getLogger(__name__)
# logger.setLevel(20)
# logger.debug('level %d' % (logger.getEffectiveLevel()))

pc = getConfig()

DEFAULT_MEM_POOL = 'defaultmem'
# localpool
DEFAULT_POOL = 'fdi_pool_' + __name__ + getpass.getuser()
Invalid_Pool_Names = ['pools', 'urn', 'URN', 'api']

Last_Time_Cookies_Saved = 0
Cookie_File = os.path.abspath(pc['cookie_file'])
print(Cookie_File)
# if not os.path.exists(Cookie_File):
#    os.makedirs(Cookie_File, 0o640,  exist_ok=True)

dbg_7types = False


def restore_cookies(session):
    """Load cookies from file for pool server.

    Cookies are used for pool sessions and are signed.
    If the session does not have a `CookieJar`, it will have after calling.
    """
    if not os.path.exists(Cookie_File):
        return
    cj = CookieJar(Cookie_File)
    # with open(Cookie_File, 'r') as f:
    #    a = f.read()
    # if len(a):
    #    cookies_d = json.loads(a)
    #    cookies = cookiejar_from_dict(cookies_d)
    # session.cookies.update(cookies)
    session.cookies = cj


def save_cookies(session, interval=10):
    """Save cookies from pool server.

    To local filesystem. Cookies are used for pool sessions and are
    signed.
    If the session does not have a `CookieJar`, it will have after calling.

    Parameters
    ----------
    session : Flask Session
        Flask session to get cookies.
    interval : float
        How many seconds before saving to disk. Set to 0 to save immediately.

    Returns
    -------
    None

    Examples
    --------
    FIXME: Add docs.

    """

    global Last_Time_Cookies_Saved

    if time.time() - Last_Time_Cookies_Saved < interval:
        return

    if not issubclass(session.cookies.__class__, CookieJar):
        cj = CookieJar(Cookie_File)
        for c in session.cookies:
            cj.set_cookie(c)
        cj.set_policy(session.cookies.get_policy())
    else:
        cj = session.cookies
    cj.save()
    logger.debug(f"{len(session.cookies)} cookies saved to {Cookie_File}.")
    session.cookies = cj
    # cookies_read = {}
    # if os.path.exists(Cookie_File):
    #     with open(Cookie_File, 'r') as f:
    #         a = f.read()
    #     if len(a):
    #         cookies_d = json.loads(a)
    #         logger.debug(
    #             f'Read {len(cookies_d)} existing cookies from {Cookie_File}')
    #         cookies_read = cookiejar_from_dict(cookies_d)

    # cookies = dict_from_cookiejar(session.cookies)
    # cookies_read.update(cookies)
    # with open(Cookie_File, 'w+') as f:
    #     f.write(json.dumps(cookies_read))
    # logger.debug(f'Merge with {len(cookies)} and save {len(cookies_read)}.')
    Last_Time_Cookies_Saved = time.time()


def get_secondary_poolurl(poolurl, poolhint='csdb:,,'):
    """Get poolurl, and secondary_poolurl etc from a poolurl.

    Extract the name and the secondary_poolurl, if there is any. from
    a poolURL.

    Parameters
    ----------
    poolurl : str
        THe poolURL.
    poolhint : str
        Hint of the beginning of the poolname in the poolurl. Ref
        `productRef::parse_poolurl`.

    Returns
    -------
    tuple
        Poolurl, secondary_poourl, the last fragment of the
        poolurl, the scheme.

    Examples
    --------
    FIXME: Add docs.


    """

    pp, schm, pl, pn, un, pw = parse_poolurl(
        poolurl, poolhint=poolhint)

    if pn.startswith('csdb:,,'):
        # find a encoded poolurl as a temp poolname
        secondary_poolurl = pn.replace(',', '/')
        last_frag = secondary_poolurl.rsplit('/', 1)[-1]
        poolurl = poolurl.replace(pn, last_frag)
    else:
        last_frag = poolurl.rsplit('/', 1)[-1]
        secondary_poolurl = None

    return poolurl, secondary_poolurl, last_frag, schm


def remoteRegister(pool):
    """ if registered a pool's auth and client will be used.

    If the pool has a `secondary_poolurl` property, after '/' is
    replaced by ',', it will be used
    to replace the poolname part of the poolurl for API call.

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
        poolo = pool

        secondary_poolurl = getattr(poolo, 'secondary_poolurl', None)
        if secondary_poolurl:
            secondary_poolurl = secondary_poolurl.replace('/', ',')
            poolurl = pool._poolurl.strip(
                '/').rsplit('/', 1)[0] + '/' + secondary_poolurl
        else:
            poolurl = pool._poolurl.strip('/')

        logger.debug(f'Register {poolurl} on the server.')

        restore_cookies(poolo.client)

        if pool.auth:
            pool.client.auth = pool.auth

        from ..pns.fdi_requests import put_on_server
        try:
            res, msg = put_on_server(
                'urn:::0', poolurl, 'register_pool',
                auth=poolo.auth, client=poolo.client)
        except ConnectionError as e:
            res, msg = 'FAILED', str(e)
            logger.error(poolurl + ' ' + lls(msg, 220))
            raise
        if res == 'FAILED':
            pw = f'{"*"*len(poolo.auth.password)}'
            np = f'<{poolo.auth.username} ' +\
                (pw+'>') if poolo.auth else ' (no authorization)>'

            raise RuntimeError(
                f'Registering {poolurl} failed with auth {np}, {msg}')
        return res, msg

    elif issubclass(pool.__class__, publicclientpool.PublicClientPool):
        from ..pns.fdi_requests import ServerError
        # register csdb pool. If existing, load. IF not exists, create and initialize sn.

        poolurl = pool._poolurl
        stat = 'new'

        # before checking poolExists
        if pool.auth:
            pool.client.auth = pool.auth

        if pool.poolExists():
            logger.info(f'Pool {poolurl} already exists.')
        else:
            logger.info(f'Pool {poolurl} NOT exists.')

            restore_cookies(pool.client)

            try:
                res = pool.createPool2()

            except ServerError as e:
                if e.code != 2:
                    if e.code == 1:
                        msg = 'Bad pool name.'
                    else:
                        msg = 'Unknown reason.'
                    msg = f'Registering {poolurl} failed with auth {np}. {msg} {e}'
                    logger.error(msg)
                    res = 'FAILED'
                    raise
                stat = 'Existing'

        if 0:
            # check news on server log
            _lg = pool.log()
            if _lg:
                logger.info(_lg)

        pool.client.headers.update({'X-AUTH-TOKEN': pool.token})

        pool.poolInfo = pool.getPoolInfo(update_hk=True)
        pool.serverDatatypes = pool.getDataType()
        ######
        if dbg_7types:
            tl = pool.getDataType(substrings='testproducts')
            logger.info(f"{'*'*21} {len(tl)} {tl}")
        #    print(pool.serverDatatypes)

        msg = f'{stat} pool registered.'
        res = 'OK'

        return res, msg
    else:
        raise ValueError(f"Cannot register {pool.__class__} on a server.")


def remoteUnregister(poolurl, auth=None, client=None, poolmanager=None):
    """ Unregister a client pool from remote servers.

    This method does not reference or dereferencepool object. """

    poolurl = poolurl.lower()
    if not (poolurl.startswith('http') or poolurl.startswith('csdb')):
        logger.warning('Ignored: %s not for a HTTPpool.' % poolurl)
        return 1
    logger.debug('unregister %s on the server', poolurl)

    if poolmanager is None:
        poolmanager = PM_S if poolurl.lower[:4] in (
            'http', 'csdb') else PoolManager

    # check if poolurl has been registered
    for pool, poolo in poolmanager._GlobalPoolList.items():
        if issubclass(poolo.__class__, HttpPool):
            continue
        if poolurl == poolo._poolurl:
            if client is None:
                client = poolo.client
            if auth is None:
                auth = poolo.auth
            break
    else:
        if len(poolmanager._GlobalPoolList) != 0:
            raise ValueError(f'Remote Unregistering failed. {poolurl} '
                             'not registered in this client or not suitable.')
    from . import httpclientpool, publicclientpool
    if issubclass(poolo.__class__, httpclientpool.HttpClientPool):
        from ..pns.fdi_requests import delete_from_server
        # url = api_baseurl + post_poolid
        # x = requests.delete(url, auth=HTTPBasicAuth(auth_user, auth_pass))
        # o = deserialize(x.text)
        urn = 'urn:::0'
        try:
            res, msg = delete_from_server(
                urn, poolurl, 'unregister_pool', auth=auth, client=client)
        except ConnectionError as e:
            res, msg = 'FAILED', str(e)
        if res == 'FAILED':
            msg = f'Unregistering {poolurl} failed. {msg}'
            if getattr(poolo, 'ignore_error_when_delete', False):
                logger.info('Ignored: ' + msg)
                code = 2
            else:
                raise ValueError(msg)
        else:
            code = 0
    elif issubclass(poolo.__class__, publicclientpool.PublicClientPool):
        poolo.poolInfo = None
        poolo.serverDatatypes = []
        code = 0
    else:
        code = 0

    save_cookies(poolo.client, interval=0)
    return code


# class ExtendedRef(weakref.ref):
#     """ returns info on how `PoolManager._GlobalPoolList` has been.

#     Ref. python 3.8 weakref doc.
#     """

#     def __init__(self, ob, callback=None, /, **annotations):
#         super().__init__(ob, callback)
#         self.__counter = 0
#         for k, v in annotations.items():
#             setattr(self, k, v)

#     def __call__(self):
#         """Return a pair containing the referent and the number of
#         times the reference has been called.
#         """
#         ob = super().__call__()
#         if ob is not None:
#             self.__counter += 1
#             ob = (ob, self.__counter)
#         return ob


# class Reporting_Wvd(WeakValueDictionary):
class Reporting_Wvd(UserDict):
    def __init__(self, *args, **kwds):
        global logger
        self.logger = logger
        super().__init__(*args, **kwds)

    def set(self, *args, **kwds):
        if self.logger:
            self.logger.debug(f"GPL{hex(id(self))} set. ({args}, {kwds})")

        super().set(*args, **kwds)

    def __setitem__(self, *args, **kwds):
        if self.logger:
            self.logger.debug(f"GPL{hex(id(self))} set_i. ({args}, {kwds})")

        super().__setitem__(*args, **kwds)

    def __getitem__(self, *args, **kwds):
        if self.logger:
            self.logger.debug(f"GPL{hex(id(self))} get_i. ({args}, {kwds})")
        return super().__getitem__(*args, **kwds)

    def __delete__(self, *args, **kwds):
        if self.logger:
            self.logger.debug(f"GPL{hex(id(self))} del. ({args}, {kwds})")
        return super().__delete__(*args, **kwds)

    def __delitem__(self, *args, **kwds):
        if self.logger:
            self.logger.debug(f"GPL{hex(id(self))} del_i. ({args}, {kwds})")
        super().__delitem__(*args, **kwds)

    def pop(self, *args, **kwds):
        if self.logger:
            self.logger.debug(f"GPL{hex(id(self))} pop. ({args}, {kwds})")
            return super().pop(*args, **kwds)

    def __popitem__(self, *args, **kwds):
        if self.logger:
            self.logger.debug(f"GPL{hex(id(self))} pop_i. ({args}, {kwds})")
        return super().__popitem__(*args, **kwds)

    def remove(self, *args, **kwds):
        if self.logger:
            self.logger.debug(f"GPL{hex(id(self))} removed. ({args}, {kwds})")
        return super().remove(*args, **kwds)

    def __update__(self, *args, **kwds):
        if self.logger:
            self.logger.debug(f"GPL{hex(id(self))} updated. ({args}, {kwds})")
        super().__update__(*args, **kwds)


class PoolManager(object):
    """
    This class provides the means to reference ProductPool objects without having to hard-code the type of pool. For example, it could be desired to easily switch from one pool type to another.

This is done by calling the getPool() method, which will return an existing pool or create a new one if necessary.
    """

    _GlobalPoolList = Reporting_Wvd()
    """ Global centralized dictionary that returns singleton -- the same -- pool for the same ID."""

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
    """ Poolpath for each type of pool. """
    del p

    # d = f'PoolManager{hex(id(_GlobalPoolList))}'
    # _locks = dict((op, makeLock(d, op)) for op in ('r', 'w'))

    @classmethod
    def _get_poolurl(cls, name):
        gpl_pool = None

        if not name:
            raise ValueError('Cannot get pool name.')
        # detect if there is secondary_poolurl
        if ':,,' in name:
            secondary_poolurl = name.replace(',', '/')
            poolname = secondary_poolurl.rsplit('/', 1)[-1]
        else:
            poolname = name
            secondary_poolurl = None
        if cls.isLoaded(poolname):
            # registery trumps config file
            gpl_pool = cls._GlobalPoolList.get(poolname, None)
            poolurl = gpl_pool._poolurl
        elif secondary_poolurl:
            poolurl = secondary_poolurl
        else:
            cfg_poolurl = getConfig('poolurl:'+poolname)
            if issubclass(cls, PM_S) and cfg_poolurl.startswith('http'):
                if ':,,' in cfg_poolurl:
                    sp = cfg_poolurl.rsplit('/', 1)
                    poolurl = sp[0]
                    if secondary_poolurl:
                        # use the secondary_poolurl if we have
                        pass
                    else:
                        secondary_poolurl = sp[1].replace(',', '/')
                else:
                    # we are on a server
                    # do not use if getConfig returned a httppool
                    poolurl = 'server://' + \
                        cls.PlacePaths['server'] + '/' + poolname
            else:
                poolurl = cfg_poolurl
                logger.info(
                    f"Made poolurl from getConfig('poolurl:{poolname}'): {poolurl}")

        # old: raise ValueError('A new pool %s cannot be created without a pool url. Is the pool registered?' % poolname)
        return poolname, poolurl, secondary_poolurl, gpl_pool

    @classmethod
    def getPool(cls, poolname=None, poolurl=None, pool=None, makenew=True, auth=None, client=None, **kwds):
        """ returns an instance of pool according to name or path of the pool.

        Returns the pool object if the pool is registered and new
        poolurl, client, auth is not given. Creates the
        pool if it does not already exist. the same poolname-poolurl
        always gets the same pool. Http pools (e.g. `HttpClientPool`
        and `PublicClientPool`) will be registered on the server side.

        If a `PublicClientPool` poolurl (with all '/' changed to ',') is
        placed where poolname is, it is a ```secondary_poolurl```
        (e.g. `csdb:,,foo.edu:12345,csdb,v1,storage,my_pool`).

PoolManager Confiuration for different registration/look-up input::

============================================= ==============================
                  Client                          Server
======== ========== ========= ================ ======= ================ ====
poolname  scheme    pool name pool type in GPL scheme  pool type in GPL schm
-------- ---------- --------- ---------------- ------- ---------------- ----
one frag     file   unchanged LocalPool         N/A     N/A              N/A
one frag     mem    unchanged MemPool           N/A     N/A              N/A
one frag   http(s)  unchanged HttpClientPool    server  HttpPool/server: N/A
one frag    csdb    unchanged PublicClientPool  N/A     N/A              N/A
w/2ndary   http(s)  last frag HttpClientPool    csdb+,  PublicClientPool http
..                            reg. w/ 2ndary
======== ========== ========= ================  ======= ================ ====

Pools registered are kept as long as the last reference remains. When the last is gone the pool gets :meth;`removed` d.

        Parameter
        ---------
        poolname : str
            name of the pool.
        poolurl : str
            If given the poolpath, scheme, place will be derived from it.
             if not given for making a new pool (i.e. when poolname
              is not a registered pool name. If poolname is missing
            it is derived from poolurl; if poolurl is also absent,
            and this class is not `PM_S` or its subclass (i.e. on
            a `Httppool` server),
            `getConfig(f'poolurl:{poolname}')' will be used to get
             poolurl. For `PM_S`, a `ValueError` will b raised.
        pool: ProductPool
            If `auth` and `client` are given they will substitute those of  `pool`. If `pool` is not given, those will need to be given.
        makenew : bool
            When the pool does not exist, make a new one (`True`; default), or `__init__` throws `PoolNotFoundError` (```False```).
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
        secondary_poolurl = gpl_pool = schm = None

        if pool is None:
            # get poolurl and scheme
            if not poolurl and not poolname:
                raise ValueError(
                    "getPool() eeds one of poolname, poolurl, or pool object.")
            elif poolurl:
                # have poolurl, check secondary_poolurl
                poolhint = kwds.get('poolhint', None)
                poolurl, secondary_poolurl, last_frag, schm = get_secondary_poolurl(
                    poolurl, poolhint=poolhint)
                if poolname:
                    if poolname != last_frag:
                        raise ValueError(
                            f"poolname {poolname} is not the last fragment of {poolurl}.")
                else:
                    poolname = last_frag
            else:
                # have poolname only, check secondary_poolurl
                poolhint = kwds.get('poolhint', None)
                poolname, poolurl, secondary_poolurl, gpl_pool = cls._get_poolurl(
                    poolname)

            # now poolname is not None
            if poolname in Invalid_Pool_Names:
                raise ValueError(
                    'Cannot register invalid pool name: ' + poolname)
            # with updated poolname
            if not gpl_pool:
                gpl_pool = cls._GlobalPoolList.get(poolname, None)
            if gpl_pool:
                pool = gpl_pool
                schm = gpl_pool._poolurl.split('://', 1)[0]
            else:
                # now we have poolname, poolurl and maybe  scheme
                # to decide what to
                # register for a client or a server (purl).
                if not schm:
                    schm = poolurl.split('://', 1)[0]
                if schm == 'file':
                    from . import localpool
                    # register a localpool on GPL. No remote.
                    pool = localpool.LocalPool(
                        poolname=poolname, poolurl=poolurl, makenew=makenew, **kwds)
                elif schm == 'mem':
                    from . import mempool
                    # register a mempool on GPL. No remote.
                    pool = mempool.MemPool(
                        poolname=poolname, poolurl=poolurl, **kwds)
                elif schm == 'server':
                    # This registers a HttpP which is a version of local pool.
                    if not issubclass(cls, PM_S):
                        raise ValueError(
                            f'Not allowed to register scheme {schm} pool {poolurl} on a client.')
                    from . import httppool
                    pool = httppool.HttpPool(
                        poolname=poolname, poolurl=poolurl, **kwds)
                elif schm == 'csdb':
                    from . import publicclientpool
                    pool = publicclientpool.PublicClientPool(
                        poolname=poolname,
                        poolurl=pc['scheme'] + poolurl[4:],
                        **kwds)
                elif schm in ('http', 'https'):
                    from . import httpclientpool
                    pool = httpclientpool.HttpClientPool(
                        poolname=poolname,
                        poolurl=poolurl,
                        **kwds)
                    if secondary_poolurl:
                        # secondary_poolurl
                        # instantiate with the "normal" poolurl.
                        # set property 'secondary_poolurl' after instantiation
                        if secondary_poolurl.startswith('csdb'):
                            pool.secondary_poolurl = secondary_poolurl
                        else:
                            # http secondary from local not implemented
                            raise TypeError(
                                f'Not allowed to register scheme {schm} pool {poolurl} on a pool server.')
                else:
                    raise NotImplementedError(f'{schm}:// is not supported')

        else:
            # pool was given from args
            if poolname and poolname != pool._poolname:
                raise ValueError(
                    f'Pool name {poolname} and pool object do not agree.')
            if poolurl and poolurl != pool._poolurl:
                raise ValueError(
                    f'Pool url {poolurl} and pool object do not agree.')

            poolname, poolurl = pool._poolname, pool._poolurl

        # overide existing pool in GPL
        if not gpl_pool and cls.isLoaded(poolname):
            gpl_pool = cls._GlobalPoolList[poolname]
        need_to_reg_save = True
        need_to_set_cl_auth = True
        # These are not saved:
        # pool does not exist but gpl_pool does or
        # both exist but are the same object
        if ((not pool and gpl_pool) or (pool and pool is gpl_pool)):
            need_to_reg_save = False
            logger.debug(f'{pool} is already registered with {poolname}')

        if makenew and issubclass(pool.__class__, ManagedPool):
            pool.make_new()
        if schm in ('http', 'https', 'csdb'):
            # remote types or all tpyes pool gets a client and aut
            if auth is not None:
                pool.auth = auth
            elif getattr(pool, 'auth', None) is None:
                if schm == 'csdb':
                    auth = HTTPBasicAuth(pc['cloud_user'], pc['cloud_pass'])
                else:
                    auth = HTTPBasicAuth(pc['username'], pc['password'])
                pool.auth = auth
            if client is not None:
                pool.client = client
            elif getattr(pool, 'client', None) is None:
                from ..httppool.session import requests_retry_session
                pool.client = requests_retry_session()
                pool.client.auth = auth
        if need_to_reg_save:
            # remote register
            if schm in ('http', 'https', 'csdb'):
                res, msg = remoteRegister(pool)
            # print(getweakrefs(p), id(p), '////')

            # If the pool is a client pool, it is this pool that goes into
            # the PM._GlobalPoolList, not the remote pool
            cls.save(poolname, pool)
            # print(getweakrefs(p), id(p))

            # Pass poolurl to PoolManager.remove() for remote pools
            # finalize(p, print, poolname, poolurl)
        else:
            # no need to save
            pass

        if issubclass(cls, PM_S):
            # if is running on a server, put pool in the sesssion
            from ..httppool.model.user import SESSION
            from flask import session as sess

            if sess and SESSION:
                # save registered pools
                if 'registered_pools' not in sess:
                    sess['registered_pools'] = {}
                if sess['registered_pools'].get(poolname, '') != pool._poolurl:
                    sess['registered_pools'][poolname] = pool._poolurl
                    sess.modified = True

        logger.debug(f'pool {lls(pool, 900)}' +
                     (f' with secondary_poolurl={secondary_poolurl}' if secondary_poolurl else ''))

        return pool

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
            if 1:
                return 1
            else:
                # weakref value dict
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

        Returns
        -------
        int :
            * returns 0 for successful removal
            * ``1`` for poolname not registered or referenced, still attempted to remove. 
            * ``> 1`` for the number of weakrefs the pool still have, and removing failed.
            * ``<0`` Trouble removing entry from `_GlobalPoolList`.
        """

        # number of weakrefs

        nwr = cls.isLoaded(poolname)

        if logger.isEnabledFor(logging_DEBUG):
            logger.debug(
                f"N Weakrefs {cls._GlobalPoolList.get(poolname,'')}....nwr={nwr}")

        if nwr == 1:
            # this is the only reference. unregister remote first.
            thepool = cls._GlobalPoolList[poolname]
            poolurl = thepool._poolurl
            from .httpclientpool import HttpClientPool
            from .publicclientpool import PublicClientPool

            if issubclass(thepool.__class__, (HttpClientPool, PublicClientPool)):
                code = remoteUnregister(poolurl, poolmanager=cls)
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

            from ..httppool.model.user import SESSION
            from flask import session as sess

            if sess and SESSION:
                from flask import session as sess
                # removed registered pools
                if 'registered_pools' in sess:
                    sess['registered_pools'].pop(poolname, '')
                sess.modified = True

        except KeyError as e:
            if ignore_error:
                logger.info("Ignored: "+str(e))
                code = -1
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

    items = _GlobalPoolList.items

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

    @classmethod
    def g(cls):
        return cls._GlobalPoolList.data

    d = _GlobalPoolList.data


class PM_S(PoolManager):
    """Made to provid a different `_GlobalPoolList` useful for testing as a mock"""
    _GlobalPoolList = Reporting_Wvd()
    """ Another Global centralized dict that returns singleton -- the same -- pool for the same ID."""

    # @classmethod
    # def __setitem__(cls, *args, **kwds):
    #     if SESSION:
    #         session.modified = True
    #     PoolManager.__setitem__(*args, **kwds)

    # @classmethod
    # def __delitem__(cls, *args, **kwds):
    #     if SESSION:
    #         session.modified = True
    #     PoolManager.__delitem__(*args, **kwds)

    # @classmethod
    # def setPoolurlMap(cls, *args, **kwds):
    #     if SESSION:
    #         session.modified = True
    #     PoolManager.setPoolurlMap(*args, **kwds)
