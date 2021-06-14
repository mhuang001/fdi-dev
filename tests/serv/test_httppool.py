# -*- coding: utf-8 -*-

#################
# This test is to be run on the same machine where the http pool server is running.
#################


from fdi.dataset.testproducts import get_sample_product
from fdi.dataset.serializable import serialize
from fdi.dataset.deserialize import deserialize
from fdi.dataset.product import Product
from fdi.pal.poolmanager import PoolManager
from fdi.utils.common import lls, trbk, fullname
from fdi.utils.fetch import fetch
#from fdi.pns import httppool_server as HS


import filelock
import sys
from urllib.request import pathname2url
from requests.auth import HTTPBasicAuth
import requests
import random
import os
import pytest
from pprint import pprint

import time
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


# last timestamp/lastUpdate
lupd = 0


test_poolid = 'fdi_'+__name__
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


def issane(o):
    """ basic check on return """
    global lupd
    assert o is not None, "Server is having trouble"
    assert 'error' not in o, o['error']
    assert o['timestamp'] > lupd
    lupd = o['timestamp']


def check0result(result, msg):
    # if msg is string, an exception must have happened
    assert result == 0, 'Error %d testing script "run". msg: ' + str(msg)
    assert msg == '' or not isinstance(msg, (str, bytes)), msg


def est_getpnspoolconfig(pc, setup):
    ''' gets and compares pnspoolconfig remote and local
    '''
    logger.info('get pnsconfig')
    aburl, headers = setup
    o = getJsonObj(aburl + '/'+'pnsconfig')
    issane(o)
    r = o['result']
    # , deepcmp(r['scripts'], pc['scripts'])
    assert r['scripts'] == pc['scripts']
    return r


# TEST HTTPPOOL  API


def check_response(o, failed_case=False):
    global lupd
    assert o is not None, "Server is having trouble"
    if not failed_case:
        assert 'FAILED' != o['result'], o['result']
        assert o['timestamp'] > lupd
        lupd = o['timestamp']
    else:
        assert 'FAILED' == o['result'], o['result']


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


def get_dirs(local_pools_dir):
    """ returns a list of directories in server pool dir. """

    path = local_pools_dir
    if os.path.exists(path):
        files = os.listdir(path)
    else:
        files = []
    return files


def get_files(poolid, local_pools_dir):
    """ returns a list of files in the given poolid in server pool dir. """

    ppath = os.path.join(local_pools_dir, poolid)
    if os.path.exists(ppath):
        files = os.listdir(ppath)
    else:
        files = []
    return files


def test_clear_server(local_pools_dir):
    clrpool = 'test_clear'
    ppath = os.path.join(local_pools_dir, clrpool)
    if not os.path.exists(ppath):
        os.makedirs(ppath)
    assert os.path.exists(ppath)
    with open(ppath+'/foo', 'w') as f:
        f.write('k')
    clear_server_local_pools_dir(clrpool, local_pools_dir)
    assert not os.path.exists(ppath)


def empty_pool_on_server(post_poolid, aburl, auth):
    url = aburl + '/' + post_poolid + '/api/removeAll'
    x = requests.get(url, auth=HTTPBasicAuth(*auth))
    o = deserialize(x.text)
    check_response(o)


def populate_server(poolid, aburl, auth):
    creators = ['Todds', 'Cassandra', 'Jane', 'Owen', 'Julian', 'Maurice']
    instruments = ['fatman', 'herscherl', 'NASA', 'CNSC', 'SVOM']

    urns = []
    for index, i in enumerate(creators):
        x = Product(description='desc ' + str(index),
                    instrument=random.choice(instruments))
        x.creator = i
        data = serialize(x)
        url = aburl + '/' + poolid + '/' + prodt + '/' + str(index)
        # print(len(data))

        x = requests.post(url, auth=HTTPBasicAuth(*auth), data=data)
        o = deserialize(x.text)
        check_response(o)
        urns.append(o['result'])
    return creators, instruments, urns


def test_CRUD_product(local_pools_dir, setup, userpass):
    ''' test saving, read, delete products API, products will be saved at /data/pool_id
    '''

    logger.info('save products')
    aburl, headers = setup
    post_poolid = test_poolid
    # register
    pool = PoolManager.getPool(test_poolid, aburl + '/'+test_poolid)
    empty_pool_on_server(post_poolid, aburl, userpass)

    files = [f for f in get_files(
        post_poolid, local_pools_dir) if f[-1].isnumeric()]
    origin_prod = len(files)

    creators, instruments, urns = populate_server(post_poolid, aburl, userpass)

    files1 = [f for f in get_files(
        post_poolid, local_pools_dir) if f[-1].isnumeric()]
    num_prod = len(files1)
    assert num_prod == len(creators) + origin_prod, 'Products number not match'

    newfiles = set(files1) - set(files)
    us = set(u.split(':', 2)[2].replace(':', '_') for u in urns)
    assert newfiles == us, str(newfiles) + str(us)

    # ==========
    logger.info('read product')

    u = random.choice(urns)
    # remove the leading 'urn:'
    url = aburl + '/' + u[4:].replace(':', '/')
    x = requests.get(url, auth=HTTPBasicAuth(*userpass))
    o = deserialize(x.text)
    check_response(o)
    assert o['result'].creator == creators[urns.index(u)], 'Creator not match'

    # ===========
    ''' Test read hk api
    '''
    logger.info('read hk')
    hkpath = '/hk'
    url = aburl + '/' + post_poolid + hkpath
    x = requests.get(url, auth=HTTPBasicAuth(*userpass))
    o1 = deserialize(x.text)
    url2 = aburl + '/' + post_poolid + '/api/readHK'
    x2 = requests.get(url2, auth=HTTPBasicAuth(*userpass))
    o2 = deserialize(x2.text)
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
        assert set(o['result']['urns'].keys()) == set(urns)

    logger.info('read classes')
    hkpath = '/hk/classes'
    url = aburl + '/' + post_poolid + hkpath
    x = requests.get(url, auth=HTTPBasicAuth(*userpass))
    o = deserialize(x.text)
    check_response(o)
    assert o['result'][prodt]['sn'][-l:] == inds
    assert o['result'][prodt]['currentSN'] == inds[-1]

    logger.info('check count')
    num = len(o['result'][prodt]['sn'])
    apipath = '/api/getCount/' + prodt + ':str'
    url = aburl + '/' + post_poolid + apipath
    x = requests.get(url, auth=HTTPBasicAuth(*userpass))
    o = deserialize(x.text)
    check_response(o)
    assert o['result'] == num

    logger.info('read tags')
    hkpath = '/hk/tags'
    url = aburl + '/' + post_poolid + hkpath
    x = requests.get(url, auth=HTTPBasicAuth(*userpass))
    o = deserialize(x.text)
    check_response(o)
    assert len(o['result']) == 0

    logger.info('read urns')
    hkpath = '/hk/urns'
    url = aburl + '/' + post_poolid + hkpath
    x = requests.get(url, auth=HTTPBasicAuth(*userpass))
    o = deserialize(x.text)
    check_response(o)

    assert set(o['result'].keys()) == set(urns)

    # ========
    logger.info('delete a product')

    files = [f for f in get_files(
        post_poolid, local_pools_dir) if f[-1].isnumeric()]
    origin_prod = len(files)

    index = files[-1].rsplit('_', 1)[1]
    url = aburl + '/' + post_poolid + '/fdi.dataset.product.Product/' + index

    x = requests.delete(url, auth=HTTPBasicAuth(*userpass))

    o = deserialize(x.text)
    check_response(o)

    files1 = [f for f in get_files(
        post_poolid, local_pools_dir) if f[-1].isnumeric()]
    num_prod = len(files1)
    assert num_prod + 1 == origin_prod, 'Products number not match'

    newfiles = set(files) - set(files1)
    assert len(newfiles) == 1
    f = newfiles.pop()
    assert f.endswith(str(index))

    # ========
    logger.info('wipe a pool')
    files = get_files(post_poolid, local_pools_dir)
    assert len(files) != 0, 'Pool is already empty: ' + post_poolid

    # wipe the pool on the server
    url = aburl + '/' + post_poolid + '/api/removeAll'
    x = requests.get(url, auth=HTTPBasicAuth(*userpass))
    o = deserialize(x.text)
    check_response(o)

    files = get_files(post_poolid, local_pools_dir)
    assert len(files) == 0, 'Wipe pool failed: ' + o['msg']

    url = aburl + '/' + post_poolid + '/api/isEmpty'
    x = requests.get(url, auth=HTTPBasicAuth(*userpass))
    o = deserialize(x.text)
    check_response(o)
    assert o['result'] == True

    logger.info('unregister a pool on the server')
    url = aburl + '/' + post_poolid
    x = requests.delete(url, auth=HTTPBasicAuth(*userpass))
    o = deserialize(x.text)
    check_response(o)

    # this should fail as pool is unregistered on the server
    url = aburl + '/' + post_poolid + '/api/isEmpty'
    x = requests.get(url, auth=HTTPBasicAuth(*userpass))
    o = deserialize(x.text)
    check_response(o, failed_case=True)


def test_product_path(setup, userpass):

    aburl, headers = setup
    auth = HTTPBasicAuth(*userpass)
    pool = PoolManager.getPool(test_poolid, aburl + '/'+test_poolid)
    # empty_pool_on_server(post_poolid,aburl,userpass)

    url0 = aburl + '/' + test_poolid + '/'
    # write sample product to the pool
    p = get_sample_product()
    prodt = fullname(p)
    data = serialize(p)
    # print(len(data))
    url1 = url0+prodt + '/0'
    x = requests.post(url1, auth=auth, data=data)
    o = deserialize(x.text)
    check_response(o)
    urn = o['result']

    # API
    pcls = urn.split(':')[2].replace(':', '/')
    urlapi = url0 + pcls
    # 'http://0.0.0.0:5000/v0.7/test/fdi.dataset.product.Product'
    x = requests.get(urlapi, auth=auth)
    o = deserialize(x.text)
    check_response(o)
    c = o['result']
    # pprint(c)
    assert 'metadata' in c

    # test product paths
    segs = ["results", "energy_table", "Energy", "data"]
    pth = '/'.join(segs)
    # make url w/  urn1
    # 'http://0.0.0.0:5000/v0.7/test/urn+test+fdi.dataset.product.Product+0/results/energy_table/Energy/data'
    url2 = url0 + urn.replace(':', '+') + '/' + pth
    x = requests.get(url2, auth=auth)
    o = deserialize(x.text)
    check_response(o)
    c = o['result']
    assert c == p['results']['energy_table']['Energy'].data
    # make w/ prodtype
    # fdi.dataset.product.Product/0
    pt = urn.split(':', 2)[2].replace(':', '/')

    urlp = url0 + pt
    # http://0.0.0.0:5000/v0.7/test/fdi.dataset.product.Product/0/results/energy_table/Energy/data
    url3 = urlp + '/' + pth
    x = requests.get(url3, auth=auth)
    o = deserialize(x.text)
    check_response(o)
    c2 = o['result']
    assert c == p['results']['energy_table']['Energy'].data

    for pth in [
            "description",
            "meta/extra/unit",
            "meta/extra/value",
            "meta/extra/isValid",
            "arraydset 1/data",
            "results/calibration_arraydset/unit",
    ]:
        url = urlp + '/' + pth
        x = requests.get(url, auth=auth)
        o = deserialize(x.text)
        check_response(o)
        c = o['result']
        f, s = fetch(pth, p)
        assert c == f
    # members

    url = url0 + pt + '/'
    x = requests.get(url, auth=auth)
    o = deserialize(x.text)
    check_response(o)
    c = o['result']
    assert 'description' in c

    # string

    # 'http://0.0.0.0:5000/v0.7/test/string/fdi.dataset.product.Product/0'
    url = url0 + pt + '/$string'
    x = requests.get(url, auth=auth)
    assert x.headers['Content-Type'] == 'text/plain'
    c = x.text
    # print(c)
    assert 'UNKNOWN' in c


def test_get_pools(local_pools_dir, setup):

    aburl, headers = setup
    url = aburl + '/'+'pools'
    x = requests.get(url)
    o = deserialize(x.text)
    check_response(o)
    c = o['result']
    assert len(c)
    assert set(c) == set(get_dirs(local_pools_dir))


def test_root(setup):
    aburl, headers = setup
    url = aburl + '/'+'pools'
    x = requests.get(url)
    o = deserialize(x.text)
    check_response(o)
    c_pools = o['result']
    # /
    url = aburl + '/'
    x = requests.get(url)
    o = deserialize(x.text)
    check_response(o)
    c = o['result']
    assert c_pools == c
    # /
    url = aburl
    x = requests.get(url)
    o = deserialize(x.text)
    check_response(o)
    c = o['result']
    assert c_pools == c


async def lock_pool(poolid, sec, local_pools_dir):
    ''' Lock a pool from reading and return a fake response
    '''
    logger.info('Keeping files locked for %f sec' % sec)
    ppath = os.path.join(local_pools_dir, poolid)
    # lock to prevent writing
    lock = '/tmp/fdi_locks/' + ppath.replace('/', '_') + '.write'
    logger.debug(lock)
    with filelock.FileLock(lock):
        await asyncio.sleep(sec)
    fakeres = '{"result": "FAILED", "msg": "This is a fake responses", "timestamp": ' + \
        str(time.time()) + '}'
    return deserialize(fakeres)


async def read_product(poolid, setup, userpass):

    aburl, headers = setup
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


def test_lock_file(setup, userpass, local_pools_dir):
    ''' Test if a pool is locked, others can not manipulate this pool anymore before it's released
    '''
    logger.info('Test read a locked file, it will return FAILED')
    aburl, headers = setup
    poolid = test_poolid
    # init server
    populate_server(poolid, aburl, userpass)
    #hkpath = '/hk/classes'
    #url = aburl + '/' + poolid + hkpath
    #x = requests.get(url, auth=HTTPBasicAuth(*userpass))

    try:
        loop = asyncio.get_event_loop()
        tasks = [asyncio.ensure_future(
            lock_pool(poolid, 2, local_pools_dir)), asyncio.ensure_future(read_product(poolid, setup, userpass))]
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
    check_response(r1, True)


def test_read_non_exists_pool(setup, userpass):
    ''' Test read a pool which doesnot exist, returns FAILED
    '''
    logger.info('Test query a pool non exist.')
    aburl, headers = setup
    wrong_poolid = 'abc'
    prodpath = '/' + prodt + '/0'
    url = aburl + '/' + wrong_poolid + prodpath
    x = requests.get(url, auth=HTTPBasicAuth(*userpass))
    o = deserialize(x.text)
    check_response(o, True)


def XXXtest_subclasses_pool(userpass):
    logger.info('Test create a pool which has subclass')
    poolid_1 = 'subclasses/a'
    poolid_2 = 'subclasses/b'
    prodpath = '/' + prodt + '/0'
    url1 = aburl + '/' + poolid_1 + prodpath
    url2 = aburl + '/' + poolid_2 + prodpath
    x = Product(description="product example with several datasets",
                instrument="Crystal-Ball", modelName="Mk II")
    data = serialize(x)
    res1 = requests.post(url1, auth=HTTPBasicAuth(
        *userpass), data=data)
    res2 = requests.post(url2, auth=HTTPBasicAuth(
        *userpass), data=data)
    o1 = deserialize(res1.text)
    o2 = deserialize(res2.text)
    check_response(o1)
    check_response(o2)

    # Wipe these pools
    url1 = aburl + '/' + poolid_1
    url2 = aburl + '/' + poolid_2

    res1 = requests.delete(url1,  auth=HTTPBasicAuth(*userpass))
    res2 = requests.delete(url2,  auth=HTTPBasicAuth(*userpass))
    o1 = deserialize(res1.text)
    check_response(o1)
    o2 = deserialize(res2.text)
    check_response(o2)


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
