# -*- coding: utf-8 -*-

#################
# This test is to be run on the same machine where the http pool server is running.
#################


from fdi.dataset.testproducts import get_demo_product
from fdi.dataset.serializable import serialize
from fdi.dataset.deserialize import deserialize
from fdi.dataset.product import Product
from fdi.pal.poolmanager import PoolManager
from fdi.pal.productstorage import ProductStorage
from fdi.pal.productpool import Lock_Path_Base
from fdi.utils.common import lls, trbk, fullname
from fdi.utils.fetch import fetch
from fdi.pns.jsonio import auth_headers

import pytest
import filelock
import sys
from urllib.request import pathname2url
from urllib.error import URLError

from flask import current_app
from requests.auth import HTTPBasicAuth
from requests.models import Response as rmResponse  # mock server
from flask.wrappers import Response as fwResponse  # live server
# import requests
import random
import os
import requests
import pytest
from pprint import pprint
import time
import getpass
from collections.abc import Mapping

import asyncio
import aiohttp

from fdi.pns.jsonio import getJsonObj, postJsonObj, putJsonObj, commonheaders
from fdi.utils.options import opt


def setuplogging():
    import logging
    import logging.config
    from . import logdict

    # create logger
    logging.config.dictConfig(logdict.logdict)
    logging.getLogger("requests").setLevel(logging.WARN)
    logging.getLogger("urllib3").setLevel(logging.WARN)
    logging.getLogger("filelock").setLevel(logging.WARN)
    return logging


logging = setuplogging()
logger = logging.getLogger()

logger.setLevel(logging.INFO)
logger.debug('logging level %d' % (logger.getEffectiveLevel()))


if 0:
    @pytest.fixture(scope="module")
    def runserver():
        from fdi.pns.httppool_server import app
        app.run(host='127.0.0.1', port=5000,
                threaded=False, debug=verbose, processes=5)

        return smtplib.SMTP("smtp.gmail.com", 587, timeout=5)


# last time/lastUpdate
lupd = 0


test_poolid = __name__.replace('.', '_')
prodt = 'fdi.dataset.product.Product'


if 0:
    poststr = 'curl -i -H "Content-Type: application/json" -X POST --data @%s http://localhost:5000%s --user %s'
    cmd = poststr % ('resource/' + 'nodetestinput.jsn',
                     pathname2url(pc['baseurl'] + '/' +
                                  nodetestinput['creator'] + '/' +
                                  nodetestinput['rootcause']),
                     'foo:bar')
    print(cmd)
    os.system(cmd)
    sys.exit()


@pytest.fixture(scope="module")
def project_app(pc):
    from fdi.httppool import create_app
    return create_app(config_object=pc, logger=logger)


def issane(o):
    """ basic check on return """
    global lupd
    assert o is not None, "Server is having trouble"
    assert 'error' not in o, o['error']
    assert o['time'] > lupd
    lupd = o['time']


def check0result(result, msg):
    # if msg is string, an exception must have happened
    assert result == 0, 'Error %d testing script "run". msg: ' + str(msg)
    assert msg == '' or not isinstance(msg, (str, bytes)), msg


def est_getpnspoolconfig(pc, server):
    ''' gets and compares pnspoolconfig remote and local
    '''
    logger.info('get pnsconfig')
    aburl, headers = server
    o = getJsonObj(aburl + '/'+'pnsconfig')
    issane(o)
    r = o['result']
    # , deepcmp(r['scripts'], pc['scripts'])
    assert r['scripts'] == pc['scripts']
    return r


# TEST HTTPPOOL  API

def getPayload(aResponse):
    """ deserializes, if content_type is json, data or tex of responses from wither the live server or the mock one.
    """

    x = aResponse.data if issubclass(
        aResponse.__class__, fwResponse) else aResponse.text
    if aResponse.headers['Content-Type'] == 'application/json':
        return deserialize(x)
    else:
        return x


def check_response(o, code=200, failed_case=False, excluded=None):
    """ Generic checking.

    :o: deserialized response data or text.
    :failed_case: True if expecing Fail result; False (default) if Success result; None if to ignore `result` being Fails or not.
    :excluded: a list of string, any of which appears in `result` is to exclude this call from being checked "FAILED".
    """
    global lupd
    if excluded is None:
        excluded = []
    assert o is not None, "Server is having trouble"
    someone = any(x in o for x in excluded)
    assert 'result' in o or \
        'Bad string to decode as JSON' not in o \
        or someone, o
    if not failed_case:
        if not someone:
            # properly formated
            if failed_case is not None:
                assert 'FAILED' != o['result'], o['result']
                assert code == 200, str(o)
                assert o['time'] > lupd
                lupd = o['time']
            return True
    else:
        assert 'FAILED' == o['result'], o['result']
        assert code >= 400, str(o)
        return True
    return False  # not properly formated


def test_clear_local_server(local_pools_dir):

    clrpool = 'test_clear'
    ppath = os.path.join(local_pools_dir, clrpool)
    if not os.path.exists(ppath):
        os.makedirs(ppath)
    assert os.path.exists(ppath)
    with open(ppath+'/foo', 'w') as f:
        f.write('k')
    clear_server_local_pools_dir(clrpool, local_pools_dir)
    assert not os.path.exists(ppath)


def test_root(server, client):
    aburl, headers = server
    url = aburl + '/'
    x = client.get(url)
    o = getPayload(x)
    check_response(o)
    c0 = o['result']  # a list
    # no slash
    url = aburl
    x = client.get(url)
    o = getPayload(x)  # a dict of urls
    if check_response(o, excluded=['Redirecting']):
        c = o['result']
        assert set(c0) == set(c)
    # /
    url = aburl + '/pools'
    x = client.get(url, headers=headers)
    o = getPayload(x)
    check_response(o)
    c_pools = o['result']  # a dict
    assert set(iter(c_pools)) <= set(iter(c0))


def make_pools(name, aburl, clnt, auth, n=1):
    """ generate n pools """

    lst = []
    for i in range(n):
        poolid = name + str(i)
        pool = PoolManager.getPool(poolid, aburl + '/'+poolid)
        lst.append(pool)
        data = serialize(Product('lone prod in '+poolid))
        url = aburl + '/' + poolid + '/'
        x = clnt.post(url, auth=auth, data=data)
        o = getPayload(x)
        check_response(o, failed_case=False)
    return lst[0] if n == 1 else lst


def test_wipe_all_pools_on_server(server, local_pools_dir, client, userpass):
    aburl, headers = server
    post_poolid = test_poolid
    auth = HTTPBasicAuth(*userpass)
    # ======== wipe all pools =====
    logger.info('Wipe all pools on the server')

    # register all pools and get count
    url = aburl + '/' + 'pools/register_all'
    x = client.put(url, auth=auth)
    o = getPayload(x)
    check_response(o, failed_case=False)
    regd = o['result']

    # make some pools
    n = 5
    lst = make_pools(post_poolid, aburl, client, auth, n)
    # make an unregistered pool by copying an existing pool
    p = os.path.join(local_pools_dir, lst[0].getId())
    os.system('cp -rf %s %s_copy' % (p, p))
    assert os.path.exists(p+'_copy')

    assert len(get_files_in_local_dir('', local_pools_dir)) >= n+1

    # wipe all pools
    url = aburl + '/' + 'pools/wipe_all'
    x = client.delete(url, auth=auth)
    o = getPayload(x)
    check_response(o, failed_case=False)

    files = get_files_in_local_dir('', local_pools_dir)
    assert len(files) == 0, 'Wipe_all_pools failed: ' + \
        o['msg'] + 'Files ' + str(files)


def test_new_user_read_write(new_user_read_write, pc):
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the username, hashed_password, authenticated, and role fields are defined correctly
    https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
    """
    new_user, headers = new_user_read_write
    assert new_user.username == pc['node']['username']
    assert new_user.hashed_password != pc['node']['password']
    assert not new_user.authenticated
    assert new_user.role == 'read_write'
    logger.debug('Done.')


def test_new_user_read_only(new_user_read_only, pc):
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the username, hashed_password, authenticated, and role fields are defined correctly
    """
    new_user, headers = new_user_read_only
    assert new_user.username == pc['node']['ro_username']
    assert not new_user.hashed_password.startswith('o')
    assert not new_user.authenticated
    assert new_user.role == 'read_only'
    logger.debug('Done.')


def getapis(server_ro, client):
    aburl, headers = server_ro
    x = client.get(aburl.rsplit('/', 2)[0]+'/apispec_1.json', headers=headers)
    return x.json()


def test_unauthorizedread_write(server, server_ro, client):
    aburl, headers = server
    roaburl, roheaders = server_ro
    poolid = test_poolid
    # generate a unauthorized user header
    uheaders = auth_headers('k', 'hu8')
    x = client.get(aburl+'/pools', headers=uheaders)
    assert x.status_code == 401
    o = getPayload(x)
    assert o == 'Unauthorized Access'

    # These needs read_write
    paths = getapis(server_ro, client)['paths']
    for p, ms in paths.items():
        for meth, spec in ms.items():
            api = p.replace('{pool}', poolid)
            if meth == 'post':
                # unknown user
                x = client.post(aburl+api, headers=uheaders, data='')
                assert x.status_code == 401
                # read_only
                x = client.post(roaburl+api, headers=roheaders, data='')
                assert x.status_code == 200 if p == '/user/login' \
                    else 401 if p == '/user/logout' else 403
                # read_write
                x = client.post(roaburl+api, headers=headers, data='')
                assert x.status_code == 401 if p == '/user/logout' else 200

    logger.debug('Done.')


def test_authorizedread_write(server, new_user_read_write, client):
    aburl, headers = server
    x = client.get(aburl+'/pools', headers=headers)
    assert x.status_code == 200
    # with pytest.raises(URLError):
    o = getPayload(x)
    check_response(o)
    pools = o['result']
    assert isinstance(pools, list)


def clear_server_local_pools_dir(poolid, local_pools_dir):
    """ deletes files in the given poolid in server pool dir. """
    logger.info('clear server pool dir ' + poolid)
    path = os.path.join(local_pools_dir, poolid)
    if os.path.exists(path):
        if path == '/':
            raise ValueError('!!!!! Cannot delete root.!!!!!!!')
        else:
            os.system('rm -rf ' + path)
        # x = Product(description='desc test case')
        # x.creator = 'test'
        # data = serialize(x)
        # url = aburl + '/' + test_poolid + '/fdi.dataset.product.Product/0'
        # x = requests.post(url, auth=HTTPBasicAuth(*userpass), data=data)


def get_files_in_local_dir(poolid, local_pools_dir):
    """ returns a list of files in the given poolid in server pool dir. """

    ppath = os.path.join(local_pools_dir, poolid)
    if os.path.exists(ppath):
        files = os.listdir(ppath)
    else:
        files = []
    return files


def empty_pool(post_poolid, aburl, auth, clnt):
    path = post_poolid + '/api/removeAll'
    url = aburl + '/' + path
    x = clnt.get(url, auth=HTTPBasicAuth(*auth))
    o = getPayload(x)
    # ignore "FAILED" so non-exisiting target will not cause a failed case.
    check_response(o, failed_case=None)


def populate_pool(poolid, aburl, auth, clnt):
    creators = ['Todds', 'Cassandra', 'Jane', 'Owen', 'Julian', 'Maurice']
    instruments = ['fatman', 'herscherl', 'NASA', 'CNSC', 'SVOM']

    urns = []
    for index, i in enumerate(creators):
        x = Product(description='desc ' + str(index),
                    instrument=random.choice(instruments))
        x.creator = i
        data = serialize(x)
        url = aburl + '/' + poolid + '/'
        x = clnt.post(url, auth=HTTPBasicAuth(*auth), data=data)
        # print(len(data))
        o = getPayload(x)
        check_response(o)
        urns.append(o['result'])

    return creators, instruments, urns


@ pytest.fixture(scope='function')
def thepool(server, client, userpass):
    aburl, headers = server
    auth = HTTPBasicAuth(*userpass)
    # register
    pool = 1  # make_pools(test_poolid, aburl, client, auth, n=1)
    yield pool, test_poolid
    del pool


def test_CRUD_product(local_pools_dir, server, userpass, client, thepool):
    ''' test saving, read, delete products API, products will be saved at /data/pool_id
    '''

    logger.info('save products')
    aburl, headers = server

    post_poolid = test_poolid
    auth = HTTPBasicAuth(*userpass)
    # register
    pool = make_pools(test_poolid, aburl, client, auth, n=1)
    empty_pool(post_poolid, aburl, userpass, client)

    files = [f for f in get_files_in_local_dir(
        post_poolid, local_pools_dir) if f[-1].isnumeric()]
    origin_prod = len(files)

    creators, instruments, urns = populate_pool(
        post_poolid, aburl, userpass, client)

    files1 = [f for f in get_files_in_local_dir(
        post_poolid, local_pools_dir) if f[-1].isnumeric()]
    # list of would-be urns from existing files.
    urns1 = ['urn:' + post_poolid + ':' + x.replace('_', ':') for x in files1]
    num_prod = len(files1)
    assert num_prod == len(creators) + origin_prod, 'Products number not match'

    newfiles = set(files1) - set(files)
    us = set(u.split(':', 2)[2].replace(':', '_') for u in urns)
    assert newfiles == us, str(newfiles) + str(us)

    # ==========
    logger.info('read product')

    u = random.choice(urns)
    url = aburl + '/' + u  # [4:].replace(':', '/')
    x = client.get(url, auth=auth)
    o = getPayload(x)
    check_response(o)
    assert o['result'].creator == creators[urns.index(u)], 'Creator not match'

    # ===========
    ''' Test read hk api
    '''
    logger.info('read hk')
    hkpath = '/hk'
    url = aburl + '/' + post_poolid + hkpath
    x = client.get(url, auth=auth)
    o1 = getPayload(x)
    url2 = aburl + '/' + post_poolid + '/api/readHK'
    x2 = client.get(url2, auth=auth)
    o2 = getPayload(x2)
    for o in [o1, o2]:
        check_response(o)
        assert o['result']['classes'] is not None, 'Classes jsn read failed'
        assert o['result']['tags'] is not None, 'Tags jsn read failed'
        assert o['result']['urns'] is not None, 'Urns jsn read failed'

        l = len(urns)
        inds = [int(u.rsplit(':', 1)[1]) for u in urns]
        # the last l sn's
        assert o['result']['classes'][prodt]['sn'][-l:] == inds
        assert o['result']['classes'][prodt]['currentSN'] == inds[-1]
        assert len(o['result']['tags']) == 0
        assert set(o['result']['urns'].keys()) == set(urns1)

    logger.info('read classes')
    hkpath = '/hk/classes'
    url = aburl + '/' + post_poolid + hkpath
    x = client.get(url, auth=auth)
    o = getPayload(x)
    check_response(o)
    assert o['result'][prodt]['sn'][-l:] == inds
    assert o['result'][prodt]['currentSN'] == inds[-1]

    logger.info('check count')
    num = len(o['result'][prodt]['sn'])
    apipath = '/api/getCount__' + prodt
    url = aburl + '/' + post_poolid + apipath
    x = client.get(url, auth=auth)
    o = getPayload(x)
    check_response(o)
    assert o['result'] == num

    logger.info('read tags')
    hkpath = '/hk/tags'
    url = aburl + '/' + post_poolid + hkpath
    x = client.get(url, auth=auth)
    o = getPayload(x)
    check_response(o)
    assert len(o['result']) == 0

    logger.info('read urns')
    hkpath = '/hk/urns'
    url = aburl + '/' + post_poolid + hkpath
    x = client.get(url, auth=auth)
    o = getPayload(x)
    check_response(o)

    assert set(o['result'].keys()) == set(urns1)

    # ========
    logger.info('delete a product')

    files = [f for f in get_files_in_local_dir(
        post_poolid, local_pools_dir) if f[-1].isnumeric()]
    origin_prod = len(files)

    index = files[-1].rsplit('_', 1)[1]
    url = aburl + '/urn' + post_poolid + '/fdi.dataset.product.Product/' + index

    x = client.delete(url, auth=auth)

    o = getPayload(x)
    check_response(o)

    files1 = [f for f in get_files_in_local_dir(
        post_poolid, local_pools_dir) if f[-1].isnumeric()]
    num_prod = len(files1)
    assert num_prod + 1 == origin_prod, 'Products number not match'

    newfiles = set(files) - set(files1)
    assert len(newfiles) == 1
    f = newfiles.pop()
    assert f.endswith(str(index))

    # ========
    logger.info('wipe a pool')
    files = get_files_in_local_dir(post_poolid, local_pools_dir)
    assert len(files) != 0, 'Pool is already empty: ' + post_poolid

    # wipe the pool on the server
    url = aburl + '/' + post_poolid + '/api/removeAll'
    x = client.get(url, auth=auth)
    o = getPayload(x)
    check_response(o)

    files = get_files_in_local_dir(post_poolid, local_pools_dir)
    assert len(files) == 0, 'Wipe pool failed: ' + o['msg']

    url = aburl + '/' + post_poolid + '/api/isEmpty'
    x = client.get(url, auth=auth)
    o = getPayload(x)
    check_response(o)
    assert o['result'] == True

    # ========
    logger.info('unregister a pool on the server')
    url = aburl + '/' + post_poolid
    x = client.delete(url, auth=auth)
    o = getPayload(x)
    check_response(o)

    # this should fail as pool is unregistered on the server
    url = aburl + '/' + post_poolid + '/api/isEmpty'
    x = client.get(url, auth=auth)
    o = getPayload(x)
    check_response(o, code=x.status_code, failed_case=True)


def test_data_path(server, userpass, client):

    aburl, headers = server
    auth = HTTPBasicAuth(*userpass)
    # empty_pool(post_poolid,aburl,userpass)
    pstore = ProductStorage(test_poolid, aburl + '/'+test_poolid)
    pool = PoolManager.getPool(test_poolid)

    url0 = aburl + '/' + test_poolid + '/'
    # write sample product to the pool
    p = get_demo_product()
    prodt = fullname(p)
    data = serialize(p)
    # print(len(data))
    url1 = url0
    x = client.post(url1, auth=auth, data=data)
    o = getPayload(x)
    check_response(o)
    urn = o['result']

    # API
    # url0       = 'http://127.0.0.1:5000/fdi/v0.10/fdi_serv.test_httppool/'
    # url1       = 'http://127.0.0.1:5000/fdi/v0.10/fdi_serv.test_httppool/'
    # urn        = 'urn:fdi_serv.test_httppool:fdi.dataset.product.Product:0'
    # pcls       = 'fdi.dataset.product.Product'
    # urlapi     = 'http://127.0.0.1:5000/fdi/v0.10/fdi_serv.test_httppool/fdi.dataset.product.Product'

    pcls = urn.split(':')[2].replace(':', '/')
    urlapi = url0 + pcls
    # 'http://127.0.0.1:5000/fdi/v0.10/fdi_serv.test_httppool/fdi.dataset.product.Product'
    x = client.get(urlapi, auth=auth)
    o = getPayload(x)
    check_response(o)
    c = o['result']
    # pprint(c)
    assert 'metadata' in c

    # test product paths
    segs = ["results", "Time_Energy_Pos", "Energy", "data"]
    pth = '/'.join(segs)
    # make url w/  urn
    # url2       = 'http://127.0.0.1:5000/fdi/v0.10/fdi_serv.test_httppool/fdi.dataset.product.Product/0/results/Time_Energy_Pos/Energy/data'
    url2 = aburl + urn.replace(':', '/')[3:] + '/' + pth
    x = client.get(url2, auth=auth)
    o = getPayload(x)
    check_response(o)
    c = o['result']
    assert c == p['results']['Time_Energy_Pos']['Energy'].data
    # make w/ prodtype
    # fdi.dataset.product.Product/0
    pt = urn.split(':', 2)[2].replace(':', '/')

    urlp = url0 + pt
    # http://127.0.0.1:5000/fdi/v0.10/fdi_serv.test_httppool/fdi.dataset.product.Product/0/results/Time_Energy_Pos/Energy/data
    url3 = urlp + '/' + pth
    x = client.get(url3, auth=auth)
    o = getPayload(x)
    check_response(o)
    c2 = o['result']
    assert c == p['results']['Time_Energy_Pos']['Energy'].data

    for pth in [
            "description",
            "meta/speed/unit",
            "meta/speed/value",
            "meta/speed/isValid",
            "Environment Temperature/data",
            "results/calibration/unit",
    ]:
        url = urlp + '/' + pth
        x = client.get(url, auth=auth)
        o = getPayload(x)
        check_response(o)
        c = o['result']
        f, s = fetch(pth, p)
        assert c == f
    # members

    # pt = fdi.dataset.product.Product/0
    url = url0 + pt + '/'
    x = client.get(url, auth=auth)
    o = getPayload(x)
    check_response(o)
    c = o['result']
    assert 'description' in c

    # string

    # 'http://127.0.0.1:5000/fdi/v0.10/fdi_serv.test_httppool/string/fdi.dataset.product.Product/0'
    url = url0 + pt + '/toString'
    x = client.get(url, auth=auth)
    assert x.headers['Content-Type'] == 'text/plain'
    c = getPayload(x)
    # print(c)
    assert 'UNKNOWN' in c


def test_get_pools(local_pools_dir, server, client):

    aburl, headers = server
    url = aburl + '/'+'pools'
    x = client.get(url, headers=headers)
    o = getPayload(x)
    check_response(o)
    c = o['result']
    assert len(c)
    assert set(c) == set(get_files_in_local_dir('', local_pools_dir))


async def lock_pool(poolid, sec, local_pools_dir):
    ''' Lock a pool from reading and return a fake response
    '''
    logger.info('Keeping files locked for %f sec' % sec)
    ppath = os.path.join(local_pools_dir, poolid)
    # lock to prevent writing
    lock = Lock_Path_Base + ppath.replace('/', '_') + '.write'
    logger.debug(lock)
    with filelock.FileLock(lock):
        await asyncio.sleep(sec)
    fakeres = '{"result": "FAILED", "msg": "This is a fake responses", "time": ' + \
        str(time.time()) + '}'
    return deserialize(fakeres)


async def read_product(poolid, server, userpass):

    aburl, headers = server
    # trying to read
    if 1:
        prodpath = '/'+prodt+'/0'
        url = aburl + '/' + poolid + prodpath
    else:
        hkpath = '/hk/classes'
        url = aburl + '/' + poolid + hkpath
    logger.debug('Reading a locked file '+url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, auth=aiohttp.BasicAuth(*userpass)) as res:
            x = await res.text()
            o = deserialize(x)
    logger.debug("@@@@@@@locked file read: " + lls(x, 200))
    return o


def test_lock_file(server, userpass, local_pools_dir, client):
    ''' Test if a pool is locked, others can not manipulate this pool anymore before it's released
    '''
    logger.info('Test read a locked file, it will return FAILED')
    aburl, headers = server
    poolid = test_poolid
    # init server
    populate_pool(poolid, aburl, userpass, client)
    # hkpath = '/hk/classes'
    # url = aburl + '/' + poolid + hkpath
    # x = client.get(url, auth=HTTPBasicAuth(*userpass))

    try:
        loop = asyncio.get_event_loop()
        tasks = [asyncio.ensure_future(
            lock_pool(poolid, 2, local_pools_dir)), asyncio.ensure_future(read_product(poolid, server, userpass))]
        taskres = loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
    except Exception as e:
        logger.error('unable to start thread ' + str(e) + trbk(e))
        raise
    res = [f.result() for f in [x for x in taskres][0]]
    logger.debug('res ' + lls(res[0], 200) + '************' + lls(res[1], 200))
    if issubclass(res[0].__class__, Mapping) and 'result' in res[0] and issubclass(res[0]['result'].__class__, str):
        r1, r2 = res[0], res[1]
    else:
        r2, r1 = res[0], res[1]
    check_response(r1, code=400, failed_case=True)


def test_read_non_exists_pool(server, userpass, client):
    ''' Test read a pool which doesnot exist, returns FAILED
    '''
    logger.info('Test query a pool non exist.')
    aburl, headers = server
    wrong_poolid = 'nonexist_' + __name__.replace('.', '_')
    prodpath = '/' + prodt + '/0'
    url = aburl + '/' + wrong_poolid + prodpath
    x = client.get(url, auth=HTTPBasicAuth(*userpass))
    o = getPayload(x)
    check_response(o, code=400, failed_case=True)


if __name__ == '__main__':
    now = time.time()
    node, verbose = opt(pc['node'])
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.info('logging level %d' % (logger.getEffectiveLevel()))

    t = 8

    if t == 7:
        # test_lock()
        # asyncio.AbstractEventLoop.set_debug()
        loop = asyncio.get_event_loop()
        tasks = [asyncio.ensure_future(napa(5, 0)),
                 asyncio.ensure_future(napa(0.5, 0.5))]
        res = loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
        print(res)

    elif t == 3:
        # test_getpnsconfig()
        test_puttestinit()
        test_putinit()
        test_getinit()
        test_getrun()
        test_putconfigpns()
        test_post()
        test_testrun()
        test_deleteclean()
        test_mirror()
        test_sleep()
    elif t == 4:
        test_serverinit()
        test_servertestinit()
        test_servertestrun()
        test_serversleep()
    elif t == 6:
        test_vvpp()

    print('test successful ' + str(time.time() - now))
