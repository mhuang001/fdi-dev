# -*- coding: utf-8 -*-

from werkzeug.datastructures import Authorization
from fdi.dataset.testproducts import get_demo_product, get_related_product
from fdi.dataset.classes import Class_Look_Up
from fdi.pal.poolmanager import PoolManager
from fdi.pal.productstorage import ProductStorage
from fdi.pns.jsonio import getJsonObj
from fdi.utils.common import lls
from fdi.pns.jsonio import auth_headers
from fdi.httppool.model.user import User
from fdi.pal.publicclientpool import PublicClientPool
from fdi.utils.run_proc import run_proc

from flask_httpauth import HTTPBasicAuth as FH_HTTPBasic_Auth
from flask import current_app
from flask.testing import FlaskClient

from requests.auth import HTTPBasicAuth
import pytest
import importlib
from urllib.error import HTTPError
import os
import time
import pty
import datetime
import requests
import logging
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)


@pytest.fixture(scope='package')
def clean_board():
    importlib.invalidate_caches()
    # importlib.reload(Classes)
    from fdi.dataset.classes import Classes
    return Classes.mapping


@pytest.fixture(scope="package")
def getConfig(clean_board):
    from fdi.utils.getconfig import getConfig as getc
    return getc


@pytest.fixture(scope="package")
def pc(getConfig):
    """ get configuration.

    """
    return getConfig(force=True)

######


SHORT = 'function'


@pytest.fixture(scope=SHORT)
def new_user_read_write(pc):
    """
    GIVEN a User model
    https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
    """
    pn = pc['node']
    new_user = User(pn['username'], pn['password'], role='read_write')
    headers = auth_headers(pn['username'], pn['password'])

    return new_user, headers


@pytest.fixture(scope=SHORT)
def new_user_read_only(pc):
    """
    GIVEN a User model
    https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
    """
    pn = pc['USERS'][1]
    new_user = User(pn['username'], pn['hashed_password'], role=pn['roles'])
    headers = auth_headers(pn['username'], password=pn['hashed_password'])

    return new_user, headers


@pytest.fixture(scope=SHORT)
def userpass(pc):
    auth_user = pc['node']['username']
    auth_pass = pc['node']['password']
    return auth_user, auth_pass


@pytest.fixture
def local_pools_dir(pc):
    """ this is a path in the local OS, where the server runs, used to directly access pool server's internals.

    return: has no trailing '/'
    """
    # http server pool
    schm = 'server'

    # basepath = pc['server_local_pools_dir']
    basepath = PoolManager.PlacePaths[schm]
    #print('WWW ', basepath, pc['api_version'])
    pools_dir = os.path.join(basepath, pc['api_version'])
    return pools_dir

####


@pytest.fixture(scope="module")
def project_app(pc):
    from fdi.httppool import create_app
    return create_app(config_object=pc, level=logger.getEffectiveLevel())


@pytest.fixture(scope="module")
def mock_app(project_app):
    app = project_app
    app.config['TESTING'] = True
    with app.app_context():
        yield app


@pytest.fixture(scope="module")
def background_app(project_app):

    # client side.
    # pool url from a local client
    cschm = 'http'
    aburl = cschm + '://' + PoolManager.PlacePaths[cschm]

    pwdir = os.path.abspath(os.path.join(__file__, '..'))
    as_user = None
    #pid, pty_fd = pty.fork()
    pid = os.fork()
    if pid:
        # child process
        cmd = 'python3.8  httppool_app.py --server=httppool_server'.split()
        try:
            with open('/tmp/pty3', 'rw') as f:
                sta = run_proc(cmd, as_user, pwdir, timeout, f.fileno)
        except IOError:
            sta = run_proc(cmd, as_user, pwdir, timeout)
        logger.info("Background live server status: %s." % str(sta))
    else:
        # main process
        logger.info('live local server %d' % pid)
        sta = None
        # wait for checkserver to return 'live'
        n = 2
        while checkserver(aburl) == 'mock':
            n -= 1
            time.sleep(4)
            if n == 0:
                break
        if n == 0:
            raise RuntimeError('Cannot run server in background.')
    return sta


def checkserver(aburl, excluded=None):
    """ make sure the server is running when tests start.

    when aburl points to an live server running external to this test (e.g. by `make runpoolserver`), server_type is set to 'live'; or a server instance will be created on-demand as a 'mock' up server.
    """

    server_type = None

    # check if data already exists
    try:
        o = getJsonObj(aburl)
        assert o is not None, 'Cannot connect to the server'
        logger.info('Initial server %s response %s' % (aburl, lls(o, 70)))
    except HTTPError as e:
        if e.code == 308:
            logger.info('%s alive. initial server response 308' % (aburl))
            server_type = 'live'
        else:
            logger.warning(aburl + ' is alive. but trouble is ')
            logger.warning(e)
            logger.warning('Live server')
            server_type = 'live'
    except URLError as e:
        logger.info('Not a live server, because %s' % str(e))
        server_type = 'mock'
    else:
        logger.info('Live server')
        server_type = 'live'
    return server_type

    # assert 'measurements' is not None, 'please start the server to refresh.'
    # initialize test data.


@pytest.fixture(scope="module")
def live_or_mock(pc):
    """ Prepares server absolute base url and common headers for clients to use.

    Based on ``PoolManager.PlacePaths[scheme]`` where ``scheme`` is `http` or `https` and auth info from `pnsconfig` from the configuration file and commandline.

    e.g. ```'http://0.0.0.0:5000/v0.7/', ('foo', 'bar')```

    Return
    ------
    tuple:
       baseurl with no trailing '/' and a string set to 'live' if the
       server os alive, 'mock' if the server is not useable as it is.

    """
    server_type = None

    # client side.
    # pool url from a local client
    cschm = 'http'
    aburl = cschm + '://' + PoolManager.PlacePaths[cschm]
    # aburl='http://' + pc['node']['host'] + ':' + \
    #    str(pc['node']['port']) + pc['baseurl']
    server_type = checkserver(aburl)
    if server_type == 'mock':
        ra
    yield aburl, server_type


@pytest.fixture(scope=SHORT)
def server(live_or_mock, new_user_read_write):
    """ Server data from r/w user, mock or alive.

    """
    aburl, ty = live_or_mock
    user, headers = new_user_read_write
    headers['server_type'] = ty
    yield aburl, headers


@pytest.fixture(scope=SHORT)
def server_ro(live_or_mock, new_user_read_only):
    """ Server data from r/w user, alive.

    """
    aburl, ty = live_or_mock
    user, headers = new_user_read_only
    headers['server_type'] = ty
    yield aburl, headers
    del aburl, headers


@pytest.fixture(scope="module")
def request_context(mock_app):
    """create the app and return the request context as a fixture
       so that this process does not need to be repeated in each test
    https://stackoverflow.com/a/66318710
    """

    yield mock_app.test_request_context


@pytest.fixture(scope="module")
def client(live_or_mock, mock_app):

    a, server_type = live_or_mock
    if server_type == 'live':
        logger.info('**** requests as client *****')
        with requests.Session() as live_client:
            yield live_client
    elif server_type == 'mock':
        logger.info('**** mock_app as client *****')
        a = background_app
        with requests.Session() as live_client:
            yield live_client

        if 0:
            with mock_app.test_client() as client:
                if 0:
                    with mock_app.app_context():
                        mock_app.preprocess_request()
                yield client
    else:
        raise ValueError('Invalid server type: ' + server_type)

# @pytest.fixture(scope="module")
# async def a_client(aiohttp_client, server_app, mock_app):
#    if server_app == None:
#        yield aiohttp_client(requests)
#    else:
#        logger.info('**** mock_app as client *****')
#        with mock_app.test_client() as client:
#            with mock_app.app_context():
#                # mock_app.preprocess_request()
#                assert current_app.config["ENV"] == "production"
#            yield aiohttp_client(client)


@pytest.fixture(scope='module')
def demo_product():
    v = get_demo_product()
    return v, get_related_product()


csdb_pool_id = 'test_csdb'


@pytest.fixture(scope="module")
def csdb(pc):
    url = pc['cloud_scheme'] + ':///' + csdb_pool_id
    # pc['cloud_host'] + ':' + \
    # str(pc['cloud_port'])
    test_pool = PublicClientPool(poolurl=url)
    return test_pool, url


@pytest.fixture(scope=SHORT)
def tmp_local_storage(tmp_path_factory):
    """ temporary local pool """

    tmppath = tmp_path_factory.mktemp('pools')
    cschm = 'file'
    pdir = str(tmppath.parent)  # PoolManager.PlacePaths[cschm]
    aburl = cschm + '://' + pdir
    poolid = str(tmppath.name)

    pool = PoolManager.getPool(poolid, aburl + '/' + poolid)
    ps = ProductStorage(pool)
    yield ps


@pytest.fixture(scope=SHORT)
def tmp_remote_storage(server, client, auth):
    """ temporary servered pool with module scope """
    aburl, headers = server
    poolid = 'test_remote_pool'
    pool = PoolManager.getPool(
        poolid, aburl + '/' + poolid, auth=auth, client=client)
    pool.removeAll()
    ps = ProductStorage(pool, client=client, auth=auth)
    assert issubclass(ps.getPool(poolid).client.__class__,
                      (requests.Session, FlaskClient))
    yield ps


@pytest.fixture(scope="module")
def tmp_prods():
    """ temporary local pool with module scope """
    prds = [get_demo_product('test-product-0: Demo_Product')]
    for i, n in enumerate(('BaseProduct', 'Product',
                          'Context', 'MapContext',
                           'TP', 'SP'), 1):
        p = Class_Look_Up[n]('test-product-%d: %s' % (i, n))
        prds.append(p)
    print("Made products: ", list((p.description, id(p)) for p in prds))

    return tuple(prds)


@pytest.fixture(scope=SHORT)
def auth(userpass, live_or_mock):

    a, server_type = live_or_mock
    if server_type == 'live':
        return HTTPBasicAuth(*userpass)
    else:
        return Authorization(
            "basic", {"username": userpass[0], "password": userpass[1]})


def gen_pools(url, auth, client, prds):

    tag = str(datetime.datetime.now())
    lst = []
    # n = len(prds)
    n = 2
    for i in range(n):
        poolid = 'test_%d' % i
        poolurl = url + '/' + poolid
        ps = ProductStorage(poolid, poolurl, client=client, auth=auth)
        # the first pool in ps
        pool = ps.getPool(poolid)
        prd = prds[i]
        prd.description = 'lone prod in '+poolid
        ref = ps.save(prd, tag=tag)
        lst.append((pool, prd, ref, tag))
    return lst


@pytest.fixture(scope=SHORT)
def tmp_pools(server, client, auth, tmp_prods):
    """ generate n pools.

    Return
    ------
    list
        list of tuples containing `ProductPool`, `BaseProduct`, `ProductRef`, `str` for each pool.

"""
    aburl, headers = server
    lst = gen_pools(aburl, auth, client, list(tmp_prods))
    return lst


@pytest.fixture(scope=SHORT)
def tmp_local_remote_pools(server, client, auth, tmp_prods):
    """ generate n local pools.

    Return
    ------
    list
        list of tuples containing `ProductPool`, `BaseProduct`, `ProductRef`, `str` for each pool.

"""
    aburl, headers = server
    if not aburl.startswith('file://') and not '://127.0.0.1' in aburl and not '://0.0.0.0' in aburl:
        raise ValueError('must be a pool running locally. not %s.' % aburl)
    lst = gen_pools(aburl, auth, client, list(tmp_prods))
    return lst


@pytest.fixture(scope=SHORT)
def existing_pools(tmp_pools):
    """ return n existing pools.

    Return
    ------
    list
        list of tuples containing `ProductPool`, `BaseProduct`, `ProductRef`, `str` for each pool.

"""
    pools = [p[0] for p in tmp_pools]
    print("get existing pools:", [p.poolname for p in pools])
    return pools
