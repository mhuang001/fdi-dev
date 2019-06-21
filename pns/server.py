#!flask/bin/python
from pprint import pformat
import datetime
import time
from pathlib import Path
import subprocess
import pkg_resources
from flask import Flask, jsonify, abort, make_response, request
from flask_httpauth import HTTPBasicAuth

from pns.logdict import logdict
import logging
import logging.config
# create logger
logging.config.dictConfig(logdict)
if __name__ == '__main__':
    logger = logging.getLogger()
else:
    logger = logging.getLogger(__name__)
logger.debug('logging level %d' % (logger.getEffectiveLevel()))

from pns.common import mkdir, opt
from pns.pnsconfig import baseurl, node, paths, prog

from dataset.product import Product, FineTime1, History
from dataset.dataset import ArrayDataset, TableDataset
from dataset.eq import serializeClassID
from dataset.deserialize import deserializeClassID

app = Flask(__name__)
auth = HTTPBasicAuth()


result = None


def initPTS():
    """ Initialize the Processing Task Software.
    """

    hf = pkg_resources.resource_filename("pns.resource", "hello")
    try:
        #subprocess.run(['/bin/rm', '-rf', prog[0]])
        #subprocess.run(['/bin/mkdir', paths['inputdir']])
        subprocess.run(['cp', hf, '/tmp'])
        return None
    except Exception as e:
        return str(e)


def checkpath(path):
    p = Path(path).resolve()
    if p.exists():
        if not p.is_dir():
            logging.error(str(p) + ' is not a directory.')
            return None
    else:
        p.mkdir()
        logging.info(str(p) + ' directory has been made.')
    return p


def run(indata):
    """ generate  product.
    put the 1st input (see maketestdata in test_pns.py)
    parameter to metadata
    and 2nd to the product's dataset
    """
    pi = checkpath(paths['inputdir'])
    po = checkpath(paths['outputdir'])
    if pi is None or po is None:
        abort(401)
    global lupd
    runner, cause = indata['creator'], indata['rootcause']
    contents = indata['input']['theName'].data
    for f in paths['inputfiles']:
        with pi.joinpath(f).open(mode="w") as inf:
            inf.write(contents)
    subprocess.run(prog)
    with po.joinpath(paths['outputfile']).open("r") as outf:
        res = outf.read()
    x = Product(description="hello world pipeline product",
                creator=runner, rootCause=cause,
                instrument="hello", modelName="you know what!")
    x['theAnswer'] = ArrayDataset(
        data=res, description='result from hello command')
    now = time.time()
    x.creationDate = FineTime1(datetime.datetime.fromtimestamp(now))
    x.type = 'test'
    x.history = History()
    return x


def genposttestprod(indata):
    """ generate post test product.
    put the 1st input (see maketestdata in test_all.py)
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
    pname, pv = list(input.meta.items())[0]
    dname, dv = list(input.sets.items())[0]
    print(im == dv)  # this should be true
    x.meta[pname] = pv
    x.sets[dname] = dv
    s1 = [dict(name='col1', unit='keV', column=[1, 4.4, 5.4E3]),
          dict(name='col2', unit='cnt', column=[0, 43.2, 2E3])]
    spec = TableDataset(data=s1)
    x.set('QualityImage', 'aQualityImage')
    x.sets["Spectrum"] = spec
    now = time.time()
    x.creationDate = FineTime1(datetime.datetime.fromtimestamp(now))
    x.type = 'test'
    x.history = History()
    return x


@app.route(baseurl + '/<string:target>', methods=['GET'])
def get_result(target):
    ''' return calculation result. If the result is None return accordingly
    '''
    logger.debug('getr %s' % (target))
    global result
    ts = time.time()
    if target == 'data':
        w = {'result': result, 'timestamp': ts}
    elif target == 'lastUpdate':
        w = {'timestamp': ts}
    else:
        abort(401)
    s = serializeClassID(w)
    logger.debug(s[:] + ' ...')
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
    return username == node['username'] and password == node['password']


@app.route(baseurl + '/<string:cmd>', methods=['POST'])
def calcresult(cmd):
    global result
    d = request.get_data()
    indata = deserializeClassID(d)
    logger.debug(indata)
    if cmd == 'data':
        result = genposttestprod(indata)
    elif cmd == 'echo':
        result = indata
    elif cmd == 'run':
        result = run(indata)
    elif cmd == 'inittest':
        result = initPTS(indata)
    else:
        logger.error(cmd)
        # abort(400)
        result = None
    ts = time.time()
    w = {'result': result, 'timestamp': ts}
    s = serializeClassID(w)
    logger.debug(s[:] + ' ...')
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
        'Pipline Node server starting. Make sure no other instance is running')
    node, verbose = opt(node)

    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.info('logging level %d' % (logger.getEffectiveLevel()))
    if node['username'] in ['', None] or node['password'] in ['', None]:
        logger.error(
            'Error. Specify non-empty username and password on commandline')
        exit(3)

    app.run(host=node['host'], port=node['port'], debug=verbose)
