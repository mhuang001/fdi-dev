# -*- coding: utf-8 -*-

from fdi.pal.poolmanager import PoolManager
from fdi.pns.jsonio import getJsonObj, postJsonObj, putJsonObj, commonheaders
from fdi.utils import getconfig
from fdi.utils.common import lls

import pytest
import copy
import os
import base64
import logging
from urllib.error import HTTPError
logger = logging.getLogger(__name__)


@pytest.fixture(scope="package")
def pc():
    """ get configuration.

    """
    pc = getconfig.getConfig()
    return pc


def checkserver(aburl):
    """ make sure the server is running when tests start
    """

    # check if data already exists
    try:
        o = getJsonObj(aburl)
        assert o is not None, 'Cannot connect to the server'
        logger.info('%s initial server response %s' % (aburl, lls(o, 100)))
    except HTTPError as e:
        if e.code == 308:
            logger.info('%s alive. initial server response 308' % (aburl))
        else:
            raise
    # assert 'result' is not None, 'please start the server to refresh.'
    # initialize test data.


@pytest.fixture(scope="package")
def setup(pc):
    """ Prepares server absolute base url and common headers fr clients to use.

    Based on ``PoolManager.PlacePaths[scheme]`` where ``scheme`` is `http` or `https` and auth info from `pnsconfig` from the configuration file and commandline.

    e.g. ```'http://0.0.0.0:5000/v0.7/', ('foo', 'bar')```

    return: url has no trailing '/'

    """
    testname = 'SVOM'
    # client side.
    # pool url from a local client
    cschm = 'http'
    aburl = cschm + '://' + PoolManager.PlacePaths[cschm]
    # aburl='http://' + pc['node']['host'] + ':' + \
    #    str(pc['node']['port']) + pc['baseurl']
    checkserver(aburl)
    up = bytes((pc['node']['username'] + ':' +
                pc['node']['password']).encode('ascii'))
    code = base64.b64encode(up).decode("ascii")
    headers = copy.copy(commonheaders)
    headers.update({'Authorization': 'Basic %s' % (code)})
    del up, code
    yield aburl, headers
    del aburl, headers


@pytest.fixture
def local_pools_dir(pc):
    """ this is a path in the local OS, where the server runs.

    the path is used to directly access pool server's internals.

    return: has no trailing '/'
    """
    # http server pool
    schm = 'server'

    #basepath = pc['server_local_pools_dir']
    basepath = PoolManager.PlacePaths[schm]
    local_pools_dir = os.path.join(basepath, pc['api_version'])
    return local_pools_dir


@pytest.fixture(scope="package")
def userpass(pc):
    auth_user = pc['auth_user']
    auth_pass = pc['auth_pass']
    return auth_user, auth_pass
