# -*- coding: utf-8 -*-


from fdi.dataset.testproducts import get_demo_product, get_related_product
from fdi.dataset.classes import Class_Look_Up
from fdi.dataset.tabledataset import TableDataset
from fdi.dataset.dataset import CompositeDataset
from fdi.dataset.arraydataset import ArrayDataset, Column
from fdi.dataset.metadata import Parameter
from fdi.pal.poolmanager import PoolManager
from fdi.pal.productstorage import ProductStorage
from fdi.pns.jsonio import getJsonObj
from fdi.utils.common import lls
from fdi.pns.jsonio import auth_headers
from fdi.httppool.model.user import User, getUsers
from fdi.httppool.session import requests_retry_session

from fdi.pal.poolmanager import dbg_7types


from flask.testing import FlaskClient
import pytest
import importlib
from urllib.error import HTTPError
from requests.auth import HTTPBasicAuth
import requests
import os
import sys
import json
import time
import copy
import socket
import shlex
import signal
import datetime

from subprocess import Popen, TimeoutExpired
import logging
import logging.config
from urllib.error import URLError

# from logdict import logdict
# logging.config.dictConfig(logdict)

logger = logging.getLogger(__name__)
print('**conftest effective logging level** ', logger.getEffectiveLevel())

# For other module and apps to use.
pytest_plugins = "fdi.testsupport.fixtures"

EX = ' -l /tmp/foo.log'

ALL_ARCHS = ('http', 'csdb', '')

DEFAULT_SERVER_RUN_METHOD = ''
DEFAULT_SERVER_ARCH = 'http'

""" DEfault how the test server is to be run """

BG_SERVER_LOG = '/tmp/test_background_server.log'
SVR_PATH=os.path.abspath(os.path.dirname(__file__)+'/../../httppool_app.py')

POOL_SEVER_THREAD = 1
RUN_SERVER_IN_BACKGROUND = f'python3 {SVR_PATH} --server=httppool_server --logstream {BG_SERVER_LOG} -d'
""" set to '' to disable running a pool in the background as the mock. """



def pytest_addoption(parser):
    """ Chooses how the test server is to run.
    """
    parser.addoption(
        "--server",
        action='store',
        #dest='SERVER_RUN',
        default=DEFAULT_SERVER_RUN_METHOD,
        help="'mock' for Flask mock server; 'background'for spawning a httppool server in the background; 'external' for using a server already setup somewhere for testing.",
        choices=('background', 'external', 'mock')
    )
    parser.addoption(
        "--id",
        action='store',
        #dest='SERVER_RUN',
        default=0,
        type=int,
        help=\
        "0 for http test_pool_1 /csdb sv2 / fdi types;"
        "1 for http test_pool_1 /csdb sv2 / fsc types;"
        "2 for http test_pool_1 /csdb test_sdb_vt / fsc types;"
        "3 for http test_pool_1 /csdb test_e2e2_vt / all fsc _vt types;"
        "4 for http test_pool_4 /csdb test_e2e2_sdb / all fsc types;"
        ,
        choices=(0, 1, 2, 3, 4)
    )

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "server_arch"
    )


SHORT = 'function'
MEDIUM = 'session'


TEST_SERVER_LIFE = 600
""" test server time limit in seconds."""

the_session = requests_retry_session()
the_session.secret_key = 'BAD_SECRET_KEY'


@ pytest.fixture(scope='session')
def clean_board():
    importlib.invalidate_caches()
    # importlib.reload(Classes)
    from fdi.dataset.classes import Classes

    return Classes.mapping


pc = None
# global variable that is initiated by `pc` to be `getConfig`.

#@ pytest.fixture(scope="session")
#def pc():
if 1:
    """ get configuration.

    """
    #global cfg
    #userclasses_file = pc['userclasses']
    from fdi.utils.getconfig import getConfig 
      
    pc = getConfig(force=True)
    # cfg = get_projectclasses(userclasses_file)
    # logger.debug(json.dumps(cfg))
    #return cfg

@ pytest.fixture(scope='session')
def set_ids(pytestconfig):

    cmd = pytestconfig.getoption("--id")
    if cmd == 0:
        csdb_pool_id = 'sv2'  # 'test_csdb_fdi2'
        http_pool_id = 'test_pool_1'
        PTYPES = ('DemoProduct', 'TB', 'TP', 'TC', 'TM', 'SP', 'TCC')
    else:
        __import__("pdb").set_trace()
        
        csdb_pool_id = http_pool_id = PTYPES = None
    return csdb_pool_id, http_pool_id, PTYPES
        
url_c = None


@ pytest.fixture(scope="session")
def urlcsdb(set_ids):
    global url_c

    url_c = '%s://%s:%s%s/%s' % ('http',
                                 pc['cloud_host'],
                                 str(pc['cloud_port']),
                                 pc['cloud_api_base'],
                                 pc['cloud_api_version'])

    return url_c


@ pytest.fixture(scope='session')
def new_user_read_write():
    """
    GIVEN a User model
    https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
    """
    new_user = User(pc['username'], pc['password'], roles='read_write')
    headers = auth_headers(pc['username'], pc['password'])
    return new_user, headers


@ pytest.fixture(scope='session')
def new_user_read_only():
    """
    GIVEN a User model
    https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
    """
    users = getUsers()
    new_user = users[pc['ro_user']]
    headers = auth_headers(pc['ro_user'], password=pc['ro_pass'])

    return new_user, headers


@ pytest.fixture(scope='session')
def userpass():
    auth_user = pc['username']
    auth_pass = pc['password']
    return auth_user, auth_pass

@ pytest.fixture(scope='session')
def userpass_ro():
    auth_user = pc['ro_user']
    auth_pass = pc['ro_pass']
    return auth_user, auth_pass


@ pytest.fixture(scope="module")
def local_pools_dir():
    """ this is a path in the local OS, where the server runs, used to directly access pool server's internals.

    return: has no trailing '/'
    """
    # http server pool
    schm = 'server'

    # basepath = pc['server_local_pools_dir']
    # basepath = PoolManager.PlacePaths[schm]
    # print('WWW ', basepath, pc['api_version'])
    # pools_dir = os.path.join(basepath, pc['api_version'])
    return PoolManager.PlacePaths[schm]

####


def background_app():
    """ if required starts a server in the background. """

    # client side.
    # pool url from a local client
    cschm = 'http'
    aburl = cschm + '://' + PoolManager.PlacePaths[cschm]
    pwdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    pid = os.fork()
    if pid == 0:
        # child process
        # ref https://code.activestate.com/recipes/66012-fork-a-daemon-process-on-unix/
        os.setsid()
        # Redirect standard file descriptors.
        sys.stdin = open('/dev/null', 'r')
        sys.stdout = open('/dev/null', 'w')
        sys.stderr = open('/dev/null', 'w')
        # run server in b/g
        chldlogger = logger
        cmd = shlex.split(RUN_SERVER_IN_BACKGROUND)
        sta = {'command': str(cmd)}
        proc = Popen(cmd, cwd=pwdir, shell=False)
        timeout = TEST_SERVER_LIFE
        try:
            sta['stdout'], sta['stderr'] = proc.communicate(
                timeout=timeout)
            logger.debug(f'###!!! {sta}')
        except TimeoutExpired:
            # https://docs.python.org/3.6/library/subprocess.html?highlight=subprocess#subprocess.Popen.communicate
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            msg = 'PID %d is terminated after pre-set timeout %d sec.' % (
                proc.pid, timeout)
        else:
            msg = 'Successful.' if proc.returncode == 0 else 'killed?'
        sta['stdout'], sta['stderr'] = proc.communicate()
        sta['returncode'] = proc.returncode

        sta['message'] = msg
        logg = "Background live server status: %s." % json.dumps(
            dict((k, lls(v, 1000)) for k, v in sta.items()))
        chldlogger.info(logg)
        with open(BG_SERVER_LOG, 'a') as f:
            f.write(logg)
        assert sta['returncode'] in (
            0, -signal.SIGTERM, -signal.SIGKILL,  signal.SIGHUP), logg
        assert os.path.exists(BG_SERVER_LOG)
        os.system('ls -l '+BG_SERVER_LOG)

        time.sleep(1)  # avoid trouble for pytest
        sys.exit(0)
    else:
        # main process
        # wait for checkserver to return 'live'
        t = 2
        time.sleep(t)
        n = 2
        while checkserver(aburl) != 'live':
            logger.debug('No server yet %d' % n)
            n -= 1
            if n == 0:
                break
            time.sleep(2)
        if n:
            msg = 'Made live local server %d' % pid
        else:
            msg = 'Failed running server PID=%s in background. timeout %dsec.' % (
                str(pid), (n+1)*2)
        logger.info(msg)
        return pid


def checkserver(aburl, times=0):
    """ make sure the server is running when tests start.

    Parameters
    ----------
    time : int
        How many self-calling is this run.
    Return
    ------
    str
        when aburl points to an live server running either
    externally to this test (e.g. by `make runpoolserver`),
    or a server instance by `background_app` fixture
    created on-demand, server_type is set to 'live';
    If no response is returned by `GET`, 'mock'
    is returned; If server response is abnormal,
    'trouble' is returned.
    """

    server_type = None
    # check if data already exists

    try:
        o = getJsonObj(aburl)
        assert o is not None, 'Cannot connect to the server'
        logger.info('Initial server %s response %s' % (aburl, lls(o, 70)))
    except HTTPError as e:
        if e.code == 308:
            logger.info('%s alive. Server response 308' % (aburl))
            server_type = 'live'
        elif e.code == 401:
            logger.info('%s alive. Server response 401' % (aburl))
            server_type = 'live'
        elif e.code == 409:
            __import__("pdb").set_trace()

            logger.info('%s %d initializing or being maintained.' % (aburl, e.code))

            if times < 1:
                time.sleep(5)
                times += 1
                test2 = checkserver(aburl, times)
                msg = 'is XX up after waiting %d s.' 
                if test2 == 'live':
                    logger.info('is finally up after waiting %i s.' % (5*times))
                    server_type = 'live'
                else:
                    logger.info('is not up after waiting %i s.' % (5*times))
                    server_type = test2            
            else:
                server_type = 'mock'
        else:
            # a different code
            logger.warning(aburl + ' is alive. but trouble is ')
            logger.warning(e)
            logger.warning('Live server')
            server_type = 'trouble'
    except (URLError, OSError, socket.timeout) as e:
        logger.info('Not a live server, because %s' % str(e))
        server_type = 'mock'
    else:
        logger.info('Live server')
        server_type = 'live'
    return server_type

    # assert 'measurements' is not None, 'please start the server to refresh.'
    # initialize test data.


# @pytest.fixture(scope=MEDIUM)
# def XXXlive_or_mock( pytestconfig, request):
#     """ Tells absolute base url and common headers to clients to use.

#     Based on ``PoolManager.PlacePaths[scheme]`` where ``scheme`` 
#     is `http` or `https` and auth info from `pnsconfig` from the
#     configuration file and commandline.
# 3
#     e.g. ```'http://0.0.0.0:5000/v0.7/', ('foo', 'bar')```

#        baseurl with no trailing '/' and a string set to 'live' if the
#        server is alive, 'mock' if using Flask's testing lib.

#     """

#     # pool url from a local client
#     aburl = 'http://' + PoolManager.PlacePaths['http']
#     # csci_url = pc['url_aliases']['csdb'].replace('csdb:', 'http:')
#     how_to_run = pytestconfig.getoption("--server")
#     logger.info(f'command line set server running: {how_to_run}')

#     # server_arch: http or csdb    
#     # server_arch = getattr(request, 'param', {}).get('server_arch', None)
#     #server_arch_name
#     yield from prepare_servers(how_to_run, aburl)



def prepare_servers(server_arch, how_to_run, aburl, csci_url, request):
    """  Chooses server type and generate fixture accordingly.

    Returns server url and how it is run according to requested how and measured results.
    Return
    ------
    tuple of strings

    (url, run_method)
    """
    
    print(f'SERVER_ARCH "{server_arch}" {how_to_run}')
    if not server_arch:
        # of test module does not have, make a guess.
        server_arch = ''
        yield None, 'unknown'
    
    elif server_arch == 'http':
        # 'http://' + pc['cloud_host']+'/' +\
        #  pc['cloud_api_base']+'/'+pc['cloud_api_version']+'user/token'
        logger.debug('Check out %s ...' % aburl)
        how_to_run_found = checkserver(aburl)
        if how_to_run_found == 'live':
            if how_to_run == "external":
                yield aburl, how_to_run_found
            elif how_to_run == "mock":
                # we eyiher get our wish has how the server runs, o we get exception.
                logger.warning(
                    'want to get a mocked server but get %s one. Will use mocked' % how_to_run_found)
                yield aburl, how_to_run
            elif how_to_run == "background":
                # we eyiher get our wish has how the server runs, o we get exception.
                logger.warning(
                    'want to get a background server but get %s one. Will use external' % how_to_run_found)
                yield aburl, 'live'
        elif how_to_run_found == "mock" and how_to_run == "mock":
            yield aburl, how_to_run_found
        elif how_to_run_found == "mock" and how_to_run == "background":
            pid = background_app()
            def kill_svr():
                # clean up
                if pid > 0:
                    logger.info(
                        'Killing server PID=%d running in the background.' % pid)
                    kpg = os.killpg(os.getpgid(pid), signal.SIGTERM)
                    logger.info('... killed. rc= %s' % str(kpg))
            request.addfinalizer(kill_svr)

            how_to_run = 'live'
            yield aburl, how_to_run
        else:
            #  req non-mock but either get a mock or a troubled
            raise RuntimeError(
                'want to get a non-mock server but get %s one.' % how_to_run_found)
    else:
        # server_arch == csdb
        if how_to_run in ['background', 'mock']:
            raise ValueError(
                f"'background', 'mock' not possible for {server_arch} server tests running {server_arch}.")

        logger.debug('Check out %s ...' % csci_url)
        how_to_run_found = checkserver(csci_url)

        if how_to_run_found == 'live':
            yield csci_url, 'live'
        else:
            raise RuntimeError('Oops server state '+how_to_run_found)


    
@ pytest.fixture(scope='session')
def mock_app():
    """ A mock app that act like a server to the client.
    """
        
    from fdi.httppool import create_app
    app = create_app(config_object=pc, level=logger.getEffectiveLevel())
    app.config['TESTING'] = True
    with app.app_context():        
        yield app
        # app.

def server2(_pytestconfig, server_arch, request, urlc=None):
    """
    Helper to make `server` and `csdb_server`
    
    """

    # pool url from a local client
    aburl = 'http://' + PoolManager.PlacePaths['http']
    csci_url = urlc
    how_to_run = _pytestconfig.getoption("--server")
    logger.info(f'command line set server running: {how_to_run}')

    if server_arch == 'http':
        yield from prepare_servers(server_arch, how_to_run, aburl, csci_url, request)
        #url, ty = next(prepare_servers(server_arch, how_to_run, aburl, csci_url, request))
        # headers['server_type'] = ty
        #yield url, ty # headers
    elif server_arch == "csdb":
        yield from prepare_servers(server_arch, how_to_run, aburl, csci_url, request) 
        #url, ty = next(prepare_servers(server_arch, how_to_run, aburl, csci_url, request))
        # headers['server_type'] = ty
        #yield url, ty #headers
    else:
        raise ValueError("invalid internal test")


@ pytest.fixture(scope=SHORT)
def server(pytestconfig, set_ids, userpass, mock_app, request):
    """ Server data from r/w user, mock or alive.

    Returns
    -------
    tuple
      baseurl, client, auth, pool (pool name is `http_pool_id`), poolurl, pstore, server_type
    """
    #    yield from server2(pc, pytestconfig, 'http', reuest=request)

    url, server_type = next(server2(pytestconfig, 'http', request=request))
    csdb_pool_id, http_pool_id, PTYPES = set_ids
    
    # register to clean up
    poolurl = url + '/' + http_pool_id
    pstore = ProductStorage()
    pstore.PM.removeAll()

    if server_type == 'mock':
        from werkzeug.datastructures import Authorization
        auth = Authorization(
            "basic", {"username": userpass[0], "password": userpass[1]})
        logger.info('**** mock_app as client *****')
        with mock_app.test_client() as client:
            if 0:
                with mock_app.app_context():
                    mock_app.preprocess_request()
            #yield client
            pstore.register(poolurl=poolurl, client=client, auth=auth)
            # pstore.register(poolname=test_pool.poolname, poolurl=poolurl)
            pool = pstore.getWritablePool(obj=True)  # PublicClientPool(poolurl=url)
            yield url, client, auth, pool, poolurl, pstore, server_type

    else:
        auth = HTTPBasicAuth(*userpass)
        logger.info('**** requests as live-client *****')
        with the_session as live_client:
            #yield live_client
            pstore.register(poolurl=poolurl, client=live_client, auth=auth)
            # ps.register(poolname=test_pool.poolname, poolurl=poolurl)
            # PublicClientPool(poolurl=url)
            pool = pstore.getWritablePool(True)

            yield url, live_client, auth, pool, poolurl, pstore, server_type

@ pytest.fixture(scope='session')
def server_ro(pytestconfig, set_ids, userpass_ro, mock_app, request):
    """ Server data from r/w user, mock or alive.

    """
    #    yield from server2(pc, pytestconfig, 'http', reuest=request)

    url, server_type = next(server2(pytestconfig, 'http', request=request))

    csdb_pool_id, http_pool_id, PTYPES = set_ids

    # register to clean up
    poolurl = url + '/' + http_pool_id
    pstore = ProductStorage()
    pstore.PM.removeAll()

    if server_type == 'mock':
        from werkzeug.datastructures import Authorization
        auth = Authorization(
            "basic", {"username": userpass[0], "password": userpass[1]})
        logger.info('**** mock_app as client *****')
        with mock_app.test_client() as client:
            if 0:
                with mock_app.app_context():
                    mock_app.preprocess_request()
            #yield client
            pstore.register(poolurl=poolurl, client=client, auth=auth)
            # pstore.register(poolname=test_pool.poolname, poolurl=poolurl)
            pool = pstore.getWritablePool(True)  # PublicClientPool(poolurl=url)
            yield url, client, auth, pool, poolurl, pstore, server_type

    else:
        auth = HTTPBasicAuth(*userpass)
        logger.info('**** requests as client *****')
        with the_session as live_client:
            #yield live_client
            pstore.register(poolurl=poolurl, client=live_client, auth=auth)
            # ps.register(poolname=test_pool.poolname, poolurl=poolurl)
            # PublicClientPool(poolurl=url)
            pool = pstore.getWritablePool(True)

            yield url, live_client, auth, pool, poolurl, pstore, server_type

# @ pytest.fixture(scope=SHORT)
# def XXXXcsdb_server(pytestconfig, userpass, request):
#     """ CSDB Server data from r/w user, mock or alive.

#     """

#     #yield from server2(pc, pytestconfig, 'csdb', new_user_read_write,    request=request
             
#     url, server_type = next( server2(pytestconfig, 'csdb', request=request))

#     auth = HTTPBasicAuth(*userpass)
  
#     # register to clean up
#     poolurl = pc['cloud_scheme'] + url[len('csdb'):] + '/storage/' + csdb_pool_id
#     pstore = ProductStorage()
#     pstore.PM.removeAll()

#     logger.info('**** requests as client *****')
#     with the_session as live_client:
#         pstore.register(poolurl=poolurl, client=live_client, auth=auth)
#         # pstore.register(poolname=test_pool.poolname, poolurl=poolurl)
#         pool = pstore.getWritablePool(True)  # PublicClientPool(poolurl=url)
#         assert pool.serverDatatypes

#         yield url, live_client, auth, pool, poolurl, pstore, server_type

@ pytest.fixture(scope='session')
def poolless_csdb_server(pytestconfig, set_ids, userpass, request, urlcsdb):
    """ CSDB Server data from r/w user, mock or alive. This returns an empty ProductStorage.

    """

    #yield from server2(pc, pytestconfig, 'csdb', new_user_read_write,    request=request
    
    url, server_type = next( server2(pytestconfig, 'csdb', request=request, urlc=urlcsdb))

    auth = HTTPBasicAuth(*userpass)
  
    # register to clean up
    poolurl = None
    pstore = ProductStorage()
    #pstore.PM.removeAll()

    logger.info('**** requests as client *****')
    with the_session as live_client:
        poolurl = pool = None
        yield url, live_client, auth, pool, poolurl, pstore, server_type

@ pytest.fixture(scope=SHORT)
def csdb_server(poolless_csdb_server, set_ids):
    """ CSDB Server data from r/w user, mock or alive.

    """

    #yield from server2(pc, pytestconfig, 'csdb', new_user_read_write,    request=request
             
    url, client, auth, pool, poolurl, pstore, server_type = poolless_csdb_server

    csdb_pool_id, http_pool_id, PTYPES = set_ids
    
    # register to clean up
    pstore.PM.removeAll()
    poolurl = pc['cloud_scheme'] + url[len('csdb'):] + '/storage/' + csdb_pool_id

    pstore.register(poolname=csdb_pool_id, poolurl=poolurl,
                    makenew=True, client=client, auth=auth)
    pool = pstore.getWritablePool(True)

    assert pool.serverDatatypes

    yield url, client, auth, pool, poolurl, pstore, server_type



@ pytest.fixture(scope="session")
def request_context(mock_app):
    """create the app and return the request context as a fixture
       so that this process does not need to be repeated in each test
    https://stackoverflow.com/a/66318710
    """

    if mock_app:
        yield mock_app.test_request_context
    else:
        yield None


#@pytest.mark.parametrize("server_arch_name", ALL_ARCHS, indirect=True)
@ pytest.fixture(scope="session")
def client(mock_app, pytestconfig):

    how_to_run = pytestconfig.getoption("--server")

    if how_to_run == 'mock':
        logger.info('**** mock_app as client *****')
        with mock_app.test_client() as client:
            if 0:
                with mock_app.app_context():
                    mock_app.preprocess_request()
            yield client
    else:
        logger.info('**** requests as client *****')
        with the_session as live_client:
            yield live_client
    
        #raise ValueError('Invalid server type: ' + server_type)

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


@ pytest.fixture(scope='session')
def demo_product():
    v = get_demo_product()
    return v, get_related_product()

def make_ps():
    # client = requests_retry_session()

    ps = ProductStorage()
    if PoolManager.size():
        logger.debug("$$$ PM not empty")
    ps.unregisterAll()
    assert ps.isEmpty()
    assert PoolManager.size() == 0

    return ps


def do_clean_csdb(test_pool, url, ps, auth):

    ######
    if dbg_7types:
        tl = test_pool.getDataType(substrings='testproducts')
        print('+'*21, len(tl), tl)

    test_pool.wipe()
    pname = test_pool._poolname

    #######
    if dbg_7types:
        tl = test_pool.getDataType(substrings='testproducts')
        print('>'*21, len(tl), tl)

    assert pname in ps._pools
    # assert pname in PoolManager.getMap()

    assert test_pool.isEmpty()

    ####
    if dbg_7types:
        tl = test_pool.getDataType(substrings='testproducts')
        print('.'*21, len(tl), tl)

    # unregister. this will set test_pool.serverDatatypes to None
    ps.unregister(pname)
    assert not ps.PM.isLoaded(pname)
    assert ps.isEmpty()
    assert test_pool.serverDatatypes == []

    # re-register the wiped pool
    ps.register(poolurl=url, client=the_session, auth=auth)
    assert ps.PM.isLoaded(pname)
    test_pool = ps.getWritablePool(True)

    assert test_pool.serverDatatypes
    if 0 and hasattr(test_pool, 'serverDatatypes'):
        logger.info(
            f"@{pname}.serverDatatypes={sorted(test_pool.serverDatatypes)}")

    return test_pool, url, ps


@ pytest.fixture(scope=SHORT)
def clean_csdb_fs(csdb_server):
    """ fuction-scope verssion of clean_csdb """
    url, client, auth, test_pool, poolurl, pstore, server_type = csdb_server
    return do_clean_csdb(test_pool, poolurl, pstore, auth=auth)


@ pytest.fixture(scope="session")
def clean_csdb_ro(csdb_server_ro):
    url, client, auth, test_pool, poolurl, pstore, server_type = csdb_server_ro
    return do_clean_csdb(test_pool, poolurl, pstore, auth=auth)


@ pytest.fixture(scope=SHORT)
def new_csdb(csdb_server, set_ids):
    logger.debug('wipe cdb_new. {purl}')
    urlc, client, auth, test_pool, poolurl, pstore, server_type = csdb_server
    csdb_pool_id, http_pool_id, PTYPES = set_ids    
    url = pc['cloud_scheme'] + \
        urlc[len('csdb'):] + '/' + csdb_pool_id + str(int(time.time()))
    # url = pc['cloud_scheme'] + urlc[len('csdb'):] + '/' + csdb_pool_id
    ps = make_ps()
    ps.register(poolurl=url, client=the_session, auth=auth)
    pool = ps.getWritablePool(True)  # PublicClientPool(poolurl=url)
    poolname = pool._poolname
    assert ps.PM.isLoaded(poolname)
    if hasattr(pool, 'serverDatatypes'):
        logger.debug(f"{poolname}.serverDatatypes={pool.serverDatatypes}")
    if dbg_7types:
        tl = pool.getDataType(substrings='testproducts')
        print('.'*21, len(tl), tl)

    yield pool, url, ps
    ps.unregister(pool)
    ps.PM.removeAll()


# @ pytest.fixture(scope='session')
# def XXXXcsdb( client, auth, urlcsdb):
    
#     url = pc['cloud_scheme'] + urlcsdb[len('csdb'):] + '/' + csdb_pool_id

#     # register to clean up
#     ps = ProductStorage()
#     ps.PM.removeAll()

#     ps.register(poolurl=url, client=client, auth=auth)
#     # ps.register(poolname=test_pool.poolname, poolurl=poolurl)
#     test_pool = ps.getWritablePool(True)  # PublicClientPool(poolurl=url)

#     assert test_pool.serverDatatypes

#     return test_pool, url, ps


# @ pytest.fixture(scope='session')
# def XXXXcsdb_client( urlcsdb, auth):
#     #urlupload = urlcsdb + '/datatype/upload'
#     #urldelete = urlcsdb + '/datatype/'
#     #urllist = urlcsdb + '/datatype/list'
#     client = the_session
#     headers = client.headers
#     client.auth = auth
#     headers = auth_headers(pc['cloud_user'], pc['cloud_pass'],
#                            headers)
#     client.headers.update(headers)
#     yield urlcsdb, client


# @ pytest.fixture(scope='session')
# def auth(userpass, request):
#     """ returns auth object in `HTTPBasicAuth` (live server) or `Authorization` (mock server).
#     """
#     __import__("pdb").set_trace()

#     a, hdr = server
#     server_type = hdr['server_type']

#     if server_type == 'live':
#         return HTTPBasicAuth(*userpass)
#     else:
#         from werkzeug.datastructures import Authorization
#         return Authorization(
#             "basic", {"username": userpass[0], "password": userpass[1]})


@ pytest.fixture(scope=SHORT)
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


@ pytest.fixture(scope=SHORT)
def tmp_remote_storage_no_wipe(server, set_ids):
    """ temporary servered pool in a local PoolManager, with module scope """
    aburl, client, auth, pool, poolurl, pstore, server_type = server

    csdb_pool_id, http_pool_id, PTYPES = set_ids

    poolid = http_pool_id

    ps = ProductStorage(poolname=poolid, poolurl=aburl + '/' + poolid,
                        client=client, auth=auth)
    pool = ps.getPool(poolid)
    assert issubclass(ps.getPool(poolid).client.__class__,
                      (requests.Session, FlaskClient))
    yield ps, pool


@ pytest.fixture(scope=SHORT)
def tmp_remote_storage(tmp_remote_storage_no_wipe):
    """ temporary servered with pools and poolManager cleared  """
    ps, pool = tmp_remote_storage_no_wipe

    ps._pools.clear()
    ps.PM.removeAll(include_read_only=True)
    ps.register(pool=pool)
    yield ps


@ pytest.fixture(scope="session")
def tmp_prod_types(set_ids):
    """ classe of temporary prods with sesion scope """
    csdb_pool_id, http_pool_id, PTYPES = set_ids
    ptypes = []
    pobjs = []
    for n in PTYPES:
        cls = Class_Look_Up[n]
        pobjs.append(cls())
        ptypes.append(cls)
    return ptypes, pobjs


PRD0_ser = get_demo_product('test-product-0: Demo_Product')
array_ser = Class_Look_Up['ArrayDataset']()


@ pytest.fixture(scope='session')
def tmp_prods(tmp_prod_types):
    """ instances of temporary prods with function scope """
    types, seri = tmp_prod_types
    while True:
        prds = [copy.deepcopy(PRD0_ser)]
        for i, n in enumerate(seri):
            if i == 0:
                continue
            p = copy.deepcopy(n)
            p.description = ('test-product-%d: %s' % (i, n))
            if p.type == 'TB':
                p.meta['pint'] = NumericParameter(
                    value=11, valid={(0, 9): 'k'})
            a = copy.deepcopy(array_ser)
            a.data = [[time.time(), n], 's']
            p['the_data'] = a
            prds.append(p)
        logger.debug("Made products: %s" %
                     str(list((p.description, id(p)) for p in prds)))
        res = tuple(prds)
        return res


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
        pool.wipe()
        prd = prds[i]
        prd.description = 'lone prod in '+poolid
        ref = ps.save(prd, tag=tag)
        lst.append((pool, prd, ref, tag))
    return lst


@ pytest.fixture(scope=SHORT)
def tmp_pools(server,  tmp_prods):
    """ generate n pools.

    Return
    ------
    list
        list of tuples containing `ProductPool`, `BaseProduct`, `ProductRef`, `str` for each pool.

"""
    aburl, client, auth, pool, poolurl, pstore, server_type = server

    lst = gen_pools(aburl, auth, client, list(tmp_prods))
    return lst


@ pytest.fixture(scope=SHORT)
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


# @ pytest.fixture(scope=SHORT)
# def XXXexisting_pools(tmp_pools):
#     """ return n existing pools.

#     Return
#     ------
#     list
#         list of tuples containing `ProductPool`, `BaseProduct`, `ProductRef`, `str` for each pool.

# """
#     pools = [p[0] for p in tmp_pools]
#     print("get existing pools:", [p.poolname for p in pools])
#     return pools


@ pytest.fixture(scope='session')
def t_package():
    """
    A names package with data
    ├── Makefile
    ├── resource3.txt
    ├── setup.py
    ├── standalone.py
    └── testpackage
        ├── one
        │   ├── module1.py
        │   ├── resource1
        │   │   └── resource1.1.txt
        │   ├── resource1.txt
        │   └── __init__.py
        └── two
            ├── four
            │   ├── five
            │   │   └── resource5.jsn
            │   ├── resource4.csv
            │   └── __init__.py
            ├── resource2.1.jsn
            ├── resource2.2.json
            ├── resource2.txt
            └── __init__.py
    """
    try:
        import testpackage
    except ModuleNotFoundError as e:
        try:
            #__import__("pdb").set_trace()
            #  make clean-tpkg;
            os.system(
                '(pip uninstall testpackage -y; cd tests/resources/testpackage; make install-tpkg PYEXE=python3) 2>&1| tee /tmp/testpackage.log')
            # 'python3.8 -c "import sys; print(sys.path)"
            # 'make  pip show testpackage;
            sys.path.insert(0, '/tmp')
            import testpackage
        except Exception as e:
            assert False, 'cannot test find_all_files from package.'+str(e)
        logger.debug('Installed and imported testpackage.')

    yield testpackage

    os.system('cd tests/resources/testpackage;make clean-tpkg')

@ pytest.fixture(scope=SHORT)
def demo_TableDataset():

    # http://herschel.esac.esa.int/hcss-doc-15.0/load/hcss_drm/ia/dataset/demo/TableDataset.py
    ELECTRON_VOLTS = 'eV'
    SECONDS = 'sec'
    # create dummy numeric data:
    # t=Double1d.range(100)
    # e=2*t+100
    t = [x * 1.0 for x in range(10)]
    e = [2 * x + 10 for x in t]

    # creating a table dataset to hold the quantified data
    table = TableDataset(description="Example table")
    table["Time"] = Column(data=t, unit=SECONDS)
    table["Energy"] = Column(data=e, unit=ELECTRON_VOLTS)

    # alternative Column creation:
    c = Column()
    c.data = t
    c.unit = SECONDS
    table["Time1"] = c

    # alternative Column creation using Java syntax:
    c1 = Column()
    c1.setData(t)
    c1.setUnit(SECONDS)
    table.addColumn("Time2", c1)

    t1 = table.copy()
    t2 = table.copy()
    assert table.getColumnCount() == 4
    assert t1.getColumnCount() == 4
    # removing a column by name:
    t1.removeColumn("Time2")
    assert t1.getColumnCount() == 3

    # removing a column by index (removing "Time1")
    # NOTE: indices start at 0!
    t2.removeColumn(3)
    assert t1 == t2

    # adding meta:
    table.meta["Foo"] = Parameter(value="Bar", description="Bla bla")

    # table access:
    print(table)  # summary
    print(table.__class__)  # type
    print(table.rowCount)
    print(table.columnCount)

    # meta data access:
    print(table.meta)
    print(table.meta["Foo"])

    # column access:
    print(table["Time"])
    print(table["Time"].data)
    print(table["Time"].unit)

    return table

@ pytest.fixture(scope=SHORT)
def demo_CompositeDataset():
    """ http://herschel.esac.esa.int/hcss-doc-15.0/load/hcss_drm/ia/dataset/demo/CompositeDataset.py
    """
    # creating a composite dataset.For this demo, we use empty datasets only.
    c = CompositeDataset()
    c["MyArray"] = ArrayDataset()  # adding an array
    c["MyTable"] = TableDataset()  # adding a table
    c["MyComposite"] = CompositeDataset()  # adding a composite as child

    # alternative Java syntax:
    c.set("MyArray", ArrayDataset())
    c.set("MyTable", TableDataset())
    c.set("MyComposite", CompositeDataset())

    # adding two children to a "MyComposite":
    c["MyComposite"]["Child1"] = ArrayDataset()
    assert issubclass(c["MyComposite"]["Child1"].__class__, ArrayDataset)
    c["MyComposite"]["Child2"] = TableDataset()
    c["MyComposite"]["Child3"] = TableDataset()

    # replace array "Child1" by a composite:
    c["MyComposite"]["Child1"] = CompositeDataset()
    assert issubclass(c["MyComposite"]["Child1"].__class__, CompositeDataset)

    # remove3 table "Child3"
    assert c["MyComposite"].containsKey("Child3") == True
    c["MyComposite"].remove("Child3")
    assert c["MyComposite"].containsKey("Child3") == False

    # report the number of datasets in this composite
    print(c.size())
    assert c.size() == 3

    # print(information about this variable ...
    # <class 'fdi.dataset.dataset.CompositeDataset'>
    # {meta = "MetaData[]", _sets = ['MyArray', 'MyTable', 'MyComposite']}
    print(c.__class__)
    print(c)

    # ... print(information about child "MyComposite", and ...
    # <class 'fdi.dataset.dataset.CompositeDataset'>
    # {meta = "MetaData[]", _sets = ['Child1', 'Child2']}
    print(c["MyComposite"].__class__)
    print(c["MyComposite"])

    # ... that of a nested child ...
    # <class 'fdi.dataset.dataset.CompositeDataset'>
    # {meta = "MetaData[]", _sets = []}
    print(c["MyComposite"]["Child1"].__class__)
    print(c["MyComposite"]["Child1"])

    # ... or using java syntax to access Child1:
    # {meta = "MetaData[]", _sets = []}
    print(c.get("MyComposite").get("Child1"))

    # or alternatively:
    # <class 'fdi.dataset.dataset.CompositeDataset'>
    # {meta = "MetaData[]", _sets = ['Child1', 'Child2']}
    child = c["MyComposite"]
    print(child.__class__)
    print(child)

    return c

