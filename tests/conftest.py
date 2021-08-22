# -*- coding: utf-8 -*-

from fdi.pal.poolmanager import PoolManager
from fdi.pns.jsonio import getJsonObj, postJsonObj, putJsonObj, commonheaders
from fdi.utils.common import lls
from fdi.pns.jsonio import auth_headers
from fdi.httppool.model.user import User

import pytest
import importlib
import base64
import copy
from urllib.error import HTTPError
import os
import requests
import logging
from urllib.error import HTTPError, URLError
from flask import current_app


logger = logging.getLogger(__name__)


@pytest.fixture(scope='package')
def clean_board():
    importlib.invalidate_caches()
    # importlib.reload(Classes)
    from fdi.dataset.classes import Classes
    global Class_Look_Up
    # importlib.reload(Class_Look_Up)
    from fdi.dataset.deserialize import Class_Look_Up
    Classes.updateMapping()

    return Classes


@pytest.fixture(scope="package")
def getConfig(clean_board):
    from fdi.utils.getconfig import getConfig as getc
    return getc


@pytest.fixture(scope="package")
def pc(getConfig):
    """ get configuration.

    """
    return getConfig()


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
            logger.info(e)
    except URLError as e:
        logger.info('Not a live server, because %s' % str(e))
        server_type = 'mock'
    else:
        logger.info('Live server')
        server_type = 'live'
    return server_type

    # assert 'result' is not None, 'please start the server to refresh.'
    # initialize test data.


@pytest.fixture(scope="module")
def new_user_read_write():
    """
    GIVEN a User model
    https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
    """
    new_user = User('rww', 'FlaskIsAwesome', 'read_write')
    return new_user


@pytest.fixture(scope="module")
def new_user_read_only():
    """
    GIVEN a User model
    https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
    """
    new_user = User('aas', 'FlaskIsAwesome', 'read_only')
    return new_user


@pytest.fixture(scope="module")
def live_or_mock_server(pc):
    """ Prepares server absolute base url and common headers for clients to use.

    Based on ``PoolManager.PlacePaths[scheme]`` where ``scheme`` is `http` or `https` and auth info from `pnsconfig` from the configuration file and commandline.

    e.g. ```'http://0.0.0.0:5000/v0.7/', ('foo', 'bar')```

    return: url has no trailing '/'

    """
    server_type = None

    testname = 'SVOM'
    # client side.
    # pool url from a local client
    cschm = 'http'
    aburl = cschm + '://' + PoolManager.PlacePaths[cschm]
    # aburl='http://' + pc['node']['host'] + ':' + \
    #    str(pc['node']['port']) + pc['baseurl']
    server_type = checkserver(aburl)
    headers = copy.copy(commonheaders)
    yield aburl, headers, server_type
    del aburl, headers
    server_type = None


@pytest.fixture(scope="module")
def server(live_or_mock_server, new_user_read_write):
    """ Server data from r/w user, alive.

    """
    aburl, headers, ty = live_or_mock_server
    user = new_user_read_write
    headers = auth_headers(user.username, user.password)
    headers['server_type'] = ty
    yield aburl, headers
    del aburl, headers


@pytest.fixture(scope="package")
def userpass(pc):
    auth_user = pc['auth_user']
    auth_pass = pc['auth_pass']
    return auth_user, auth_pass


@pytest.fixture
def local_pools_dir(pc):
    """ this is a path in the local OS, where the server runs, used to directly access pool server's internals.

    return: has no trailing '/'
    """
    # http server pool
    schm = 'server'

    #basepath = pc['server_local_pools_dir']
    basepath = PoolManager.PlacePaths[schm]
    local_pools_dir = os.path.join(basepath, pc['api_version'])
    return local_pools_dir


@pytest.fixture(scope="module")
def mock_server(live_or_mock_server):
    """ Prepares server configuredand alive

    """
    aburl, headers, server_type = live_or_mock_server
    # assert server_type == 'mock', 'must have a mock server. Not ' + \
    #    str(server_type)
    yield aburl, headers
    del aburl, headers


@pytest.fixture(scope="module")
def mock_app(mock_server, project_app):
    app = project_app
    app.config['TESTING'] = True
    with app.app_context():
        yield app


@pytest.fixture(scope="module")
def server_app(live_or_mock_server, project_app):
    a, h, server_type = live_or_mock_server
    if server_type != 'mock':
        yield None
    else:
        app = project_app
        app.config['TESTING'] = True
        with app.app_context():
            yield app


@pytest.fixture(scope="module")
def request_context(mock_app):
    """create the app and return the request context as a fixture
       so that this process does not need to be repeated in each test
    https://stackoverflow.com/a/66318710
    """

    return mock_app.test_request_context


@pytest.fixture(scope="module")
def client(server_app, mock_app):
    if server_app == None:
        yield requests
    else:
        with mock_app.test_client() as client:
            with mock_app.app_context():
                # mock_app.preprocess_request()
                assert current_app.config["ENV"] == "production"
            yield client
