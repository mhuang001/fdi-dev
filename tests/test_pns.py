# -*- coding: utf-8 -*-
import sys
import base64
from urllib.request import pathname2url
import requests
import os
import pkg_resources
import copy
import time

# This is to be able to test w/ or w/o installing the package
# https://docs.python-guide.org/writing/structure/
from .pycontext import spdc

from .logdict import doLogging, logdict
if doLogging:
    import logging
    import logging.config
    # create logger
    logging.config.dictConfig(logdict)
    logger = logging.getLogger()
    logging.getLogger("requests").setLevel(logging.WARN)
    logging.getLogger("urllib3").setLevel(logging.WARN)
    logging.getLogger("filelock").setLevel(logging.WARN)

from spdc.pns.common import getJsonObj, postJsonObj, putJsonObj, commonheaders
from spdc.pns.options import opt

# default configuration is provided. Copy pnsconfig.py to ~/local.py
from spdc.pns.pnsconfig import pnsconfig as pc
import sys
from os.path import expanduser, expandvars
env = expanduser(expandvars('$HOME'))
sys.path.insert(0, env)
try:
    from local import pnsconfig as pc
except Exception:
    pass

if doLogging:
    logger.setLevel(pc['logginglevel'])
    logger.debug('level %d' % (logger.getEffectiveLevel()))

from spdc.pns import server
from spdc.dataset.odict import ODict
from spdc.dataset.serializable import serializeClassID, serializeClassID
from spdc.dataset.product import Product
from spdc.dataset.metadata import NumericParameter
from spdc.dataset.deserialize import deserializeClassID
from spdc.dataset.dataset import ArrayDataset, GenericDataset
from spdc.dataset.eq import deepcmp

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


def test_getpnsconfig():
    ''' gets and compares pnsconfig remote and local
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


def test_serverinit():
    """ server unit test for put init. 
    this is conflict with put testinit. will condition the server for running the PTS, not suitable for running other test
    """
    ret, sta = server.initPTS(None)
    check0result(ret, sta)


def test_putinit():
    """ calls the default pnsconfig['scripts']['init'] script.
    this is conflict with put testinit. will condition the server for running the PTS, not suitable for running other test
    """

    d = {'timeout': 5}
    o = putJsonObj(aburl +
                   '/init',
                   d,
                   headers=commonheaders)
    issane(o)
    check0result(o['result'], o['message'])

# this will condition the server for testing


def test_servertestinit():
    """ server unit test for put testinit """
    ret, sta = server.testinit(None)
    check0result(ret, sta)


# this will condition the server for testing
def test_puttestinit():
    """ Prepares for the rest of the tests.  Renames the 'init' 'config' 'run' 'clean' scripts to "*.save" and points it to the '.ori' scripts.
    """

    checkserver()
    d = {'timeout': 5}
    o = putJsonObj(aburl +
                   '/testinit',
                   d,
                   headers=commonheaders)
    issane(o)
    check0result(o['result'], o['message'])


def test_getinit():
    ''' compare. server side initPTS contens with the local  default copy
    '''
    logger.info('get initPTS')
    c = 'init'
    n = pc['scripts'][c][0].rsplit('/', maxsplit=1)[1]
    fn = pkg_resources.resource_filename("spdc.pns.resources", n)
    checkContents(cmd='/' + c, filename=fn + '.ori')


def test_getrun():
    ''' compare. server side run contens with the local default copy
    '''
    logger.info('get run')
    c = 'run'
    n = pc['scripts'][c][0].rsplit('/', maxsplit=1)[1]
    fn = pkg_resources.resource_filename("spdc.pns.resources", n)
    checkContents(cmd='/' + c, filename=fn + '.ori')


def test_putconfigpns():
    """ send signatured pnsconfig and check.
    this function is useless for a stateless server
    """
    t = test_getpnsconfig()
    t['testing'] = 'yes'
    d = {'timeout': 5, 'input': t}
    # print(nodetestinput)
    o = putJsonObj(aburl +
                   '/pnsconf',
                   d,
                   headers=commonheaders)
    # put it back not to infere other tests
    del t['testing']
    d = {'timeout': 5, 'input': t}
    p = putJsonObj(aburl +
                   '/pnsconf',
                   d,
                   headers=commonheaders)

    issane(o)
    assert o['result']['testing'] == 'yes', o['message']
    assert 'testing' not in pc, str(pc)
    issane(p)
    assert 'testing' not in p['result']


def makeposttestdata():
    a1 = 'a test NumericParameter'
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
    assert p.meta['creator'] == nodetestinput['creator']
    assert p.rootCause == nodetestinput['rootcause']
    # input data
    input = nodetestinput['input']
    pname, pv = list(input.meta.items())[0]
    dname, dv = list(input.getDataWrappers().items())[0]
    # compare with returened data
    assert p.meta[pname] == pv
    assert p[dname] == dv


def test_post():
    ''' send a set of data to the server and get back a product with
    properties, parameters, and dataset containing those in the input
    '''
    logger.info('POST testpipeline node server')

    nodetestinput = makeposttestdata()
    # print(nodetestinput)
    o = postJsonObj(aburl +
                    '/testcalc',
                    nodetestinput,
                    headers=commonheaders)
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
    assert p.meta['creator'] == nodetestinput['creator']
    assert p.rootCause == nodetestinput['rootcause']
    # input data
    input = nodetestinput['input']
    answer = 'hello ' + input['theName'].data + '!'
    assert p['theAnswer'].data[:len(answer)] == answer


def test_servertestrun():
    ''' send a product that has a name string as its data
    to the server "testrun" routine locally installed with this
    test, and get back a product with
    a string 'hello, $name!' as its data
    '''
    logger.info('POST test for pipeline node server "testrun": hello')

    test_servertestinit()

    x = makeruntestdata()
    # construct the nodetestinput to the node
    nodetestinput = ODict({'creator': 'me', 'rootcause': 'server test',
                           'input': x})
    js = serializeClassID(nodetestinput)
    logger.debug(js[:160])
    o, msg = server.testrun(js)
    # issane(o) is skipped
    checkrunresult(o, msg, nodetestinput)


def test_testrun():
    ''' send a product that has a name string as its data
    to the server and get back a product with
    a string 'hello, $name!' as its data
    '''
    logger.info('POST test for pipeline node server: hello')

    test_puttestinit()

    x = makeruntestdata()
    # construct the nodetestinput to the node
    nodetestinput = ODict({'creator': 'me', 'rootcause': 'server test',
                           'input': x})
    # print(nodetestinput)
    o = postJsonObj(aburl +
                    '/testrun',
                    nodetestinput,
                    headers=commonheaders)
    issane(o)
    checkrunresult(o['result'], o['message'], nodetestinput)


def test_deleteclean():
    ''' make input and output dirs and see if DELETE removes them.
    '''
    logger.info('delete cleanPTS')
    # make sure input and output dirs are made
    test_testrun()
    o = getJsonObj(aburl + '/input')
    issane(o)
    assert o['result'] is not None
    o = getJsonObj(aburl + '/output')
    issane(o)
    assert o['result'] is not None

    url = aburl + '/clean'
    try:
        r = requests.delete(url, headers=commonheaders, timeout=15)
        stri = r.text
    except Exception as e:
        logger.error("Give up DELETE " + url + ' ' + str(e))
        stri = None
    o = deserializeClassID(stri)
    issane(o)
    assert o['result'] is not None, o['message']
    o = getJsonObj(aburl + '/input')
    issane(o)
    assert o['result'] is None
    o = getJsonObj(aburl + '/output')
    issane(o)
    assert o['result'] is None


def test_mirror():
    ''' send a set of data to the server and get back the same.
    '''
    logger.info('POST testpipeline node server')
    nodetestinput = makeposttestdata()
    # print(nodetestinput)
    o = postJsonObj(aburl +
                    '/echo',
                    nodetestinput,
                    headers=commonheaders)
    # print(o)
    issane(o)
    r = deepcmp(o['result'], nodetestinput)
    assert r is None, r


def test_serversleep():
    """
    """
    s = '1.5'
    tout = 2
    now = time.time()
    re, st = server.dosleep({'timeout': tout}, s)
    d = time.time() - now - float(s)
    assert re == 0, str(re)
    assert d > 0 and d < 0.5
    print('dt=%f re=%s state=%s' % (d, str(re), str(st)))
    now = time.time()
    # let it timeout
    tout = 1
    re, st = server.dosleep({'timeout': tout}, s)
    d = time.time() - now - tout
    assert re < 0
    assert d > 0 and d < float(s) - tout
    print('dt=%f re=%s state=%s' % (d, str(re), str(st)))


def test_sleep():
    """
    """
    s = '1.5'
    tout = 2
    now = time.time()
    o = postJsonObj(aburl +
                    '/sleep/' + s,
                    {'timeout': tout},
                    headers=commonheaders)
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
                    headers=commonheaders)
    d = time.time() - now - tout
    # print(o)
    issane(o)
    re, st = o['result'], o['message']
    assert re < 0
    assert d > 0 and d < float(s) - tout
    #print('deviation=%f re=%s state=%s' % (d, str(re), str(st)))


from multiprocessing import Process, Pool, TimeoutError


def info(title):
    print(title)
    print('module name:' + __name__)
    if hasattr(os, 'getppid'):  # only available on Unix
        print('parent process: %d' % (os.getppid()))
    print('process id: ' + str(os.getpid()))
    print(time.time())


def nap(t, d):
    info(t)
    time.sleep(d)
    s = str(t)
    tout = 5
    o = postJsonObj(aburl +
                    '/sleep/' + s,
                    {'timeout': tout},
                    headers=commonheaders
                    )
    # print('nap ' + str(time.time()) + ' ' + str(s) + ' ' + str(o)
    return o


import aiohttp
import asyncio


async def napa(t, d):
    # info(t)
    asyncio.sleep(d)
    s = str(t)
    tout = 11
    o = None
    js = serializeClassID({'timeout': tout})
    async with aiohttp.ClientSession() as session:
        async with session.post(aburl +
                                '/sleep/' + s,
                                data=js,
                                headers=commonheaders
                                ) as resp:
            # print(resp.status)
            stri = await resp.text()
    o = deserializeClassID(stri)
    #print('nap ' + str(time.time()) + ' ' + str(s) + ' ' + str(o))
    return o


def test_lock():
    """ when a pns is busy with any commands that involves executing in the $pnshome dir the execution is locked system-wide with a lock-file .lock. Any attempts to execute a shell command when the lock is in effect will get a 409.
    """

    tm = 3
    if 0:
        with Pool(processes=4) as pool:
            res = pool.starmap(nap, [(tm, 0), (0.5, 0.5)])
    if 0:
        # does not work
        import threading
        try:
            threading.Thread(target=nap(tm, 0))
            threading.Thread(target=nap(0.5, 0.5))
        except Exception as e:
            print("Error: unable to start thread " + str(e))
        time.sleep(tm + 2)
    if 1:
        loop = asyncio.get_event_loop()
        tasks = [asyncio.ensure_future(napa(tm, 0)),
                 asyncio.ensure_future(napa(0.5, 0.5))]
        taskres = loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
        res = [f.result() for f in [x for x in taskres][0]]

    # print(res)
    if issubclass(res[0]['message'].__class__, ODict):
        r1, r2 = res[0], res[1]
    else:
        r2, r1 = res[0], res[1]
    assert r1['result'] == 0
    assert '409' in r2['message']


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
        test_serverinit()
        test_servertestinit()
        test_servertestrun()
        test_serversleep()
    elif t == 6:
        test_vvpp()

    print('test successful ' + str(time.time() - now))
