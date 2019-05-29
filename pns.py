#!flask/bin/python
from pprint import pformat
import datetime
import time
from flask import Flask, jsonify, abort, make_response, request
from flask_httpauth import HTTPBasicAuth

from logdict import logdict
import logging
import logging.config
# create logger
logging.config.dictConfig(logdict)
logger = logging.getLogger()
logger.debug('logging level %d' % (logger.getEffectiveLevel()))

from common import opt

import pnsconfig as pc
from dataset.product import Product, FineTime1, History
from dataset.dataset import ArrayDataset, TableDataset
from dataset.eq import serializeClassID
from dataset.deserialize import deserializeClassID

app = Flask(__name__)
auth = HTTPBasicAuth()


result = None

lupd = None


def genposttestprod(indata):
    """ generate poet test product.
    put the 1st input (see maketestdata in test_pns.py)
    parameter to metadata
    and 2nd to the product's dataset
    """

    runner, cause = indata['creator'], indata['rootcause']
    x = Product(description="This is my product example",
                creator=runner, rootCause=cause,
                instrument="MyFavourite", modelName="Flight")
    i1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    im = ArrayDataset(data=i1, unit='magV', description='image 1')
    input = indata['input']
    pname, pv = input[0]
    dname, dv = input[1]
    print(im == dv)
    x.meta[pname] = pv
    x.sets[dname] = dv
    s1 = [dict(name='col1', unit='keV', column=[1, 4.4, 5.4E3]),
          dict(name='col2', unit='cnt', column=[0, 43.2, 2E3])]
    spec = TableDataset(data=s1)
    x.set('QualityImage', 'aQualityImage')
    x.sets["Spectrum"] = spec
    lupd = time.time()
    x.creationDate = FineTime1(datetime.datetime.fromtimestamp(lupd))
    x.type = 'test'
    x.history = History()
    return x


@app.route(pc.baseurl + '/<string:target>', methods=['GET'])
def get_result(target):
    ''' return calculation result. If the result is None return accordingly
    '''
    logger.debug('getr %s' % (target))
    global result, lupd
    ts = time.time()
    if target == 'data':
        w = {'result': result, 'lastUpdate': lupd, 'timestamp': ts}
    elif target == 'lastUpdate':
        w = {'lastUpdate': lupd, 'timestamp': ts}
    else:
        abort(401)
    s = serializeClassID(w)
    logger.debug(s[:100] + ' ...')
    resp = make_response(s)
    resp.headers['Content-Type'] = 'application/json'
    return resp


# import requests
# from http.client import HTTPConnection
# HTTPConnection.debuglevel = 1

@auth.verify_password
def verify(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    if not (username and password):
        return False
    return username == pc.node['username'] and password == pc.node['password']


@app.route(pc.baseurl + '/<string:cmd>', methods=['POST'])
def calcresult(cmd):
    global result
    global lupd
    d = request.get_data()
    indata = deserializeClassID(d)
    print(indata)
    if cmd == 'data':
        result = genposttestprod(indata)
    elif cmd == 'echo':
        result = indata
    else:
        print(cmd)
        # abort(400)
        result = None
    ts = time.time()
    lupd = ts
    w = {'result': result, 'lastUpdate': lupd,
         'timestamp': ts}
    s = serializeClassID(w)
    logger.debug(s[:100] + ' ...')
    resp = make_response(s)
    resp.headers['Content-Type'] = 'application/json'
    return resp


@app.errorhandler(400)
def bad_request(error):
    ts = time.time()
    w = {'error': 'Bad request.', 'timestamp': ts}
    return make_response(jsonify(w), 400)


@app.errorhandler(401)
def unauthorized(error):
    ts = time.time()
    w = {'error': 'Unauthorized. Authentication needed to modify.', 'timestamp': ts}
    return make_response(jsonify(w), 401)


@app.errorhandler(404)
def not_found(error):
    ts = time.time()
    w = {'error': 'Not found.', 'timestamp': ts}
    return make_response(jsonify(w), 404)


@app.errorhandler(409)
def not_found(error):
    ts = time.time()
    w = {'error': 'Conflict. Updating.', 'timestamp': ts}
    return make_response(jsonify(w), 409)


if __name__ == '__main__':

    logger.info(
        'Pipline Pc.Node server starting. Make sure no other instance is running')
    pc.node, verbose = opt(pc.node)

    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.info('logging level %d' % (logger.getEffectiveLevel()))
    if pc.node['username'] in ['', None] or pc.node['password'] in ['', None]:
        logger.error(
            'Error. Specify non-empty username and password on commandline')
        exit(3)

    app.run(host=pc.node['host'], port=pc.node['port'], debug=verbose)
