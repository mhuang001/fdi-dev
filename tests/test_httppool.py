# -*- coding: utf-8 -*-
import pytest
from fdi.dataset.serializable import serialize
from fdi.dataset.deserialize import deserialize
from fdi.dataset.product import Product
from fdi.pal.poolmanager import PoolManager
from fdi.utils.getconfig import getConfig
from fdi.utils.common import lls, trbk
#from fdi.pns import httppool_server as HS


import filelock
import sys
import base64
from urllib.request import pathname2url
from requests.auth import HTTPBasicAuth
import requests
import random
import os
import time
from collections.abc import Mapping

import asyncio
import aiohttp

from fdi.pns.jsonio import getJsonObj, postJsonObj, putJsonObj, commonheaders
from fdi.utils.options import opt

# default configuration is provided. Copy pnsconfig.py to ~/local.py
from fdi.pns.pnsconfig import pnsconfig as pc


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


pc.update(getConfig())
logger.setLevel(logging.INFO)
logger.debug('logging level %d' % (logger.getEffectiveLevel()))


if 0:
    @pytest.fixture(scope="module")
    def runserver():
        from fdi.pns.httppool_server import app
        app.run(host='127.0.0.1', port=5000,
                threaded=False, debug=verbose, processes=5)

        return smtplib.SMTP("smtp.gmail.com", 587, timeout=5)


testname = 'SVOM'
aburl = 'http://' + pc['node']['host'] + ':' + \
    str(pc['node']['port']) + pc['baseurl']

up = bytes((pc['node']['username'] + ':' +
            pc['node']['password']).encode('ascii'))
code = base64.b64encode(up).decode("ascii")
commonheaders.update({'Authorization': 'Basic %s' % (code)})
del up, code

# last timestamp/lastUpdate
lupd = 0

auth_user = pc['auth_user']
auth_pass = pc['auth_pass']
test_poolid = 'test'
basepath = pc['server_poolpath']
prodt = 'fdi.dataset.product.Product'

# http server pool
schm = 'server'
basepath = PoolManager.PlacePaths[schm]
poolpath = os.path.join(basepath, pc['api_version'])
# client side
cschm = 'http'
api_baseurl = cschm + '://' + \
    PoolManager.PlacePaths[cschm] + '/'


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


def checkserver():
    """ make sure the server is running when tests start
    """
    global testpns
    # check if data already exists
    o = getJsonObj(aburl + '/')
    assert o is not None, 'Cannot connect to the server'
    logger.info('initial server response %s' % (str(o)[:100] + '...'))
    # assert 'result' is not None, 'please start the server to refresh.'
    # initialize test data.


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


def est_getpnspoolconfig():
    ''' gets and compares pnspoolconfig remote and local
    '''
    logger.info('get pnsconfig')
    o = getJsonObj(aburl + '/pnsconfig')
    issane(o)
    r = o['result']
    # , deepcmp(r['scripts'], pc['scripts'])
    assert r['scripts'] == pc['scripts']
    return r


def checkContents(cmd, filename):
    """ checks a GET commands return matches contents of a file.
    """
    o = getJsonObj(aburl + cmd)
    issane(o)
    with open(filename, 'r') as f:
        result = f.read()
    assert result == o['result'], o['message']


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


def clear_server_poolpath(poolid):
    """ deletes files in the given poolid in server pool dir. """
    logger.info('clear server pool dir ' + poolid)
    path = os.path.join(poolpath, poolid)
    if os.path.exists(path):
        if path == '/':
            raise ValueError('!!!!! Cannot delete root.!!!!!!!')
        else:
            os.system('rm -rf ' + path)
        # x = Product(description='desc test case')
        # x.creator = 'test'
        # data = serialize(x)
        # url = api_baseurl + test_poolid + '/fdi.dataset.product.Product/0'
        # x = requests.post(url, auth=HTTPBasicAuth(auth_user, auth_pass), data=data)


def get_files(poolid):
    """ returns a list of files in the given poolid in server pool dir. """

    path = os.path.join(poolpath, poolid)
    if os.path.exists(path):
        files = os.listdir(path)
    else:
        files = []
    return files


def test_clear_server():
    clrpool = 'test_clear'
    cpath = os.path.join(poolpath, clrpool)
    if not os.path.exists(cpath):
        os.makedirs(cpath)
    assert os.path.exists(cpath)
    with open(cpath+'/foo', 'w') as f:
        f.write('k')
    clear_server_poolpath(clrpool)
    assert not os.path.exists(cpath)


def populate_server(poolid):
    creators = ['Todds', 'Cassandra', 'Jane', 'Owen', 'Julian', 'Maurice']
    instruments = ['fatman', 'herscherl', 'NASA', 'CNSC', 'SVOM']

    urns = []
    for index, i in enumerate(creators):
        x = Product(description='desc ' + str(index),
                    instrument=random.choice(instruments))
        x.creator = i
        data = serialize(x)
        url = api_baseurl + poolid + '/' + prodt + '/' + str(index)
        x = requests.post(url, auth=HTTPBasicAuth(
            auth_user, auth_pass), data=data)
        o = deserialize(x.text)
        check_response(o)
        urns.append(o['result'])
    return creators, instruments, urns


def test_CRUD_product():
    ''' test saving, read, delete products API, products will be saved at /data/pool_id
    '''

    logger.info('save products')
    post_poolid = test_poolid
    clear_server_poolpath(post_poolid)

    files = [f for f in get_files(post_poolid) if f[-1].isnumeric()]
    origin_prod = len(files)

    creators, instruments, urns = populate_server(post_poolid)

    files1 = [f for f in get_files(post_poolid) if f[-1].isnumeric()]
    num_prod = len(files1)
    assert num_prod == len(creators) + origin_prod, 'Products number not match'

    newfiles = set(files1) - set(files)
    us = set(u.split(':', 2)[2].replace(':', '_') for u in urns)
    assert newfiles == us, str(newfiles) + str(us)

    # ==========
    logger.info('read product')

    u = random.choice(urns)
    # remove the leading 'urn:'
    url = api_baseurl + u[4:].replace(':', '/')
    x = requests.get(url, auth=HTTPBasicAuth(auth_user, auth_pass))
    o = deserialize(x.text)
    check_response(o)
    assert o['result'].creator == creators[urns.index(u)], 'Creator not match'

    # ===========
    ''' Test read hk api
    '''
    logger.info('read hk')
    hkpath = '/hk'
    url = api_baseurl + post_poolid + hkpath
    x = requests.get(url, auth=HTTPBasicAuth(auth_user, auth_pass))
    o = deserialize(x.text)
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
    assert [d['meta']['creator'].value for
            d in list(o['result']['urns'].values())[-l:]] == creators

    logger.info('read classes')
    hkpath = '/hk/classes'
    url = api_baseurl + post_poolid + hkpath
    x = requests.get(url, auth=HTTPBasicAuth(auth_user, auth_pass))
    o = deserialize(x.text)
    check_response(o)
    assert o['result'][prodt]['sn'][-l:] == inds
    assert o['result'][prodt]['currentSN'] == inds[-1]

    logger.info('read tags')
    hkpath = '/hk/tags'
    url = api_baseurl + post_poolid + hkpath
    x = requests.get(url, auth=HTTPBasicAuth(auth_user, auth_pass))
    o = deserialize(x.text)
    check_response(o)
    assert len(o['result']) == 0

    logger.info('read urns')
    hkpath = '/hk/urns'
    url = api_baseurl + post_poolid + hkpath
    x = requests.get(url, auth=HTTPBasicAuth(auth_user, auth_pass))
    o = deserialize(x.text)
    check_response(o)

    clst = [d['meta']['creator'].value for d in list(
        o['result'].values())[-l:]]
    assert clst == creators

    # ========
    logger.info('delete a product')

    files = [f for f in get_files(post_poolid) if f[-1].isnumeric()]
    origin_prod = len(files)

    index = files[-1].rsplit('_', 1)[1]
    url = api_baseurl + post_poolid + '/fdi.dataset.product.Product/' + index
    x = requests.delete(url, auth=HTTPBasicAuth(auth_user, auth_pass))
    o = deserialize(x.text)
    check_response(o)

    files1 = [f for f in get_files(post_poolid) if f[-1].isnumeric()]
    num_prod = len(files1)
    assert num_prod + 1 == origin_prod, 'Products number not match'

    newfiles = set(files) - set(files1)
    assert len(newfiles) == 1
    f = newfiles.pop()
    assert f.endswith(str(index))

    # ========
    logger.info('delete a pool')
    files = get_files(post_poolid)
    assert len(files) != 0, 'Pool is already empty: ' + post_poolid

    url = api_baseurl + post_poolid
    x = requests.delete(url, auth=HTTPBasicAuth(auth_user, auth_pass))
    o = deserialize(x.text)
    check_response(o)

    files = get_files(post_poolid)
    assert len(files) == 0, 'Wipe pool failed: ' + o['msg']


async def lock_pool(poolid, sec):
    ''' Lock a pool from reading and return a fake response
    '''
    logger.info('Keeping files locked for %f sec' % sec)
    ppath = os.path.join(poolpath, poolid)
    # lock to prevent writing
    lock = '/tmp/fdi_locks/' + ppath.replace('/', '_') + '.write'
    logger.debug(lock)
    with filelock.FileLock(lock):
        await asyncio.sleep(sec)
    fakeres = '{"result": "FAILED", "msg": "This is a fake responses", "timestamp": ' + \
        str(time.time()) + '}'
    return deserialize(fakeres)


async def read_product(poolid):
    # trying to read
    if 1:
        prodpath = '/'+prodt+'/0'
        url = api_baseurl + poolid + prodpath
    else:
        hkpath = '/hk/classes'
        url = api_baseurl + poolid + hkpath
    logger.debug('Reading a locked file '+url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, auth=aiohttp.BasicAuth(auth_user, auth_pass)) as res:
            x = await res.text()
            o = deserialize(x)
    logger.debug("@@@@@@@locked file read: " + lls(x, 200))
    return o


def test_lock_file():
    ''' Test if a pool is locked, others can not manipulate this pool anymore before it's released
    '''
    logger.info('Test read a locked file, it will return FAILED')
    poolid = test_poolid
    # init server
    populate_server(poolid)
    #hkpath = '/hk/classes'
    #url = api_baseurl + poolid + hkpath
    #x = requests.get(url, auth=HTTPBasicAuth(auth_user, auth_pass))

    try:
        loop = asyncio.get_event_loop()
        tasks = [asyncio.ensure_future(
            lock_pool(poolid, 2)), asyncio.ensure_future(read_product(poolid))]
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


def test_read_non_exists_pool():
    ''' Test read a pool which doesn't exist, returns FAILED
    '''
    logger.info('Test query a pool non exist.')
    wrong_poolid = 'abc'
    prodpath = '/' + prodt + '/0'
    url = api_baseurl + wrong_poolid + prodpath
    x = requests.get(url, auth=HTTPBasicAuth(auth_user, auth_pass))
    o = deserialize(x.text)
    check_response(o, True)


def XXXtest_subclasses_pool():
    logger.info('Test create a pool which has subclass')
    poolid_1 = 'subclasses/a'
    poolid_2 = 'subclasses/b'
    prodpath = '/' + prodt + '/0'
    url1 = api_baseurl + poolid_1 + prodpath
    url2 = api_baseurl + poolid_2 + prodpath
    x = Product(description="product example with several datasets",
                instrument="Crystal-Ball", modelName="Mk II")
    data = serialize(x)
    res1 = requests.post(url1, auth=HTTPBasicAuth(
        auth_user, auth_pass), data=data)
    res2 = requests.post(url2, auth=HTTPBasicAuth(
        auth_user, auth_pass), data=data)
    o1 = deserialize(res1.text)
    o2 = deserialize(res2.text)
    check_response(o1)
    check_response(o2)

    # Wipe these pools
    url1 = api_baseurl + poolid_1
    url2 = api_baseurl + poolid_2

    res1 = requests.delete(url1,  auth=HTTPBasicAuth(auth_user, auth_pass))
    res2 = requests.delete(url2,  auth=HTTPBasicAuth(auth_user, auth_pass))
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
