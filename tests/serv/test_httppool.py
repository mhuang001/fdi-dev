# -*- coding: utf-8 -*-

#################
# This test is to be run on the same machine where the http pool server is running.
#################

from fdi.httppool.model.user import LOGIN_TMPLT
from fdi.dataset.unstructureddataset import UnstructuredDataset
from test_dataset import bookstore, simple_ex, complex_ex, do_jsonPath
from fdi.dataset.testproducts import get_demo_product
from fdi.dataset.serializable import serialize
from fdi.dataset.deserialize import deserialize, serialize_args
from fdi.dataset.product import Product
from fdi.pal.httpclientpool import HttpClientPool
from fdi.pal.poolmanager import PoolManager
from fdi.pal.productstorage import ProductStorage
from fdi.pal.productpool import Lock_Path_Base, makeLockpath
from fdi.utils.common import lls, trbk, fullname
from fdi.utils.fetch import fetch
from fdi.pns.fdi_requests import safe_client
from fdi.pns.jsonio import auth_headers

import pytest
import filelock

import sys
import copy
import concurrent.futures
import requests.models
from urllib.request import pathname2url
from urllib.error import URLError

from flask import current_app, g, request
from requests.auth import HTTPBasicAuth
from flask.wrappers import Response as fwResponse  # live server
# import requests
import random
import os
import requests
import pytest
from pprint import pprint
import time
from collections.abc import Mapping

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


def make_auth(userpass):
    return userpass
    # for mock server.
    # return
    #   "basic", {"username": userpass[0], "password": userpass[1]})


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

def getPayload(aResponse, ignore_error=True):
    """ deserializes, if content_type is json, data or tex of responses from wither the live server or the mock one.
    """

    if not ignore_error:
        assert aResponse.status_code == 200, 'Unsuccessful response %d.' % aResponse.status_code

    x = aResponse.data if issubclass(
        aResponse.__class__, fwResponse) else aResponse.text
    if aResponse.headers['Content-Type'] == 'application/json':
        return deserialize(x, int_key=True),  aResponse.status_code
    else:
        return x, aResponse.status_code


def check_response(o, code=200, failed_case=False, excluded=None, login=False, ordered=True):
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
    oc = o.__class__
    assert issubclass(oc, dict) and 'result' in o or \
        issubclass(oc, str) and 'Bad string to decode as JSON' not in o or \
        issubclass(oc, bytes) and not o.startswith(b'<!DOC') or \
        someone, o
    if failed_case is None:
        return True
    elif not failed_case:
        if not someone:
            # properly formated
            if login:
                if issubclass(oc, bytes) and o.startswith(b'<!doctype html>'):
                    assert b'password' in o
                    return True
                else:
                    return o
            assert 'FAILED' != o['result'], o['msg']
            assert code == 200, str(o)
            if ordered:
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


def test_svcl(server, client):
    aburl, headers = server
    cl = client
    print(cl)
    print(aburl)


def test_root(server, client):
    aburl, headers = server
    url = aburl + '/'
    x = safe_client(client.get, url)
    o, code = getPayload(x)
    check_response(o, code=code)
    c0 = o['result']  # a list
    # no slash
    url = aburl
    x = safe_client(client.get, url)
    o, code = getPayload(x)  # a dict of urls
    if check_response(o, code=code, excluded=['Redirecting']):
        c = o['result']
        assert set(c0) == set(c)
    # /
    url = aburl + '/pools/'
    x = safe_client(client.get, url, headers=headers)
    o, code = getPayload(x)
    check_response(o, code=code)
    c_pools = o['result']  # a dict
    assert set(iter(c_pools)) <= set(iter(c0))


def test_wipe_all_pools_on_server(server, tmp_local_remote_pools, local_pools_dir, client, auth):

    npools = tmp_local_remote_pools
    n = len(npools)
    pool, prd, ref, tag = npools[0]
    # ======== wipe all pools =====
    logger.info('Wipe all pools on the server')

    # register all pools and get count
    aburl, headers = server
    url = aburl + '/' + 'pools/register_all'
    x = safe_client(client.post, url, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=code, failed_case=False)
    regd = o['result']

    # make an unregistered pool by copying an existing pool
    p = os.path.join(local_pools_dir, pool.getId())
    os.system('cp -rf %s %s_copy' % (p, p))
    assert os.path.exists(p+'_copy')

    assert len(get_files_in_local_dir('', local_pools_dir)) >= n+1

    # wipe all pools
    url = aburl + '/' + 'pools/wipe_all'
    x = safe_client(client.delete, url, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=code, failed_case=False)

    files = get_files_in_local_dir('', local_pools_dir)
    assert len(files) == 0, 'Wipe_all_pools failed: ' + \
        o['msg'] + 'Files ' + str(files)


def est_wipe_all_pools_on_server(server, local_pools_dir, client, auth):
    aburl, headers = server
    post_poolid = test_poolid
    # ======== wipe all pools =====
    logger.info('Wipe all pools on the server')

    # register all pools and get count
    url = aburl + '/' + 'pools/register_all'
    x = safe_client(client.post, url, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=code, failed_case=False)
    regd = o['result']

    # make some pools
    n = 5
    import random
    pn = post_poolid+str(random.randint(0, 100))
    lst = make_pools(pn, aburl, client, auth, n)
    # make an unregistered pool by copying an existing pool
    p = os.path.join(local_pools_dir, lst[0].getId())
    os.system('cp -rf %s %s_copy' % (p, p))
    assert os.path.exists(p+'_copy')

    assert len(get_files_in_local_dir('', local_pools_dir)) >= n+1

    # wipe all pools
    url = aburl + '/' + 'pools/wipe_all'
    x = safe_client(client.delete, url, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=code, failed_case=False)

    files = get_files_in_local_dir('', local_pools_dir)
    assert len(files) == 0, 'Wipe_all_pools failed: ' + \
        o['msg'] + 'Files ' + str(files)


def test_new_user_read_write(new_user_read_write, pc):
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the username, hashed_password, authenticated, and roles fields are defined correctly
    https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
    """
    new_user, headers = new_user_read_write
    assert new_user.username == pc['username']
    assert new_user.hashed_password != pc['password']
    assert not new_user.authenticated
    assert new_user.roles == ('read_write',)
    logger.debug('Done.')


def test_new_user_read_only(new_user_read_only, pc):
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the username, hashed_password, authenticated, and roles fields are defined correctly
    """
    new_user, headers = new_user_read_only
    assert new_user.username == pc['ro_user']
    assert not new_user.hashed_password.startswith('o')
    assert not new_user.authenticated
    assert new_user.roles == ('read_only',)
    logger.debug('Done.')


def getapis(server_ro, client):
    aburl, headers = server_ro
    x = safe_client(client.get, aburl.rsplit('/', 1)
                    [0]+'/apispec_1.json', headers=headers)
    return deserialize(x.text if type(x) == requests.models.Response else x.data)


def test_unauthorizedread_write(server, server_ro, client, tmp_local_remote_pools):
    aburl, headers = server
    roaburl, roheaders = server_ro
    pool, prod, ref, tag = tmp_local_remote_pools[0]
    poolid = pool.poolname
    # generate a unauthorized user header
    uheaders = auth_headers('k', 'hu8', headers=headers)
    if uheaders['server_type'] == 'mock':
        # we need to run before_requet, so we call full_dispatch_request
        # ref https://flask.palletsprojects.com/en/2.2.x/testing/#accessing-and-modifying-the-session
        with current_app.test_request_context(aburl+'/pools/', method='GET', headers=uheaders):
            # now we have request set
            with current_app.test_client() as client:
                # now we have client set
                with client.session_transaction() as session:
                    # now we have session set
                    user_id = session.get('user_id')
                    hdrs = str(request.headers)
                    logger.debug('*** session %x user_id = "%s"' %
                                 (id(session), str(user_id))+hdrs)
                    x = current_app.full_dispatch_request()
    else:
        x = safe_client(client.get, aburl+'/pools/', headers=uheaders)
    if LOGIN_TMPLT:
        # In order to use the login page, the return code has to be 200
        assert x.status_code == 200
        o, code = getPayload(x, ignore_error=False)
        assert str(o).startswith('<!doctype html>')
    else:
        # If json is to be used, the return code shoul be 401 to trigger browser login prompt
        assert x.status_code == 401
        o, code = getPayload(x, ignore_error=True)
        assert o in ('Unauthorized Access', b'Unauthorized Access')

    # These needs read_write
    paths = getapis(server_ro, client)['paths']
    for p, ms in paths.items():
        for meth, spec in ms.items():
            api = p.replace('{pool}', poolid)
            if meth == 'post':
                print(meth, aburl+api, '""')
                # unknown user
                x = safe_client(client.post, aburl+api,
                                headers=uheaders, data='')
                assert x.status_code == 200 if p == '/pool/{method_args}' else 401
                # read_only
                x = safe_client(client.post, roaburl+api,
                                headers=roheaders, data='')
                if LOGIN_TMPLT:
                    # In order to use the login page, the return code has to be 200
                    assert x.status_code == 200 if p == '/login' \
                        else 401 if p == '/logout' else 403
                assert x.status_code == 200 if p == '/login' \
                    else 401 if p == '/logout' else 403
                # read_write
                x = safe_client(client.post, aburl+api,
                                headers=headers, data='')
                assert x.status_code == 401 if p == '/user/logout' else 200

    logger.debug('Done.')


def test_authorizedread_write(server, new_user_read_write, client):
    aburl, headers = server
    x = safe_client(client.get, aburl+'/pools/', headers=headers)
    assert x.status_code == 200
    # with pytest.raises(URLError):
    o, code = getPayload(x)
    check_response(o, code=code, login=True)
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
        # x = requests.post(url, auth=make_auth(userpass), data=data)


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
    url = aburl + '/' + path + '/'  # trailing / is needed by mock server
    x = clnt.get(url, auth=auth)
    o, code = getPayload(x)
    # ignore "FAILED" so non-exisiting target will not cause a failed case.
    check_response(o, code=code, failed_case=None)


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
        x = clnt.post(url, auth=auth, data=data)
        # print(len(data))
        o, code = getPayload(x)
        check_response(o, code=code)
        urns.append(o['result'])

    return creators, instruments, urns


def test_CRUD_product(local_pools_dir, server, auth, client):
    ''' test saving, read, delete products API, products will be saved at /data/pool_id
    '''

    logger.info('save products')
    aburl, headers = server

    post_poolid = test_poolid
    # auth = HTTPBasicAuth(*userpass) # not working with mock server
    # auth = tuple(userpasss.values())

    # register
    #pool = make_pools(test_poolid, aburl, client, auth, n=1)
    empty_pool(post_poolid, aburl, auth, client)

    files = [f for f in get_files_in_local_dir(
        post_poolid, local_pools_dir) if f[-1].isnumeric()]
    origin_prod = len(files)

    creators, instruments, urns = populate_pool(
        post_poolid, aburl, auth, client)

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
    x = safe_client(client.get, url, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=code)
    assert o['result'].creator == creators[urns.index(u)], 'Creator not match'

    # ===========
    ''' Test read hk api
    '''
    logger.info('read hk')
    hkpath = '/hk'
    url = aburl + '/' + post_poolid + hkpath + \
        '/'  # trailing / is needed by mock server
    x = safe_client(client.get, url, auth=auth)
    o1, c1 = getPayload(x)
    url2 = aburl + '/' + post_poolid + '/api/readHK' + \
        '/'  # trailing / is needed by mock server
    x2 = safe_client(client.get, url2, auth=auth)
    o2, c2 = getPayload(x2)
    for o, c in [(o1, c1), (o2, c2)]:
        check_response(o, code=c)
        assert o['result']['classes'] is not None, 'Classes jsn read failed'
        assert o['result']['tags'] is not None, 'Tags jsn read failed'
        assert o['result']['urns'] is not None, 'Urns jsn read failed'
        assert o['result']['dTypes'] is not None, 'dTypes jsn read failed'
        assert o['result']['dTags'] is not None, 'dTags jsn read failed'

        inds = list(o['result']['dTypes'][prodt]['sn'])
        l = len(inds)
        # the last l sn's
        assert list(o['result']['dTypes'][prodt]['sn'])[-l:] == inds
        assert o['result']['dTypes'][prodt]['currentSN'] == inds[-1]
        assert len(o['result']['dTags']) == 0
        assert set(':'.join(['urn', post_poolid, prodt, str(i)])
                   for i in inds) == set(urns1)

    logger.info('read dTypes')
    hkpath = '/hk/dTypes'
    url = aburl + '/' + post_poolid + hkpath
    x = safe_client(client.get, url, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=code)
    assert list(o['result'][prodt]['sn'])[-l:] == inds
    assert o['result'][prodt]['currentSN'] == inds[-1]
    assert set('urn:%s:%s:%s' % (post_poolid, c, str(n))
               for c in o['result'] for n in o['result'][c]['sn'].keys()) == set(urns1)

    logger.info('check count')
    num = len(o['result'][prodt]['sn'])
    apipath = '/api/getCount__' + prodt
    url = aburl + '/' + post_poolid + apipath + \
        '/'  # trailing / is needed by mock server
    x = safe_client(client.get, url, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=code)
    assert o['result'] == num

    logger.info('read dTags')
    hkpath = '/hk/dTags'
    url = aburl + '/' + post_poolid + hkpath
    # '/'  # trailing / is needed by mock server
    x = safe_client(client.get, url, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=code)
    assert len(o['result']) == 0

    # ========
    logger.info('delete a product')

    files = [f for f in get_files_in_local_dir(
        post_poolid, local_pools_dir) if f[-1].isnumeric()]
    origin_prod = len(files)

    index = files[-1].rsplit('_', 1)[1]
    # poolname following 'urn' immediately
    url = aburl + '/urn' + post_poolid + '/fdi.dataset.product.Product/' + index

    x = safe_client(client.delete, url, auth=auth)

    o, code = getPayload(x)
    check_response(o, code=code)

    files1 = [f for f in get_files_in_local_dir(
        post_poolid, local_pools_dir) if f[-1].isnumeric()]
    num_prod = len(files1)
    assert num_prod + 1 == origin_prod, 'Products number not match'

    newfiles = set(files) - set(files1)
    assert len(newfiles) == 1
    f = newfiles.pop()
    assert f.endswith(str(index))

    # ':'+poolname following 'urn'
    index2 = files[-2].rsplit('_', 1)[1]
    url2 = aburl + '/urn' + ':' + post_poolid + \
        '/fdi.dataset.product.Product/' + index2

    x = safe_client(client.delete, url2, auth=auth)

    o, code = getPayload(x)
    check_response(o, code=code)

    files2 = [f for f in get_files_in_local_dir(
        post_poolid, local_pools_dir) if f[-1].isnumeric()]
    num_prod2 = len(files2)
    assert num_prod2 + 2 == origin_prod, 'Products number not match'

    newfiles = set(files1) - set(files2)
    assert len(newfiles) == 1
    f = newfiles.pop()
    assert f.endswith(str(index2))

    # ========
    logger.info('wipe a pool')
    files = get_files_in_local_dir(post_poolid, local_pools_dir)
    assert len(files) != 0, 'Pool is already empty: ' + post_poolid

    # wipe the pool on the server
    url = aburl + '/' + post_poolid + '/api/removeAll' + \
        '/'  # trailing / is needed by mock server
    x = safe_client(client.get, url, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=code)

    files = get_files_in_local_dir(post_poolid, local_pools_dir)
    assert len(files) == 0, 'Wipe pool failed: ' + o['msg']

    url = aburl + '/' + post_poolid + '/api/isEmpty' + \
        '/'  # trailing / is needed by mock server
    x = safe_client(client.get, url, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=code)
    assert o['result'] == True

    # ========
    logger.info('unregister a pool on the server')
    url = aburl + '/' + post_poolid
    x = safe_client(client.delete, url, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=code)

    # this should fail as pool is unregistered on the server
    url = aburl + '/' + post_poolid + '/api/isEmpty' + \
        '/'  # trailing / is needed by mock server
    x = safe_client(client.get, url, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=x.status_code, failed_case=True)


def test_data_path(server, auth, client):

    aburl, headers = server
    # empty_pool(post_poolid,aburl,auth)
    pstore = ProductStorage(test_poolid, aburl + '/' +
                            test_poolid, auth=auth, client=client)
    pool = PoolManager.getPool(test_poolid)

    url0 = aburl + '/' + test_poolid + '/'
    # write sample product to the pool
    p = get_demo_product()
    prodt = fullname(p)
    data = serialize(p)
    # print(len(data))
    url1 = url0
    x = safe_client(client.post, url1, auth=auth, data=data)
    o, code = getPayload(x)
    check_response(o, code=code)
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
    x = safe_client(client.get, urlapi, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=code)
    c = o['result']
    assert 'metadata' in c

    # test product paths
    segs = ["measurements", "Time_Energy_Pos", "Energy", "data"]
    pth = '/'.join(segs)
    # make url w/  urn
    # url2       = 'http://127.0.0.1:5000/fdi/v0.10/fdi_serv.test_httppool/fdi.dataset.product.Product/0/measurements/Time_Energy_Pos/Energy/data'
    url2 = aburl + urn.replace(':', '/')[3:] + '/' + pth
    x = safe_client(client.get, url2, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=code)
    c = o['result']
    assert c == p['measurements']['Time_Energy_Pos']['Energy'].data
    # make w/ prodtype
    # fdi.dataset.product.Product/0
    pt = urn.split(':', 2)[2].replace(':', '/')

    urlp = url0 + pt
    # http://127.0.0.1:5000/fdi/v0.10/fdi_serv.test_httppool/fdi.dataset.product.Product/0/measurements/Time_Energy_Pos/Energy/data
    url3 = urlp + '/' + pth
    x = safe_client(client.get, url3, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=code)
    c2 = o['result']
    assert c == p['measurements']['Time_Energy_Pos']['Energy'].data

    for pth in [
            "description",
            "meta/speed/unit",
            "meta/speed/value",
            "meta/speed/isValid",
            "Environment Temperature/data",
            "measurements/calibration/unit",
    ]:
        url = urlp + '/' + pth
        x = safe_client(client.get, url, auth=auth)
        o, code = getPayload(x)
        check_response(o, code=code)
        c = o['result']
        f, s = fetch(pth, p)
        assert c == f
    # members

    # pt = fdi.dataset.product.Product/0
    url = url0 + pt + '/'
    x = safe_client(client.get, url, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=code)
    c = o['result']
    assert 'description' in c

    # string

    # 'http://127.0.0.1:5000/fdi/v0.10/fdi_serv.test_httppool/string/fdi.dataset.product.Product/0'
    url = url0 + pt + '/toString'
    x = safe_client(client.get, url, auth=auth)
    assert x.headers['Content-Type'] == 'text/plain'
    o, c = getPayload(x)
    assert ('UNKNOWN' if isinstance(o, str) else b'UNKNOWN') in o


def test_get_pools(local_pools_dir, server, client):

    aburl, headers = server
    url = aburl + '/'+'pools' + '/'  # trailing / is needed by mock server
    x = safe_client(client.get, url, headers=headers)
    o, code = getPayload(x)
    check_response(o, code=code)
    c = o['result']
    assert len(c)
    assert set(c) == set(get_files_in_local_dir('', local_pools_dir))


def lock_pool2(poolid, sec, local_pools_dir):
    ''' Lock a pool from reading and return a fake response
    '''
    ppath = os.path.join(local_pools_dir, poolid)
    # lock to prevent writing
    lock = Lock_Path_Base + ppath.replace('/', '_') + '.read'
    xx = makeLockpath(poolid, 'r')
    logger.info('Keeping files %s locked for %f sec' % (lock, sec))
    t0 = str(time.time())
    with filelock.FileLock(lock):
        time.sleep(sec)
    fakeres = '{"result": "DONE", "msg": "This is a fake responses", "time": ' + t0 + '}'
    return deserialize(fakeres)


def read_product2(poolid, server, auth, client):

    aburl, headers = server

    # trying to read
    if 1:
        prodpath = '/'+prodt+'/0'
        # trailing / is needed by mock server
        url = aburl + '/' + poolid + prodpath  # + '/'
    else:
        hkpath = '/hk/dTypes'
        url = aburl + '/' + poolid + hkpath + '/'  # trailing / is needed by mock server
    logger.debug('Reading a locked file http...%s' % (url[-5:]))
    x = safe_client(client.get, url, auth=auth)
    r = x.text if type(x) == requests.models.Response else x.data
    logger.info("read %f http...%s  %s" % (time.time(), url[-5:], lls(r, 26)))
    o, code = getPayload(x)
    o['msg'] = r
    return o


def pararun(n, sleep2, *args):
    res, futs = {}, {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=n) as executor:
        for i in range(n):
            time.sleep(sleep2)
            tt = time.time()
            readfut = executor.submit(*args)
            futs[tt] = readfut
        for creadfut in concurrent.futures.as_completed(futs.values()):
            # __import__('pdb').set_trace()

            readres = creadfut.result()
            tt = time.time()
            # logger.info('PPPPPP %f %s FFFF %s' % (readres['time'], readres['result'].description,st$
            #readres['msg'] = tt
            res[tt] = readres
    return res

# https://github.com/pallets/flask/issues/4375#issuecomment-990102774


def Xest_lock_file2(server, userpass, local_pools_dir, client):
    ''' Test if a pool is locked, others can not manipulate this pool anymore before it's released
    '''
    logger.info('%f Test read a locked file, it will return DONE.' %
                time.time())
    aburl, headers = server
    poolid = test_poolid
    # init server
    populate_pool(poolid, aburl, userpass, client)
    # hkpath = '/hk/dTypes'
    # url = aburl + '/' + poolid + hkpath
    # x = safe_client(client.get, url, auth=make_auth(userpass))
    locreadres, futs = {}, {}
    sleep1, sleep2 = 1.0, 0.12

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futs[time.time()] = executor.submit(
            lock_pool2, poolid, sleep1, local_pools_dir)
        logger.info('%f lock submitted. %s. start reading ...' %
                    (time.time(), str(futs)))

        futs[time.time()] = executor.submit(pararun, 10, sleep2,
                                            read_product2, poolid,
                                            server, userpass, client)
        for locreadfut in concurrent.futures.as_completed(futs.values()):
            locreadres[time.time()] = locreadfut.result()

    logger.debug(list(locreadres))
    # __import__('pdb').set_trace()
    for t, r in locreadres.items():
        if r.get('msg', '') == 'This is a fake responses':
            # lock process
            result = r
            tl = t
        else:
            res = r
            tr = t
    logger.debug('res ' + str(res)[:99])

    #assert result['result'] == 'DONE'
    v = list(res.values())
    assert issubclass(v[0].__class__, Mapping)
    assert 'result' in v[-1]
    assert v[0]['result'].description == 'desc 0'
    assert not issubclass(v[-1]['result'].__class__, str)
    print(len(res), v[-1]['time']-result['time'])
    assert v[-1]['time']-result['time'] > sleep1
    assert len(v) > int(sleep1/sleep2) - 1

    """try:
        loop = asyncio.get_running_loop()
        # 1. Run in the default loop's executor:
        #__import__('pdb').set_trace()
        result = await loop.run_in_executor(None, lock_pool2, poolid, sleep1, local_pools_dir)
        for i in range(10):
                readres = read_product2(poolid, server, userpass, client)
                logger.info('PPPPPP %d %d' % (i,i))
                res.append(readres)
                if 'FAIL' in readres['result']:
                     time.sleep(sleep2)
                else:
                     break
        # task=functool.partial(read_product,poolid, server, userpass, client))
        # print('custom thread pool', result, res)
    except Exception as e:
        logger.error('unable to start thread ' + str(e) + trbk(e))
        raise
    """


"""
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


async def read_product(poolid, server, userpass, client):

    aburl, headers = server
    if headers['server_type'] == 'live':
        auth = aiohttp.BasicAuth(*userpass)
    else:
        auth = make_auth(userpass)
    # trying to read
    if 1:
        prodpath = '/'+prodt+'/0'
        # trailing / is needed by mock server
        url = aburl + '/' + poolid + prodpath + '/'
    else:
        hkpath = '/hk/dTypes'
        url = aburl + '/' + poolid + hkpath + '/'  # trailing / is needed by mock server
    logger.debug('Reading a locked file '+url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, auth=auth) as res:
            x = await res.text()
            o = deserialize(x)
    logger.debug("@@@@@@@locked file read: " + lls(x, 200))
    return o

# https://github.com/pallets/flask/issues/4375#issuecomment-990102774


def XXtest_lock_file(server, userpass, local_pools_dir, client):
    ''' Test if a pool is locked, others can not manipulate this pool anymore before it's released
    '''
    logger.info('Test read a locked file, it will return FAILED')
    aburl, headers = server
    poolid = test_poolid
    # init server
    populate_pool(poolid, aburl, userpass, client)
    # hkpath = '/hk/dTypes'
    # url = aburl + '/' + poolid + hkpath
    # x = safe_client(client.get, url, auth=make_auth(userpass))

    try:
        loop = asyncio.get_event_loop()
        tasks = [asyncio.ensure_future(
            lock_pool(poolid, 2, local_pools_dir)), asyncio.ensure_future(read_product(poolid, server, userpass, client))]
        taskres = loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
    except Exception as e:
        logger.error('unable to start thread ' + str(e) + trbk(e))
        raise
    res = [f.result() for f in [x for x in taskres][0]]
    logger.debug('res ' + lls(res[0], 200) + '************' + lls(res[1], 200))
    if issubclass(res[0].__class__, Mapping) and 'result' in res[0] \
       and issubclass(res[0]['result'].__class__, str):
        r1, r2 = res[0], res[1]
    else:
        r2, r1 = res[0], res[1]
    check_response(r1, code=400, failed_case=True)
    """


def test_read_non_exists_pool(server, userpass, client):
    ''' Test read a pool which doesnot exist, returns FAILED
    '''
    logger.info('Test query a pool non exist.')
    aburl, headers = server
    wrong_poolid = 'nonexist_' + __name__.replace('.', '_')
    prodpath = '/' + prodt + '/0'
    url = aburl + '/' + wrong_poolid + prodpath
    x = safe_client(client.get, url, auth=make_auth(userpass))
    o, code = getPayload(x)
    check_response(o, code=400, failed_case=True)


def xtest_webapi_jsonPath(server, userpass, client):
    """
    """

    aburl, headers = server

    logger.info('Create pools on the server.')
    poolid = test_poolid
    poolurl = aburl + '/' + poolid
    pool = HttpClientPool(poolname=poolid, poolurl=poolurl)
    pstore = ProductStorage(pool)
    logger.info('n the server.')

    # ref
    class Get_jsonPath_from_server():
        def __init__(self, data=None, doctype='xml', attr_prefix='', *args, **kwds):
            dnm = 'bookstore' if 'bicycle' in data else 'complex_ex' if 'complex' in data else 'simple_ex'
            u = UnstructuredDataset(data=data, description=dnm,
                                    doctype=doctype, attr_prefix=attr_prefix,
                                    *args, **kwds)
            p = Product(description=dnm, data=u)
            nonlocal pool
            nonlocal pstore
            ref = pstore.save(u, tag=dnm)
            # prod  url. remove 'urn:', ':' -> '/'
            self.pool = pool
            self.purl = aburl + '/' + ref.urn[4:].replace(':', '/')

        def jsonPath(self, *args, **kwds):
            urlargs = serialize_args(*args, not_quoted=False, **kwds)
            urlargs = serialize_args(urlargs, not_quoted=False)
            url = self.purl + '/jsonPath__' + urlargs
            nonlocal userpass
            auth = make_auth(userpass)
            x = safe_client(client.get, url, auth=auth)
            o, code = getPayload(x)
            check_response(o, code=code)
            return o['result']

    do_jsonPath(Get_jsonPath_from_server)


if __name__ == '__main__':
    now = time.time()
    node, verbose = opt(pc)
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
