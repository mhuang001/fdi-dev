# -*- coding: utf-8 -*-

from .getswag import swag
from .. import checkpath
from .httppool_server import (
    excp,
    resp
)
from ..session import SESSION

from .. import ctx
from ..model.user import auth
from .. import SES_DBG

from ..._version import __version__, __revision__
from ...dataset.deserialize import deserialize_args, deserialize
from ...pal import poolmanager as pm_mod
from ...pal.poolmanager import Ignore_Not_Exists_Error_When_Delete, PM_S_from_g
from ...pal.productpool import PoolNotFoundError
from ...pal.publicclientpool import PublicClientPool
from ...pal.localpool import LocalPool
from ...pal.webapi import WebAPI
# from ...pal.urn import parseUrn
from ...pal.dicthk import HKDBS
from ...pal.urn import parse_poolurl
from ...utils.getconfig import getConfig
from ...utils.common import (lls,
                             logging_ERROR,
                             logging_WARNING,
                             logging_INFO,
                             logging_DEBUG,
                             trbk
                             )
from ...utils.colortext import (ctext,
                               _CYAN,
                               _GREEN,
                               _HIWHITE,
                               _WHITE_RED,
                               _YELLOW,
                               _MAGENTA,
                               _BLUE_DIM,
                               _BLUE,
                               _RED,
                               _BLACK_RED,
                               _RESET
                               )

from flask import g, Blueprint, jsonify, request, current_app, url_for, abort, session
from werkzeug.exceptions import HTTPException
# from flasgger import swag_from
from urllib.parse import urljoin 

import shutil
import time, importlib
import copy
import os
from operator import itemgetter

from os.path import join, expandvars
from itertools import chain

endp = swag['paths']

pools_api = Blueprint('pools', __name__)

# Do not redirect a URL ends with no slash to URL/

#@pools_api.before_app_request
def XXXb4req_pools():

    logger = current_app.logger
    return

    ##PM_S = PM_S_from_g(g)
    
    if not SESSION:
        if logger.isEnabledFor(logging_DEBUG):
            logger.warning('Called with no SESSION')
        return

    if SES_DBG and logger.isEnabledFor(logging_DEBUG):
        _c =  (ctx(PM_S=PM_S, app=current_app, session=session,
                   request=request, auth=auth))
        logger.debug(f"{_c}")

#@pools_api.after_app_request
def XXXaftreq_pools(resp):

    logger = current_app.logger
    return resp

    if not SESSION:
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug('Called with no SESSION')
        return resp

    PM_S = PM_S_from_g(g)
    if SES_DBG and logger.isEnabledFor(logging_DEBUG):
        logger.debug(ctx(PM_S=PM_S, app=current_app, session=session,
                         request=request, auth=auth))
    resp = save_registered_pools(resp)
    
    return resp


######################################
####   get_pools_url   ####
######################################


@ pools_api.route('/', methods=['GET'], strict_slashes=False)
def get_pools_url():
    """ Get names and urls of all pools, registered or not.
    """
    logger = current_app.logger

    PM_S = PM_S_from_g(g)

    ts = time.time()
    burl = request.base_url

    res = {}
    symbols = [' ', '*', '.']
    maps = list(PM_S._GlobalPoolList.maps[:2])
    maps.append(PM_S._GlobalPoolList.UNLOADED)

    for rank in (0, 1, 2):
        m = {}
        for n, po in maps[rank].items():
            pooltype = 'CSDBpool' if issubclass(po.__class__, PublicClientPool) else 'HTTPpool' if issubclass(po.__class__, LocalPool) else ""
            m[f"({symbols[rank]} {pooltype}) {n}"] = join(burl,n)        
        res.update(m)

    dvers = getConfig('docker_version')
    svers = getConfig('server_version')

    from ..model.user import getUsers
    # report user info
    guser = getattr(g, 'user', None)
    name = getattr(guser, 'username', '')
    roles = getattr(guser, 'roles', '')
    loggedin = guser is not None
    user = {'username': name,
            'logged_in_as': str(roles) if loggedin else "not logged in."                
            }
    u = str(user)
    if logger.isEnabledFor(logging_DEBUG):
            logger.debug(f"{_YELLOW}{u}")

    code = 200
    msg = {'pools_found': len(res),
           'version': {'fdi': __revision__,
                       'docker': dvers if dvers else 'None',
                       'HTTPPool_server': svers if svers else 'None',
                       },
           'user': user,
           }
    return resp(code, res, msg, ts)


######################################
#### /  get_pools   ####
######################################


@ pools_api.route('/_', methods=['GET'])
def get_pools():
    """ Get names of all pools, registered or not.
    """
    logger = current_app.logger

    ts = time.time()
    result = get_name_all_pools()

    res = result
    msg = '%d pools found.' % len(result)
    code = 200
    return resp(code, res, msg, ts)


def get_name_all_pools(path=None, make_dir = False):
    """ Returns names of all pools in the given directory.

    """

    PM_S = PM_S_from_g(g)

    logger = current_app.logger
    path = current_app.config['FULL_BASE_LOCAL_POOLPATH'] if path is None else path
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('Listing all directories from ' + path)

    alldirs = dict(PM_S.getMap())
    if make_dir:
        os.makedirs(path, exist_ok=True)
        allfilelist = os.listdir(path)
        for file in allfilelist:
            filepath = join(path, file)
            if os.path.isdir(filepath):
                alldirs[file] = file
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug(f"PoolManager and {path} have {lls(alldirs, 1000)}")
    return list(alldirs.keys())


####################################################
#### /pools   get_all_pools_size_counts/        ####
#### 333#######################################V#####


@ pools_api.route('/pools', methods=['GET'])
@ auth.login_required(role=['read_only', 'read_write'])
def get_all_pools_size_counts():
    """ Returns a list of Pool IDs (pool names) of all pools and their size and file counts.
    ---
    """

    logger = current_app.logger
    ts = time.time()
    serialize_out = False
    FAILED = '"FAILED"' if serialize_out else 'FAILED'
    data_path = current_app.config['FULL_BASE_LOCAL_POOLPATH']
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('Information of all  pools.')

    if not os.path.exists(data_path):
        return resp(404, FAILED, f'Find no directory at {data_path}')
    pools = {}
    s = c = 0
    for i in os.listdir(data_path):
        _, count, msg, size = get_data_count(None, i)

        pools[i] = {'size_in_bytes': size, 'number_of_data_files': count}
        s += size
        c += count

    result = pools
    msg = 'There is/are %d pools (%s) holding %d products. %.1d MB.' % \
        (len(pools), data_path, c, s/1000000)
    code = 200
    return resp(code, result, msg, ts)

##########################################
#### /pools/   get_registered_pools/  ####
##########################################


@ pools_api.route('/pools/', methods=['GET'])
@ auth.login_required(role=['read_only', 'read_write'])
def get_registered_pools():
    """ Returns a list of Pool IDs (pool names) of all pools registered with the Global PoolManager.
    ---
    """

    logger = current_app.logger
    ts = time.time()
    PM_S  = PM_S_from_g(g)
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('Listing all registered pools.')

        # [p.getPoolurl() for p in PM_S.getMap()()]
    result = list(PM_S.getMap())
    msg = 'There is/are %d pools registered to the PoolManager.' % len(result)
    code = 200
    return resp(code, result, msg, ts)


######################################
#### /pools/register/{pool}       ####
######################################


@ pools_api.route('/pools/register/<string:pool>', methods=['GET'])
@ pools_api.route('/pools/register/<string:pool>/', methods=['GET'])
@ auth.login_required(role='read_write')
def register2(pool):
    """
    Register the given pool with GET.

    Register the pool of given Pool IDs to the global PoolManager.
    This is an alternative to PUT /{pool} using GET".

    Ref. `register` document.
    """

    return register(pool)



######################################
#### /pools/unregister/{pool}     ####
######################################


@ pools_api.route('/pools/unregister/<string:pool>', methods=['GET'])
@ pools_api.route('/pools/unregister/<string:pool>/', methods=['GET'])
@ auth.login_required(role='read_write')
def unregister2(pool):
    """
    Unregister the given pool with GET.

    Unregister the pool of given Pool IDs from the global PoolManager.
    This is an alternative to PUT /{pool} using GET".

    Ref. `unregister` document.
    """

    return unregister(pool)

######################################
#### /lock         ####
######################################


@ pools_api.route('/lock', methods=['PUT', 'GET'])
@ pools_api.route('/lock/', methods=['PUT', 'GET'])
#@ auth.login_required(role=['locker'])
def lock():
    """ Stop serving except the `unlock` one.

    """
    logger = current_app.logger
    ts = time.time()
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('Load all pools.')
    # will have / at the end
    #burl = request.base_url.rsplit('lock', 1)[0]
    current_app.config['SERVER_LOCKED'] = True
    result = 'OK'
    msg = 'Server successfully locked.'
    code = 200
    return resp(code, result, msg, ts)

######################################
#### /unlock         ####
######################################


@ pools_api.route('/unlock', methods=['PUT', 'GET'])
@ pools_api.route('/unlock/', methods=['PUT', 'GET'])
#@ auth.login_required(role=['locker'])
def unlock():
    """ Resume serving.

    """

    logger = current_app.logger
    ts = time.time()
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('Load all pools.')
    # will have / at the end
    burl = request.base_url.rsplit('unlock', 1)[0]
    app.config['SERVER_LOCKED'] = False
    result = 'OK'
    msg = 'Server successfully unlocked.'
    code = 200
    return resp(code, result, msg, ts)


######################################
#### /pools/register_all         ####
######################################


@ pools_api.route('/pools/register_all', methods=['PUT', 'GET'])
@ pools_api.route('/pools/register_all/', methods=['PUT', 'GET'])
#@ auth.login_required(role=['all_doer'])
def register_all():
    """ Register (Load) all pools on the server.

    Including those one stored in session cookies.
    """

    logger = current_app.logger
    ts = time.time()
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('Load all pools.')
    # will have / at the end
    burl = request.base_url.rsplit('register_all', 1)[0]
    result, bad = load_pools(None, auth.current_user())
    code = 400 if len(bad) else 200
    # result = ', '.join(pmap.keys())
    if issubclass(result.__class__, dict):
        result = dict((x, burl+x) for x in result)
    msg = '%d pools successfully loaded. Troubled: %s' % (
        len(result), str(bad))
    return resp(code, result, msg, ts)


def load_pools(poolnames, usr):
    """
    Adding all pool to server pool storage.

    Parameters
    ----------
    poolnames : tr, list
        if given as a list of poolnames, only the exisiting ones of the list will be loaded.
    usr : str
        current authorized user.
    Returns
    -------
    dict
        a `dict` of successfully loaded pools names-pool in `good`, and troubled ones in `bad` with associated exception info.
    """

    logger = current_app.logger
    path = current_app.config['FULL_BASE_LOCAL_POOLPATH']
    # include those that do not have a directory (e.g. csdb)
    PM_S = PM_S_from_g(g)
    pmap = dict(PM_S.getMap())

    bad = {}
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('loading all from ' + path)
    alldirs = poolnames if poolnames else get_name_all_pools(path)
    with current_app.config['LOCKS']['w'], current_app.config['LOCKS']['r'] :
        for nm in alldirs:
            # must save the link or PM_S._GlobalPoolList will remove as dead weakref
            code, thepool, msg = register_pool(nm, usr=usr)
            if code == 200:
                pmap[nm] = thepool
            else:
                bad[nm] = nm+': '+msg

    if logger.isEnabledFor(logging_DEBUG):
        logger.debug("Registered pools: %s, bad %s.  Local dir %s" %
                     (str(list(pmap.keys())), str(list(bad)), path))

    return pmap, bad

######################################
#### /pools/unregister_all        ####
######################################


@ pools_api.route('/pools/unregister_all', methods=['PUT', 'GET'])
@ pools_api.route('/pools/unregister_all/', methods=['PUT', 'GET'])
#@ auth.login_required(role=['all_doer'])
def unregister_all():

    logger = current_app.logger
    ts = time.time()
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('unregister-all ')

    with current_app.config['LOCKS']['w'], current_app.config['LOCKS']['r'] :

        good, bad = unregister_pools()
    code = 200 if not bad else 416
    result = good
    msg = '%d pools unregistered%s' % (len(good),
                                       (' except %s.' % str(bad) if len(bad) else '.'))
    return resp(code, result, msg, ts)


def unregister_pools(poolnames=None):
    """
    Removing all pools from the PoolManager.
`w
    poolnames: if given as a list of poolnames, only the ones in the list will be unregistered.

    Returns: a list of successfully unregistered pools names in `good`, and troubled ones in `bad` with associated exception info.
    """
    logger = current_app.logger
    PM_S = PM_S_from_g(g)
    
    good = []
    notgood = []
    all_pools = poolnames if poolnames else copy.copy(
        list(PM_S.getMap().keys()))
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('unregister pools ' + str(all_pools))

    with current_app.config['LOCKS']['w'], current_app.config['LOCKS']['r'] :
        for nm in all_pools:
            code, res, msg = unregister_pool(nm)
            if res == 'FAILED':
                notgood.append(nm+': '+msg)
            else:
                good.append(nm)
    return good, notgood

######################################
#### /pools/wipe_all   ####
######################################


@ pools_api.route('/pools/wipe_all', methods=['DELETE'])
@ pools_api.route('/pools/wipe_all/', methods=['DELETE'])
@ auth.login_required(role=['all_doer'])
def wipe_all():
    """ Remove contents of all pools.

    Only registerable pools will be wiped. Pool directories are not removed.
    """
    logger = current_app.logger
    ts = time.time()
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('Wipe-all pool')

    good, bad = wipe_pools(None, auth.current_user())
    code = 200 if not bad else 416
    result = good
    msg = '%d pools wiped%s' % (0 if good is None else len(good),
                                (' except %s.' % '.' if bad is None or not len(bad) else str(bad)))
    return resp(code, result, msg, ts)


def wipe_pools(poolnames, usr):
    """
    Deleting all pools using pool api so locking is properly used.

    poolnames: if given as a list of poolnames, only the  ones in the list will be deleted.

    Returns: a list of successfully removed pools names in `good`, and troubled ones in `bad` with associated exception info.
    """
    logger = current_app.logger
    path = current_app.config['FULL_BASE_LOCAL_POOLPATH']
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('DELETING pools contents from ' + path)

    # alldirs = poolnames if poolnames else get_name_all_pools(path)

    good = []
    notgood = []
    all_pools, not_loadable = load_pools(poolnames, usr)
    names = list(all_pools.keys())
    for nm in copy.copy(names):
        thepool = all_pools[nm]
        try:
            re = thepool.removeAll()
            if isinstance(thepool, PublicClientPool):
                res = 0 if re is None or len(re) == 0 else 2
                if res:
                    logger.info('CSDB Pool %s trouble deleting.' % nm)
                    notgood.append(nm+': '+str(res))
                else:
                    good.append(nm)
                    logger.info('Pool %s deleted.' % nm)
            else:
                PM_S = PM_S_from_g(g)
                shutil.rmtree(join(path, nm))
                res = PM_S.remove(nm)
                if res > 1:
                    notgood.append(nm+': '+str(res))
                    logger.info('Pool %s not deleted.' % nm)
                else:
                    good.append(nm)
                    logger.info('Pool %s deleted.' % nm)
        except Exception as e:
            notgood.append(nm+': '+str(e))

    return good, notgood

###########################################
####    /{pool}    /{pool}/  GET, PUT  ####
###########################################


@ pools_api.route('/<string:pool>/', methods=['GET'])
@ pools_api.route('/<string:pool>', methods=['GET'])
@ auth.login_required(role=['read_only', 'read_write'])
def get_pool(pool):
    """ Get information of the given pool.

    Returns the state of the pool of given Pool IDs.
    """

    logger = current_app.logger

    ts = time.time()
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('Get pool info of ' + pool)

    result = get_pool_info(pool)

    return result


def get_pool_info(poolname, serialize_out=False):
    ''' returns information of the pool.
    '''
    msg = ''
    ts = time.time()
    FAILED = '"FAILED"' if serialize_out else 'FAILED'

    allpools = get_name_all_pools(
        current_app.config['FULL_BASE_LOCAL_POOLPATH'])

    if poolname not in allpools:
        code, result, msg = 404, FAILED, poolname + ' is not an existing Pool ID.'
        display = {'result': result}
        return resp(code, display, msg, ts, False)

    PM_S = PM_S_from_g(g)
    try:
        poolobj = PM_S.getPool(poolname)
    except ValueError as e:
        code, result, msg = 409, FAILED, str(e)

    if msg != '':
        display = {'result': result}
    else:
        not_c = not isinstance(poolobj, PublicClientPool)
        code, result, mes = load_HKdata([poolname], serialize_out=not_c)
        if not_c:
            result = deserialize(result, int_key=True)
        burl = request.base_url
        if burl.endswith('/'):
            burl = burl[:-1]

        # add urls to urns
        ty_display = {}
        rec_u = 0
        for cl, sns in result['dTypes'].items():
            if cl == '_STID':
                continue
            snd_url = {}
            # sns is like {'currentSN': 2,
            # 'sn': {'0': {'tags': [], 'meta': [14, 2779]}, '1': ...
            rec_u += len(sns['sn'])
            for sn, snd in sns['sn'].items():
                # str makes a list to show in one line
                base = {'tags': str(snd.get('tags', [])),
                        'meta': str(snd.get('meta', [])),
                        'url': '/'.join((burl, cl, str(sn)))
                        }
                snd_url[sn] = base
            ty_display[cl.rsplit('.', 1)[-1]] = snd_url
        display = {'DataTypes': ty_display}
        # Add url to tags
        dt_display = {}
        for t, clses in result['dTags'].items():
            if t == '_STID':
                continue
            cdict = {}
            j = 0
            for cls, sns in clses.items():
                sndict = dict((int(j), '/'.join((burl, cls, sn)))
                              for sn in sns)
                # use card name as index
                cdict[cls.rsplit('.', 1)[-1]] = sndict
            dt_display[t] = cdict
        display['Tags'] = dt_display

        _, count, _, sz = get_data_count(None, poolname)
        msg ={ 'Getting information pool URL': str(poolobj.poolurl),
               'mes': mes,
               'data items recorded': rec_u,
               'counted': count,
               'bytes total': sz
               }
    return resp(code, display, msg, ts, False)


def register_pool(poolname, usr, poolurl=None):
    """ Register this pool to PoolManager.

    :returns: code, pool object if successful, message
    """

    logger = current_app.logger
    if poolname is None:
        return 401, 'FAILED', f'No pool name.'

    PM_S = PM_S_from_g(g)
    assert id(PM_S._GlobalPoolList.maps[0]) == id(pm_mod._PM_S._GlobalPoolList.maps[0])

    # with secondary={thepool.secondary_poolurl}")
    # read_write has precedence over read_only
    makenew = usr and ('read_write' in usr.roles)
    m = f'poolname={poolname} poolURL={poolurl} makenew={makenew}'
    logger.debug(m)
    
    PM_S = PM_S = PM_S_from_g(g)
    try:
        po = PM_S.getPool(poolname=poolname, poolurl=poolurl, makenew=makenew)
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug(ctx(PM_S=PM_S, app=current_app, session=session, request=request, auth=auth))
        return 200, po, f"Registered {po.poolurl} @ {PM_S()} OK"
    except (ValueError, NotImplementedError, PoolNotFoundError) as e:
        code, result, msg = excp(
            e,
            msg='Unable to register pool: ' + poolname)
        logger.error(msg)
        return code, result, msg

################################################
####  {pool}                      PUT   ####
################################################


@ pools_api.route('/<string:pool>/', methods=['PUT'])
@ pools_api.route('/<string:pool>', methods=['PUT'])
@ auth.login_required(role='read_write')
def register(pool):
    """ Register the given pool.

    Register the pool of given Pool IDs to the global PoolManager.

    :return: response made from http code, poolurl, message
    """

    logger = current_app.logger

    ts = time.time()
    if logger.isEnabledFor(logging_DEBUG):
        PM_S = PM_S_from_g(g)
        assert id(PM_S._GlobalPoolList.maps[0]) == id(pm_mod._PM_S._GlobalPoolList.maps[0])
        logger.debug(ctx(PM_S=PM_S, app=current_app, session=session, request=request, auth=auth))
    
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug(f"Registering pool @ {pool}")

    if ':' in pool:
        # with secondary poolurl
        poolurl = pool.replace(',', '/')
        poolname = poolurl.rsplit('/', 1)[1]
    else:
        poolname = pool
        poolurl = None
    usr = auth.current_user()
    with current_app.config['LOCKS']['w'], current_app.config['LOCKS']['r'] :
        code, thepool, msg = register_pool(poolname, usr, poolurl=poolurl)

    res = thepool if issubclass(thepool.__class__, str) else thepool._poolurl
    return resp(code, res, msg, ts, length=200)


################################################
####  {pool}/unregister DELETE   ####
################################################
@ pools_api.route('/<string:pool>', methods=['DELETE'])
@ auth.login_required(role='read_write')
def unregister(pool):
    """ Unregister this pool from PoolManager.

        Check if the pool exists in server, and unregister or raise exception message to client.

    """
    logger = current_app.logger
    ts = time.time()
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('Unregister pool ' + pool)
    with current_app.config['LOCKS']['w']:
        code, result, msg = unregister_pool(pool)
    return resp(code, result, msg, ts)


def unregister_pool(pool):
    """ Unregister this pool from PoolManager.

    Check if the pool exists in server, and unregister or raise exception message.
    :return: http code, return value, message.
    """
    PM_S = PM_S_from_g(g)

    poolname = pool
    current_app.logger.debug('UNREGISTER (DELETE) POOL' + poolname)

    with current_app.config['LOCKS']['w']:
        try:
            result = PM_S.remove(poolname)
            if result == 1:
                result = '1'
                msg = 'Pool not registered or referenced: ' + poolname
                code = 200
            elif result == 0:
                result = '0'
                msg = 'Unregister pool ' + poolname + ' OK.'
                code = 200
            else:
                result = 'FAILED'
                msg = 'Unable to unregister pool: ' + poolname
                code = 409
            # current_app.logger.debug(f'{code}; {result}; {msg}')
        except Exception as e:
            code, result, msg = excp(
                e,
                msg='Unable to unregister pool: ' + poolname)
            current_app.logger.error(msg)
    current_app.logger.debug(f'{code} {result} {msg}')
    checkpath.cache_clear()
    return code, result, msg


######################################
####  {pool}/hk/          ####
######################################


@ pools_api.route('/<string:pool>/hk', methods=['GET'])
@ pools_api.route('/<string:pool>/hk/', methods=['GET'])
@ auth.login_required(role=['read_only', 'read_write'])
def hk(pool):
    """ All kinds of pool housekeeping data.

    """

    logger = current_app.logger

    ts = time.time()
    pool = pool.strip('/')
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('get HK for ' + pool)

    PM_S = PM_S = PM_S_from_g(g)
    poolobj = PM_S.getPool(pool)
    code, result, msg = load_HKdata([pool, 'hk'], serialize_out=True)

    return resp(code, result, msg, ts, serialize_out=True)


def load_HKdata(paths, serialize_out=True, poolurl=None):
    """Load HKdata of a pool
    """

    poolname = paths[0]
    poolurl = poolurl if poolurl else current_app.config['POOLURL_BASE'] + poolname
    # resourcetype = fullname(data)

    PM_S = PM_S = PM_S_from_g(g)
    try:
        poolobj = PM_S.getPool(poolname=poolname, poolurl=poolurl)
        result = poolobj.readHK(hktype=None, serialize_out=serialize_out)
        msg = 'OK.'
        code = 200
    except Exception as e:
        code, result, msg = excp(e, serialize_out=serialize_out)
        raise e
    return code, result, msg


################################################
####  {pool}/api/        List webAPIs       ####
################################################


@ pools_api.route('/<string:pool>/api/', methods=['GET'])
@ pools_api.route('/<string:pool>/api', methods=['GET'])
@ auth.login_required(role=['read_only', 'read_write'])
def api_info(pool):
    """ A list of names of allowed API methods.

    Returns a list of name of methods allowed to be called with web APIs on this pool.
    """

    logger = current_app.logger

    ts = time.time()
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug(f'get allowed API methods for {pool}')

    return resp(200, WebAPI, 'OK.', ts, serialize_out=False)


######################################
#### /{pool}/wipe  PUT/  ####
######################################


@ pools_api.route('/<string:pool>/wipe', methods=['PUT'])
@ pools_api.route('/<string:pool>/wipe/', methods=['PUT'])
@ auth.login_required(role='read_write')
def wipe(pool):
    """ Removes all contents of the pool.

    requests all data in the pool be removed.
    """
    ts = time.time()
    logger = current_app.logger
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug(f'wipe ' + pool)

    good, bad = wipe_pools([pool], auth.current_user())
    if bad:
        code = 416
        result = 'FAILED'
        msg = 'Unable to wipe ' + pool + ' %s %s' % (str(good), str(bad))
    else:
        code = 200
        result = 0
        msg = 'Wiping %s done.' % pool

    return resp(code, result, msg, ts)

######################################
####  {pool}/hk/{kind}          ####
######################################


@ pools_api.route('/<string:pool>/hk/<string:kind>', methods=['GET'])
@ auth.login_required(role=['read_only', 'read_write'])
def hk_single(pool, kind):
    """ Returns the given kind of pool housekeeping data.
    """

    logger = current_app.logger

    ts = time.time()
    pool = pool.strip('/')
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug(f'get {kind} HK for ' + pool)

    code, result, msg = load_single_HKdata([pool, 'hk', kind])

    return resp(code, result, msg, ts, serialize_out=True)


def load_single_HKdata(paths, serialize_out=True):
    """ Returns pool housekeeping data of the specified type: classes or urns or tags.
    """

    hkname = paths[-1]
    # paths[-2] is 'hk'
    poolname = '/'.join(paths[: -2])
    poolurl = current_app.config['POOLURL_BASE'] + poolname
    # resourcetype = fullname(data)

    PM_S = PM_S_from_g(g)

    if hkname not in HKDBS:
        raise ValueError('Invalid HK type. Must be one of '+', '.join(HKDBS))
    try:
        poolobj = PM_S.getPool(poolname=poolname, poolurl=poolurl)
        result = poolobj.readHK(hkname, serialize_out=serialize_out)
        code, msg = 200, hkname + ' HK data returned OK'
    except Exception as e:
        code, result, msg = excp(e, serialize_out=serialize_out)
    return code, result, msg

######################################
####  {pool}/count/{data_type}          ####
######################################


@ pools_api.route('/<string:pool>/count/', methods=['GET'])
@ pools_api.route('/<string:pool>/count', methods=['GET'])
@ pools_api.route('/<string:pool>/count/<string:data_type>/', methods=['GET'])
@ pools_api.route('/<string:pool>/count/<string:data_type>', methods=['GET'])
def count(pool, data_type=None):
    """ Returns the number of all types or of a given type of data in the given pool.

    Parameter

    :data_type:  (part of) dot-separated full class name of data items in pool.
    """
    logger = current_app.logger
    # return count_general(pool=pool, data_type=data_type, logger=current_app.logger)

    PM_S = PM_S_from_g(g)
    
    # def count_general(pool, data_type, logger):
    ts = time.time()
    poolname = pool.strip('/')
    poolurl = current_app.config['POOLURL_BASE'] + poolname
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug(f'get {data_type} count for ' + pool)

    try:
        poolobj = PM_S.getPool(poolname=poolname, poolurl=poolurl)
        result = poolobj.getCount(data_type)
        code, msg = 200, 'Recorded count of %s returned OK' % (
            data_type if data_type else 'all types')
    except Exception as e:
        code, result, msg = excp(e, serialize_out=False)

    return resp(code, result, msg, ts, serialize_out=False)


@ pools_api.route('/<string:pool>/counted/', methods=['GET'])
@ pools_api.route('/<string:pool>/counted', methods=['GET'])
@ pools_api.route('/<string:pool>/counted/<string:data_type>/', methods=['GET'])
@ pools_api.route('/<string:pool>/counted/<string:data_type>', methods=['GET'])
def counted(pool, data_type=None):
    """ Counts and Returns the number of given type of data in the given pool.

    :data_type1:  (part of) dot-separated full class name of data items in pool.
    """

    logger = current_app.logger

    ts = time.time()
    pool = pool.strip('/')
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug(f'count {data_type} type for ' + pool)

    code, result, msg, size = get_data_count(
        data_type=data_type, pool_id=pool)

    return resp(code, result, msg, ts, serialize_out=False)


def get_data_count(data_type, pool_id, check_register=False):
    """ Return the total count for the given product type, or all types, and pool_id in the directory.

    'data_type': (part of) 'clsssname'. `None` for all types.
    'pool_id': 'pool name'

    """

    logger = current_app.logger
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('### method %s data_type %s pool %s***' %
                     (request.method, data_type, pool_id))
    res = 0
    nm = []

    PM_S = PM_S_from_g(g)

    if check_register and not PM_S.isLoaded(pool_id):
        return 404, 'FAILED', f'Pool {pool_id} not registered.', 0
    pool = PM_S.getPool(pool_id)
    if isinstance(pool, PublicClientPool):
        # res = pool.getCount(typename=data_type, update=True)
        poolnm, paths = (None, pool_id+'/' +
                         data_type) if data_type else (pool_id, None)
        prds = pool.getDataInfo('', paths=paths, pool=poolnm,
                                nulltype=False, limit=1000000)
        res = len(prds)
        size = sum(map(itemgetter('size'), prds))

    else:
        path = join(current_app.config['FULL_BASE_LOCAL_POOLPATH'], pool_id)
        size = 0
        if os.path.exists(path):
            for i in os.listdir(path):
                size += os.path.getsize(join(path, i))
                if i[-1].isnumeric() and ((data_type is None) or (data_type in i)):
                    res = res+1
                    nm.append(i)
        else:
            return 404, 'FAILED', f'Pool {pool_id} not found.', 0
    s = str(nm)
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug(('All types' if data_type is None else data_type) +
                     ' found ' + s)
    return 200, res, 'Counted %d %s files OK.' % (res, data_type if data_type else 'all types'), size


######################################
####  {pool}/api/{method}/{args} ####
######################################


@ pools_api.route('/<string:pool>/api/<string:method_args>/', methods=['GET', 'POST'])
@ pools_api.route('/<string:pool>/api/<string:method_args>', methods=['GET', 'POST'])
@ auth.login_required(role='read_write')
def api(pool, method_args):
    """ Call api mathods on the running pool and returns the result.

    """
    
    logger = current_app.logger

    ts = time.time()
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('get API for %s, %s(%d args).' %
                     (pool, method_args[:6], len(method_args.split('__'))-1))
    PM_S = PM_S_from_g(g)
    #######
    if logger.isEnabledFor(logging_DEBUG):

        logger.debug(ctx(PM_S=PM_S, app=current_app, session=session, request=request, auth=auth))
            
            
    if request.method == 'POST':
        # long args are sent with POST
        if request.data is None:
            result, msg = 'FAILED', 'No Request data for command '+request.method
            code = 400
            return resp(code, result, msg, ts, serialize_out=True)
        data = request.get_data(as_text=True)
        paths = [pool, 'api', method_args, data]
    else:
        paths = [pool, 'api', method_args]
    lp0 = len(paths)

    posted = request.method == 'POST'
    code, result, msg = call_pool_Api(
        paths, serialize_out=False, posted=posted)

    return resp(code, result, msg, ts, serialize_out=False)


def call_pool_Api(paths, serialize_out=False, posted=False):
    """ Call api methods on the running pool and returns the result.

    return: value if args is pool property; execution result if method.
    """

    FAILED = '"FAILED"' if serialize_out else 'FAILED'
    logger = current_app.logger
    ts = time.time()

    if posted:
        code = 200
        try:
            m_args, kwds = tuple(deserialize(paths[3]))
        except ValueError as e:
            code = 422
        m_args.insert(0, paths[2])

    else:
        args, kwds = [], {}
        # the unquoted args. may have ',' in strings
        # quoted_m_args = paths[ind_meth+1]

        # from the unquoted url extract the first path segment.
        quoted_m_args = request.url.split(
            paths[0] + '/' + paths[1] + '/')[1].strip('/')
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug('get API : "%s"' % lls(quoted_m_args, 1000))
        if 0 and quoted_m_args == 'removeTag__tm-all':
            logger.debug(f"%%% {PM_S.isLoaded('test_csdb_fdi2')}")

        # get command positional arguments and keyword arguments
        code, m_args, kwds = deserialize_args(
            quoted_m_args, serialize_out=serialize_out)

    if code != 200:
        result, msg = m_args, kwds
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug(f'RT{code} {msg}')
        return 0, resp(422, result, msg, ts, serialize_out=False), 0

    method = m_args[0]

    if method not in WebAPI:
        code = 400
        msg = 'Unknown web API method: %s.' % method
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug(f'RT{code} {msg}')
        return 0, resp(code, FAILED,  msg,
                       ts, serialize_out=False), 0
    args = m_args[1:] if len(m_args) > 1 else []
    kwdsexpr = [str(k)+'='+str(v) for k, v in kwds.items()]
    msg = '%s(%s)' % (method, ', '.join(
        chain(((getattr(x, 'where', str(x)))[:100] for x in args), kwdsexpr)))
    PM_S = PM_S_from_g(g)
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('WebAPI ' + lls(msg, 300) +
                     (ctx(PM_S=PM_S, app=current_app, session=session, request=request, auth=auth)))


    poolname = paths[0]
    poolurl = current_app.config['POOLURL_BASE'] + poolname
    # not successful
    if not PM_S.isLoaded(poolname):
        if method in ('removeAll', 'wipe') and Ignore_Not_Exists_Error_When_Delete:
            msg = f'{method} API-method ignored: Pool {poolname} not found or not registered.'
            result = 'OK'
            code = 200
            if logger.isEnabledFor(logging_DEBUG):
                logger.debug(f'RT{code} {msg}')
            return 0, resp(code, result, msg, ts, serialize_out=False), 0
        else:
            result = FAILED
            msg = f'{method} API-method: Pool {poolname} not found or not registered.'            
            code = 404
            logger.debug(f'RT{code} {msg}')
            return 0, resp(code, result, msg, ts, serialize_out=False), 0

    try:
        poolobj = PM_S.getPool(poolname=poolname, poolurl=poolurl)
        res = getattr(poolobj, method)(*args, **kwds)
        result = res
        msg = f'{msg}>{lls(res,32)}< OK.'
        code = 200
    except Exception as e:
        if 'not exist' in str(e):
            code = 404
        else:
            code = 422
        code, result, msg = excp(e, code, serialize_out=serialize_out)

    if logger.isEnabledFor(logging_DEBUG):
        logger.debug(f'RT{code} {msg}')
    elif logger.isEnabledFor(logging_INFO):
        logger.debug(f'RT{code} {msg[:39]}')
    return 0, resp(code, result, msg, ts, serialize_out=False), 0
