import sys
from pprint import pprint, pformat
import base64
from collections import OrderedDict
from urllib.request import pathname2url
import os

from logdict import logdict
import logging
import logging.config
# create logger
logging.config.dictConfig(logdict)
logger = logging.getLogger()

logger.debug('level %d' % (logger.getEffectiveLevel()))

from common import getJsonObj, postJsonObj, commonheaders, opt
import pnsconfig as pc
from dataset.deserialize import deserializeClassID
from dataset.product import Product
from dataset.metadata import NumericParameter
from dataset.dataset import ArrayDataset
from dataset.eq import deepcmp

testname = 'SVOM'
addrport = ''


# last timestamp/lastUpdate
lupd = 0


if 0:
    poststr = 'curl -i -H "Content-Type: application/json" -X POST --data @%s http://localhost:5000%s --user %s'
    cmd = poststr % ('resource/' + 'inputtestdata.jsn',
                     pathname2url(pc.baseurl + '/' +
                                  inputtestdata['creator'] + '/' +
                                  inputtestdata['rootcause']),
                     'foo:bar')
    print(cmd)
    os.system(cmd)
    sys.exit()


def setup_module():
    global testpns
    # check if data already exists
    o = getJsonObj(addrport + pc.baseurl + '/data')
    assert o is not None, 'Cannot connect to the server'
    logger.info('initial server response %s' % (str(o)))
    assert 'result' is not None, 'please start the server to refresh.'
    # initialize test data.


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
    global result, lupd, inputtestdata
    p = o['result']
    assert issubclass(p.__class__, Product), (p.__class__)
    # creator rootcause
    #print('p.toString()' + p.toString())
    assert p.meta['creator'] == inputtestdata['creator']
    assert p.rootCause == inputtestdata['rootcause']
    # input data
    input = inputtestdata['input']
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
    global result, lupd, inputtestdata
    inputtestdata = makeposttestdata()
    code = base64.b64encode(b"foo:bar").decode("ascii")
    commonheaders.update({'Authorization': 'Basic %s' % (code)})
    # print(inputtestdata)
    o = postJsonObj(addrport + pc.baseurl +
                    '/data',
                    inputtestdata,
                    headers=commonheaders)
    assert o is not None, "Server is having trouble"
    assert ('error' not in o) or (o['lastUpdate'] - lupd < 0), o['error']
    assert o['timestamp'] == o['lastUpdate']
    lupd = o['lastUpdate']
    checkpostresult(o)


def checkrunresult(o):
    global result, lupd, inputtestdata
    p = o['result']
    assert issubclass(p.__class__, Product), (p.__class__)
    # creator rootcause
    #print('p.toString()' + p.toString())
    assert p.meta['creator'] == inputtestdata['creator']
    assert p.rootCause == inputtestdata['rootcause']
    # input data
    input = inputtestdata['input']
    assert p.data == input.data


def test_run():
    ''' send a product that has a name string as its data
    to the server and get back a product with
    a string 'hello, $name!' as its data
    '''
    logger.info('POST testpipeline node server by running hello')
    global result, lupd, inputtestdata
    x = Product(description="hello world pipeline input product")
    x.data = ArrayDataset(data=res, description='stranger')

    inputtestdata = OrderedDict({'creator': 'me', 'rootcause': 'server test',
                                 'input': x})
    code = base64.b64encode(b"foo:bar").decode("ascii")
    commonheaders.update({'Authorization': 'Basic %s' % (code)})
    # print(inputtestdata)
    o = postJsonObj(addrport + pc.baseurl +
                    '/run',
                    inputtestdata,
                    headers=commonheaders)
    assert o is not None, "Server is having trouble"
    assert ('error' not in o) or (o['lastUpdate'] - lupd < 0), o['error']
    assert o['timestamp'] == o['lastUpdate']
    lupd = o['lastUpdate']
    checkrunresult(o)


def test_get():
    ''' lastUpdate nor result should change.
    '''
    logger.info('read the result')
    o = getJsonObj(addrport + pc.baseurl + '/data')
    assert o is not None, "Server is having trouble"
    assert ('error' not in o) or (o['lastUpdate'] - lupd < 0), o['error']
    assert o['timestamp'] > o['lastUpdate']
    assert o['lastUpdate'] == lupd  # this is the case after the 1st POST
    checkpostresult(o)


def test_getlastUpdate():
    logger.info('read when the result was caculated')
    global lupd
    o = getJsonObj(addrport + pc.baseurl + '/lastUpdate')
    assert o['lastUpdate'] == lupd  # this is the case after the 1st POST
    tr = o['timestamp']
    assert tr >= lupd, 't-read %f lastt %f' % (tr, lastt)


def test_postmirror():
    ''' send a set of data to the server and get back the same.
    '''
    logger.info('POST testpipeline node server')
    global result, lupd, inputtestdata
    code = base64.b64encode(b"foo:bar").decode("ascii")
    commonheaders.update({'Authorization': 'Basic %s' % (code)})
    # print(inputtestdata)
    o = postJsonObj(addrport + pc.baseurl +
                    '/echo',
                    inputtestdata,
                    headers=commonheaders)
    assert ('error' not in o) or (o['lastUpdate'] - lupd < 0), o['error']
    # print(o)
    r = deepcmp(o['result'], inputtestdata)
    assert r is None, r


if __name__ == '__main__':
    pc.node, verbose = opt(pc.node)
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.info('logging level %d' % (logger.getEffectiveLevel()))
    addrport = 'http://' + pc.node['host'] + ':' + str(pc.node['port'])
    setup_module()
    test_post()
    test_getlastUpdate()
    test_get()
    test_get()
    test_postmirror()
    test_post()
    print('test successful')
