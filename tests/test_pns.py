# -*- coding: utf-8 -*-

from multiprocessing import Process, Pool, TimeoutError
from fdi.dataset.eq import deepcmp
from fdi.dataset.dataset import GenericDataset
from fdi.dataset.arraydataset import ArrayDataset
from fdi.dataset.deserialize import deserialize
from fdi.dataset.numericparameter import NumericParameter
from fdi.dataset.product import Product
from fdi.dataset.serializable import serialize
from fdi.dataset.odict import ODict
from fdi.utils.options import opt
from fdi.utils.getconfig import getConfig


from fdi.pns.jsonio import getJsonObj, postJsonObj, putJsonObj, commonheaders
from fdi.dataset.classes import Classes

import asyncio
import aiohttp
import pytest
import sys
import base64
from urllib.request import pathname2url
import requests
import os
import pkg_resources
import copy
import time
from collections.abc import Mapping

# This is to be able to test w/ or w/o installing the package
# https://docs.python-guide.org/writing/structure/
from .pycontext import fdi

Classes.updateMapping()


@pytest.fixture(scope='module')
def importserver():
    """ Prepare getconfig.CONFIG then import pns_server.

    """
    from fdi.pns import pns_server
    return pns_server


def setuplogging():
    import logging.config
    import logging
    from . import logdict

    # create logger
    logging.config.dictConfig(logdict.logdict)
    logging.getLogger("requests").setLevel(logging.WARN)
    logging.getLogger("urllib3").setLevel(logging.WARN)
    logging.getLogger("filelock").setLevel(logging.WARN)
    return logging


logging = setuplogging()
logger = logging.getLogger(__name__)


# default configuration is read and can be superceded
# by ~/.config/pnslocal.py, which is also used by the local test server
# run by scrupt startserver.

pc = getConfig()
logger.setLevel(pc['logginglevel'])
logger.debug('logging level %d' % (logger.getEffectiveLevel()))

if 0:
    import pytest

    # @pytest.fixture(scope="module")
    def runserver():
        from fdi.pns.runflaskserver import app
        app.run(host='127.0.0.1', port=5000,
                threaded=False, debug=verbose, processes=5)

        return smtplib.SMTP("smtp.gmail.com", 587, timeout=5)


# last timestamp/lastUpdate
lupd = 0


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


@pytest.fixture
def getpnsconfig(setup):
    ''' gets and compares pnsconfig remote and local
    '''
    logger.debug('get pnsconfig')
    aburl, headers = setup
    o = getJsonObj(aburl + '/' + 'pnsconfig', debug=False)
    issane(o)
    r = o['result']
    # , deepcmp(r['scripts'], pc['scripts'])
    assert r['scripts'] == pc['scripts']
    return r


def checkContents(cmd, filename, aburl, headers):
    """ checks a GET commands return matches contents of a file.
    """
    o = getJsonObj(aburl + '/' + cmd)
    issane(o)
    with open(filename, 'r') as f:
        result = f.read()
    assert result == o['result'], o['message']


def test_serverinitPTS(importserver):
    """ server unit test for put init. 

    this runs the runPTS script, and is in conflict with put testinit, as this will condition the server for running the PTS, not suitable for running other tests.
    """
    ret, sta = pns_server.initPTS(None)
    check0result(ret, sta)


def test_putinit(puttestinit):
    """ calls the default pnsconfig['scripts']['init'] script.

    this runs the runPTS script, and is in conflict with put testinit, as this will condition the server for running the PTS, not suitable for running other tests.
    """

    aburl, headers = puttestinit
    d = {'timeout': 5}
    o = putJsonObj(aburl +
                   '/init',
                   d,
                   headers=headers)
    issane(o)
    check0result(o['result'], o['message'])

# this will condition the server for testing


def test_servertestinit(importserver):
    """ server unit test for put testinit """
    ret, sta = pns_server.testinit(None)
    check0result(ret, sta)


# this will condition the server for testing
@pytest.fixture
def puttestinit(setup):
    """ Prepares for the rest of the tests.  Renames the 'init' 'config' 'run' 'clean' scripts to "*.save" and points it to the '.ori' scripts.
    """

    aburl, headers = setup
    d = {'timeout': 5}
    o = putJsonObj(aburl +
                   '/testinit',
                   d,
                   headers=headers)
    issane(o)
    check0result(o['result'], o['message'])
    yield aburl, headers


def test_getinit(setup):
    ''' compare. server side initPTS contens with the local  default copy
    '''
    logger.debug('get initPTS')
    c = 'init'
    n = pc['scripts'][c][0].rsplit('/', maxsplit=1)[1]
    fn = pkg_resources.resource_filename("fdi.pns.resources", n)
    checkContents(c, fn + '.ori', *setup)


def test_getrun(setup):
    ''' compare. server side run contens with the local default copy
    '''
    logger.debug('get run')
    c = 'run'
    n = pc['scripts'][c][0].rsplit('/', maxsplit=1)[1]
    fn = pkg_resources.resource_filename("fdi.pns.resources", n)
    checkContents(c, fn + '.ori', *setup)


def test_putconfigpns(puttestinit, getpnsconfig):
    """ send signatured pnsconfig and check.
    this function is useless for a stateless server
    """
    aburl, headers = puttestinit
    t = getpnsconfig
    t['testing'] = 'yes'
    d = {'timeout': 5, 'input': t}
    # print(nodetestinput)
    o = putJsonObj(aburl +
                   '/pnsconf',
                   d,
                   headers=headers)
    # put it back not to infere other tests
    del t['testing']
    d = {'timeout': 5, 'input': t}
    p = putJsonObj(aburl +
                   '/pnsconf',
                   d,
                   headers=headers)

    issane(o)
    assert o['result']['testing'] == 'yes', o['message']
    assert 'testing' not in pc, str(pc)
    issane(p)
    assert 'testing' not in p['result']


def makeposttestdata():
    a1 = 'a test sNumericParameter'
    a2 = 1
    a3 = 'second'
    v = NumericParameter(description=a1, value=a2, unit=a3)
    i0 = 6
    i1 = [[1, 2, 3], [4, 5, i0], [7, 8, 9]]
    i2 = 'ev'                 # unit
    i3 = 'img1'  # description
    image = ArrayDataset(data=i1, unit=i2, description=i3)
    x = Product(description="test post input product")
    x.set('testdataset', image)
    x.meta['testparam'] = v
    return ODict({'creator': 'me', 'rootcause': 'server test',
                  'input': x})


def checkpostresult(o, nodetestinput):

    p = o['result']
    assert issubclass(p.__class__, Product), (p.__class__)
    # creator rootcause
    # print('p.toString()' + p.toString())
    assert p.meta['creator'].value == nodetestinput['creator']
    assert p.rootCause == nodetestinput['rootcause']
    # input data
    input = nodetestinput['input']
    pname, pv = list(input.meta.items())[0]
    dname, dv = list(input.getDataWrappers().items())[0]
    # compare with returened data
    assert p.meta[pname] == pv
    assert p[dname] == dv


def test_post(setup):
    ''' send a set of data to the server and get back a product with
    properties, parameters, and dataset containing those in the input
    '''
    logger.debug('POST testpipeline node server')

    aburl, headers = setup
    nodetestinput = makeposttestdata()
    # print(nodetestinput)
    o = postJsonObj(aburl +
                    '/testcalc',
                    nodetestinput,
                    headers=headers)
    issane(o)
    checkpostresult(o, nodetestinput)


def makeruntestdata():
    """ the input has only one product, which has one dataset,
    which has one data item -- a string that is the name
    """
    x = Product(description="hello world pipeline input product")
    x['theName'] = GenericDataset(
        data='stranger', description='input. the name')
    return x


def checkrunresult(p, msg, nodetestinput):

    assert issubclass(p.__class__, Product), str(p) + ' ' + str(msg)

    # creator rootcause
    # print('p.toString()' + p.toString())
    assert p.meta['creator'].value == nodetestinput['creator']
    assert p.rootCause == nodetestinput['rootcause']
    # input data
    input = nodetestinput['input']
    answer = 'hello ' + input['theName'].data + '!'
    assert p['theAnswer'].data[:len(answer)] == answer


def test_servertestrun(importserver):
    ''' send a product that has a name string as its data
    to the server "testrun" routine locally installed with this
    test, and get back a product with
    a string 'hello, $name!' as its data
    '''
    logger.debug('POST test for pipeline node server "testrun": hello')

    test_servertestinit()

    x = makeruntestdata()
    # construct the nodetestinput to the node
    nodetestinput = ODict({'creator': 'me', 'rootcause': 'server test',
                           'input': x})
    js = serialize(nodetestinput)
    logger.debug(js[:160])
    o, msg = pns_server.testrun(js)
    # issane(o) is skipped
    checkrunresult(o, msg, nodetestinput)


def test_testrun(puttestinit):
    ''' send a product that has a name string as its data
    to the server and get back a product with
    a string 'hello, $name!' as its data
    '''
    logger.debug('POST test for pipeline node server: hello')
    aburl, headers = puttestinit

    x = makeruntestdata()
    # construct the nodetestinput to the node
    nodetestinput = ODict({'creator': 'me', 'rootcause': 'server test',
                           'input': x})
    # print(nodetestinput)
    o = postJsonObj(aburl +
                    '/testrun',
                    nodetestinput,
                    headers=headers)
    issane(o)
    checkrunresult(o['result'], o['message'], nodetestinput)


def test_deleteclean(puttestinit):
    ''' make input and output dirs and see if DELETE removes them.
    '''
    logger.debug('delete cleanPTS')
    aburl, headers = puttestinit
    # make sure input and output dirs are made
    test_testrun(puttestinit)
    o = getJsonObj(aburl + '/input')
    issane(o)
    assert o['result'] is not None
    o = getJsonObj(aburl + '/output')
    issane(o)
    assert o['result'] is not None

    url = aburl + '/clean'
    try:
        r = requests.delete(url, headers=headers, timeout=15)
        stri = r.text
    except Exception as e:
        logger.error("Give up DELETE " + url + ' ' + str(e))
        stri = None
    o = deserialize(stri)
    issane(o)
    assert o['result'] is not None, o['message']
    o = getJsonObj(aburl + '/input')
    issane(o)
    assert o['result'] is None
    o = getJsonObj(aburl + '/output')
    issane(o)
    assert o['result'] is None


def test_mirror(setup):
    ''' send a set of data to the server and get back the same.
    '''
    logger.debug('POST testpipeline node server')
    aburl, headers = setup
    nodetestinput = makeposttestdata()
    # print(nodetestinput)
    o = postJsonObj(aburl +
                    '/echo',
                    nodetestinput,
                    headers=headers)
    # print(o)
    issane(o)
    r = deepcmp(o['result'], nodetestinput)
    assert r is None, r


def test_serversleep(importserver):
    """
    """
    s = '1.5'
    tout = 2
    now = time.time()
    re, st = pns_server.dosleep({'timeout': tout}, s)
    d = time.time() - now - float(s)
    assert re == 0, str(re)
    assert d > 0 and d < 0.5
    #print('dt=%f re=%s state=%s' % (d, str(re), str(st)))
    now = time.time()
    # let it timeout
    tout = 1
    re, st = pns_server.dosleep({'timeout': tout}, s)
    d = time.time() - now - tout
    assert re < 0
    assert d > 0 and d < float(s) - tout
    print('dt=%f re=%s state=%s' % (d, str(re), str(st)))


def test_sleep(setup):
    """
    """
    aburl, headers = setup
    s = '1.7'
    tout = 2
    now = time.time()
    o = postJsonObj(aburl +
                    '/sleep/' + s,
                    {'timeout': tout},
                    headers=headers)
    d = time.time() - now - float(s)
    # print(o)
    issane(o)
    re, st = o['result'], o['message']
    assert re == 0, str(re)
    assert d > 0 and d < 0.5
    #print('deviation=%f re=%s state=%s' % (d, str(re), str(st)))
    # let it timeout
    tout = 1
    now = time.time()
    o = postJsonObj(aburl +
                    '/sleep/' + s,
                    {'timeout': tout},
                    headers=headers)
    d = time.time() - now - tout
    # print(o)
    issane(o)
    re, st = o['result'], o['message']
    #print('deviation=%f re=%s state=%s' % (d, str(re), str(st)))
    assert re < 0
    assert d > 0 and d < float(s) - tout


def info(title):
    print(title)
    print('module name:' + __name__)
    if hasattr(os, 'getppid'):  # only available on Unix
        print('parent process: %d' % (os.getppid()))
    print('process id: ' + str(os.getpid()))
    print(time.time())


def nap(t, d, aburl, headers):
    info(t)
    time.sleep(d)
    s = str(t)
    tout = 5
    o = postJsonObj(aburl +
                    '/sleep/' + s,
                    {'timeout': tout},
                    headers=headers
                    )
    # print('nap ' + str(time.time()) + ' ' + str(s) + ' ' + str(o)
    return o


async def napa(t, d, aburl, headers):
    # info(t)
    asyncio.sleep(d)
    s = str(t)
    tout = 11
    o = None
    js = serialize({'timeout': tout})
    async with aiohttp.ClientSession() as session:
        async with session.post(aburl +
                                '/sleep/' + s,
                                data=js,
                                headers=headers
                                ) as resp:
            # print(resp.status)
            stri = await resp.text()
    o = deserialize(stri)
    #print('nap ' + str(time.time()) + ' ' + str(s) + ' ' + str(o))
    return o


def test_lock(setup):
    """ when a pns is busy with any commands that involves executing in the $pnshome dir the execution is locked system-wide with a lock-file .lock. Any attempts to execute a shell command when the lock is in effect will get a 409.
    """

    tm = 3
    if 0:
        with Pool(processes=4) as pool:
            res = pool.starmap(nap, [(tm, 0, aburl, headers),
                                     (0.5, 0.5, *setup)])
    if 0:
        # does not work
        import threading
        try:
            threading.Thread(target=nap(tm, 0, aburl, headers))
            threading.Thread(target=nap(0.5, 0.5, *setup))
        except Exception as e:
            print("Error: unable to start thread " + str(e))
        time.sleep(tm + 2)
    if 1:
        loop = asyncio.get_event_loop()
        tasks = [asyncio.ensure_future(napa(tm, 0, *setup)),
                 asyncio.ensure_future(napa(0.5, 0.5, *setup))]
        taskres = loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
        res = [f.result() for f in [x for x in taskres][0]]

    # print(res)
    if issubclass(res[0]['message'].__class__, Mapping):
        r1, r2 = res[0], res[1]
    else:
        r2, r1 = res[0], res[1]
    assert r1['result'] == 0, str(res)
    assert '409' in r2['message']


if __name__ == '__main__':
    now = time.time()
    node = pc['node']
    # Get username and password and host ip and port.
    ops = [
        {'long': 'help', 'char': 'h', 'default': False, 'description': 'print help'},
        {'long': 'verbose', 'char': 'v', 'default': False,
            'description': 'print info'},
        {'long': 'username=', 'char': 'u',
            'default': node['username'], 'description':'user name/ID'},
        {'long': 'password=', 'char': 'p',
            'default': node['password'], 'description':'password'},
        {'long': 'host=', 'char': 'i',
            'default': node['host'], 'description':'host IP/name'},
        {'long': 'port=', 'char': 'o',
            'default': node['port'], 'description':'port number'}
    ]
    out = opt(ops)
    verbose = out[1]['result']
    for j in range(2, 6):
        n = out[j]['long'].strip('=')
        node[n] = out[j]['result']

    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.debug('logging level %d' % (logger.getEffectiveLevel()))

    t = 8

    if t == 7:
        # test_lock()
        # asyncio.AbstractEventLoop.set_debug()
        loop = asyncio.get_event_loop()
        tasks = [asyncio.ensure_future(napa(5, 0, aburl, headers)),
                 asyncio.ensure_future(napa(0.5, 0.5, aburl, headers))]
        res = loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
        print(res)

    elif t == 3:
        test_getpnsconfig()
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
        test_serverinitPTS()
        test_servertestinit()
        test_servertestrun()
        test_serversleep()
    elif t == 6:
        test_vvpp()

    print('test successful ' + str(time.time() - now))
