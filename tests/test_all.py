import sys
from pprint import pprint, pformat
import pkg_resources
import subprocess
import base64
from collections import OrderedDict
from urllib.request import pathname2url
import requests
import os
from os.path import isfile, isdir, join, expanduser, expandvars

from pns.logdict import logdict
import logging
import logging.config
# create logger
logging.config.dictConfig(logdict)
logger = logging.getLogger()

logger.debug('level %d' % (logger.getEffectiveLevel()))

from pns.common import getJsonObj, postJsonObj, putJsonObj, commonheaders, opt

# default configuration is provided. Copy pnsconfig.py to ~/local.py
from pns.pnsconfig import baseurl, node, paths, init, config, prog, clean
import sys
env = expanduser(expandvars('$HOME'))
sys.path.insert(0, env)
try:
    from local import baseurl, node, paths, init, config, prog, clean
except Exception:
    pass

from pns import server
from dataset.deserialize import deserializeClassID
from dataset.product import Product
from dataset.metadata import NumericParameter
from dataset.dataset import ArrayDataset
from dataset.eq import deepcmp, serializeClassID

testname = 'SVOM'
addrport = 'http://' + node['host'] + ':' + str(node['port'])

# last timestamp/lastUpdate
lupd = 0


if 0:
    poststr = 'curl -i -H "Content-Type: application/json" -X POST --data @%s http://localhost:5000%s --user %s'
    cmd = poststr % ('resource/' + 'nodetestinput.jsn',
                     pathname2url(baseurl + '/' +
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
    o = getJsonObj(addrport + baseurl + '/')
    assert o is not None, 'Cannot connect to the server'
    logger.info('initial server response %s' % (str(o)[:100] + '...'))
    # assert 'result' is not None, 'please start the server to refresh.'
    # initialize test data.


def checkputinitresult(result, msg):
    assert len(msg) == 0, msg
    assert result['returncode'] == 0, 'Error %d testing script file hello. STDOUT %s STDERR %s'\
        % (result['returncode'], result['stdout'], result['stderr'])


def test_serverinit():
    """ server unit test for init() """
    returncode, msg = server.initPTS(None)
    checkputinitresult(returncode, msg)


def test_putinit():
    """ calls the default pnsconfig.paths['pnshome']/initPTS script
    which checks the existence of hello
    """
    code = base64.b64encode(b"foo:bar").decode("ascii")
    commonheaders.update({'Authorization': 'Basic %s' % (code)})
    # print(nodetestinput)
    o = putJsonObj(addrport + baseurl +
                   '/init',
                   None,
                   headers=commonheaders)
    issane(o)
    checkputinitresult(o['result'], o['message'])


def issane(o):
    """ basic check on POST return """
    global lupd
    assert o is not None, "Server is having trouble"
    assert 'error' not in o, o['error']
    assert o['timestamp'] > lupd
    lupd = o['timestamp']


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
    return OrderedDict({'creator': 'me', 'rootcause': 'server test',
                        'input': x})


def checkpostresult(o):
    global result, lupd, nodetestinput
    p = o['result']
    assert issubclass(p.__class__, Product), (p.__class__)
    # creator rootcause
    # print('p.toString()' + p.toString())
    assert p.meta['creator'] == nodetestinput['creator']
    assert p.rootCause == nodetestinput['rootcause']
    # input data
    input = nodetestinput['input']
    pname, pv = list(input.meta.items())[0]
    dname, dv = list(input.sets.items())[0]
    # compare with returened data
    assert p.meta[pname] == pv
    assert p.sets[dname] == dv


def test_post():
    ''' send a set of data to the server and get back a product with
    properties, parameters, and dataset containing those in the input
    '''
    logger.info('POST testpipeline node server')
    global result, lupd, nodetestinput
    checkserver()
    nodetestinput = makeposttestdata()
    code = base64.b64encode(b"foo:bar").decode("ascii")
    commonheaders.update({'Authorization': 'Basic %s' % (code)})
    # print(nodetestinput)
    o = putJsonObj(addrport + baseurl +
                   '/init',
                   None,
                   headers=commonheaders)
    o = postJsonObj(addrport + baseurl +
                    '/data',
                    nodetestinput,
                    headers=commonheaders)
    issane(o)
    checkpostresult(o)


def makeruntestdata():
    """ the input has only one product, which has one dataset,
    which has one data item -- a string that is the name
    """
    x = Product(description="hello world pipeline input product")
    x['theName'] = ArrayDataset(data='stranger', description='input. the name')
    return x


def checkrunresult(p):
    global result, lupd, nodetestinput

    assert issubclass(p.__class__, Product), str(p.__class__) + ' ' + str(p)
    # creator rootcause
    # print('p.toString()' + p.toString())
    assert p.meta['creator'] == nodetestinput['creator']
    assert p.rootCause == nodetestinput['rootcause']
    # input data
    input = nodetestinput['input']
    answer = 'hello ' + input['theName'].data + '!\n'
    assert p['theAnswer'].data == answer


def test_serverrun():
    ''' send a product that has a name string as its data
    to the server "run" routine locally installed with this
    test, and get back a product with
    a string 'hello, $name!' as its data
    '''
    logger.info('POST test for pipeline node server "run": hello')
    global result, nodetestinput

    x = makeruntestdata()
    # construct the nodetestinput to the node
    nodetestinput = OrderedDict({'creator': 'me', 'rootcause': 'server test',
                                 'input': x})
    js = serializeClassID(nodetestinput)
    logger.debug(js[:160])
    o, msg = server.run(js)
    # issane(o) is skipped
    checkrunresult(o)


def test_run():
    ''' send a product that has a name string as its data
    to the server and get back a product with
    a string 'hello, $name!' as its data
    '''
    logger.info('POST test for pipeline node server: hello')
    global result, lupd, nodetestinput
    checkserver()

    test_putinit()

    x = makeruntestdata()
    # construct the nodetestinput to the node
    nodetestinput = OrderedDict({'creator': 'me', 'rootcause': 'server test',
                                 'input': x})
    code = base64.b64encode(b"foo:bar").decode("ascii")
    commonheaders.update({'Authorization': 'Basic %s' % (code)})
    # print(nodetestinput)
    o = postJsonObj(addrport + baseurl +
                    '/run',
                    nodetestinput,
                    headers=commonheaders)
    issane(o)
    checkrunresult(o['result'])


def test_getinit():
    ''' compare server side initPTS contens with the local copy
    '''
    logger.info('get initPTS')
    o = getJsonObj(addrport + baseurl + '/init')
    issane(o)
    with open(init[0], 'r') as f:
        result = f.read()
    assert result == o['result']


def test_deleteclean():
    ''' make input and output dirs and see if DELETE removes them.
    '''
    logger.info('delete cleanPTS')
    # make sure input and output dirs are made
    test_run()
    o = getJsonObj(addrport + baseurl + '/input')
    issane(o)
    assert o['result'] is not None
    o = getJsonObj(addrport + baseurl + '/output')
    issane(o)
    assert o['result'] is not None

    url = addrport + baseurl + '/clean'
    code = base64.b64encode(b"foo:bar").decode("ascii")
    commonheaders.update({'Authorization': 'Basic %s' % (code)})
    try:
        r = requests.delete(url, headers=commonheaders, timeout=15)
        stri = r.text
        o = deserializeClassID(stri)
    except Exception as e:
        logger.debug(e)
        logger.error("Give up DELETE " + url)
        o = None
    issane(o)
    assert o['result'] is not None, o['message']
    o = getJsonObj(addrport + baseurl + '/input')
    issane(o)
    assert o['result'] is None
    o = getJsonObj(addrport + baseurl + '/output')
    issane(o)
    assert o['result'] is None


def test_mirror():
    ''' send a set of data to the server and get back the same.
    '''
    logger.info('POST testpipeline node server')
    checkserver()
    global result, lupd, nodetestinput
    nodetestinput = makeposttestdata()
    code = base64.b64encode(b"foo:bar").decode("ascii")
    commonheaders.update({'Authorization': 'Basic %s' % (code)})
    # print(nodetestinput)
    o = postJsonObj(addrport + baseurl +
                    '/echo',
                    nodetestinput,
                    headers=commonheaders)
    # print(o)
    issane(o)
    r = deepcmp(o['result'], nodetestinput)
    assert r is None, r


if __name__ == '__main__':
    node, verbose = opt(node)
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.info('logging level %d' % (logger.getEffectiveLevel()))
    test_post()
    # test_getlastUpdate()
    # test_get()
    # test_get()
    test_postmirror()
    test_run()
    print('test successful')
