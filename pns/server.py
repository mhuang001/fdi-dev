#!flask/bin/python
from pprint import pformat
import datetime
import time
import sys
from os.path import isfile, isdir, join, expanduser, expandvars
from os import listdir
import os
from pathlib import Path
import traceback
import pwd
import grp
import types
from subprocess import Popen, PIPE, TimeoutExpired, run as srun
import pkg_resources
from flask import Flask, jsonify, abort, make_response, request, url_for
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
from pns.pnsconfig import baseurl, node, paths, init, config, prog, clean, timeout

# default configuration is provided. Copy pnsconfig.py to ~/local.py
import sys
env = expanduser(expandvars('$HOME'))
sys.path.insert(0, env)
try:
    from local import baseurl, node, paths, init, config, prog, clean, timeout
except Exception:
    pass

from dataset.product import Product, FineTime1, History
from dataset.dataset import ArrayDataset, TableDataset
from dataset.eq import serializeClassID
from dataset.deserialize import deserializeClassID

app = Flask(__name__)
auth = HTTPBasicAuth()


class status():
    successful = 0


result = None


def _execute(cmd, input=None, timeout=10):
    """ Executes a command on the server host in the pnshome directory and returns run status. Default imeout is 10sec.
    """
    sta = {'command': str(cmd)}
    cp = srun(cmd, input=input, stdout=PIPE, stderr=PIPE,
              cwd=paths['pnshome'], timeout=timeout,
              encoding='utf-8')  # universal_newlines=True)
    sta['stdout'], sta['stderr'] = cp.stdout, cp.stderr
    sta['returncode'] = cp.returncode
    return sta

    proc = Popen(cmd, stdin=PIPE, stdout=PIPE,
                 stderr=PIPE, universal_newlines=True)
    try:
        sta['stdout'], sta['stderr'] = proc.communicate(timeout=timeout)
        sta['returncode'] = proc.returncode
    except TimeoutExpired:
        # The child process is not killed if the timeout expista,
        # so in order to cleanup properly a well-behaved application
        # should kill the child process and finish communication
        # https://docs.python.org/3.6/library/subprocess.html?highlight=subprocess#subprocess.Popen.communicate
        proc.kill()
        sta['stdout'], sta['stderr'] = proc.communicate()
        sta['returncode'] = proc.returncode
    return sta


def initPTS(d=None):
    """ Initialize the Processing Task Software by running the init script defined in the config. Execution on the server host is in the pnshome directory and run result and status are returned.
    """

    # timeout is imported and needs to be declared global if referenced in ifs
    global timeout

    # hf = pkg_resources.resource_filename("pns.resource", "hello")
    logger.debug(str(d))
    indata = deserializeClassID(d)

    if hasattr(indata, '__iter__') and 'timeout' in indata:
        timeout = indata['timeout'].value

    stat = _execute(init, timeout=timeout)
    return stat['returncode'], stat


def configPTS(d=None):
    """ Configure the Processing Task Software by running the config script. Ref init PTS.
    """

    # timeout is imported and needs to be declared global if referenced in ifs
    global timeout

    logger.debug(str(d))
    indata = deserializeClassID88(d)

    if hasattr(indata, '__iter__') and 'timeout' in indata:
        timeout = indata['timeout'].value

    stat = _execute(config, timeout=timeout)
    return stat['returncode'], stat


def cleanPTS(d):
    """ Removing traces of past runnings the Processing Task Software.
    """
    # timeout is imported and needs to be declared global if referenced in ifs
    global timeout

    logger.debug(str(d))
    indata = deserializeClassID(d)

    if hasattr(indata, '__iter__') and 'timeout' in indata:
        timeout = indata['timeout'].value
    else:
        timeout = 10

    stat = _execute(clean, timeout=timeout)
    return stat['returncode'], stat


def checkpath(path):
    p = Path(path).resolve()
    if p.exists():
        if not p.is_dir():
            msg = str(p) + ' is not a directory.'
            logging.error(msg)
            abort(400)
    else:
        p.mkdir()
        uid = pwd.getpwnam("www-data").pw_uid
        gid = grp.getgrnam("www-data").gr_gid
        os.chown(str(p), uid, gid)
        logging.info(str(p) + ' directory has been made.')
    return p


def run(d):
    """ Generates a product by running script defined in the config as prog ('hello' for testing). Execution on the server host is in the pnshome directory and run result and status are returned.
    """
    pi = checkpath(paths['inputdir'])
    po = checkpath(paths['outputdir'])
    if pi is None or po is None:
        abort(401)
    # timeout is imported and needs to be declared global if referenced in ifs
    global timeout
    global lupd

    indata = deserializeClassID(d)
    logger.debug(indata)
    runner, cause = indata['creator'], indata['rootcause']
    contents = indata['input']['theName'].data
    for f in paths['inputfiles']:
        fp = pi.joinpath(f)
        if fp.exists():
            logging.debug('infile mode 0%o ' % (fp.stat().st_mode))
        try:
            if fp.exists():
                fp.rename(str(fp) + '.old')
            with fp.open(mode="w+") as inf:
                inf.write(contents)
        except Exception as e:
            return -1, str(e) + ' '.join(x) for x in
                traceback.extract_tb(e.__traceback__).format()

    ######### run PTS ########
    logger.debug(timeout)
    if hasattr(indata, '__iter__') and 'timeout' in indata:
        timeout = indata['timeout'].value

    stat = _execute(prog, timeout=timeout)
    if stat['returncode'] != 0:
        return stat['returncode'], stat

    ######### output ########
    try:
        with po.joinpath(paths['outputfile']).open("r") as outf:
            res = outf.read()
    except Exception as e:
        return -1, str(e)
    x = Product(description="hello world pipeline product",
                creator=runner, rootCause=cause,
                instrument="hello", modelName="you know what!")
    x['theAnswer'] = ArrayDataset(
        data=res, description='result from hello command')
    now = time.time()
    x.creationDate = FineTime1(datetime.datetime.fromtimestamp(now))
    x.type = 'test'
    x.history = History()
    return x, stat


def genposttestprod(d):
    """ generate post test product.
    put the 1st input (see maketestdata in test_all.py)
    parameter to metadata
    and 2nd to the product's dataset
    """

    indata = deserializeClassID(d)
    logger.debug(indata)

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
    return x, ''


def filesin(dir):
    """ returns names and contents of all files in the dir, 'None' if dir not existing. """

    if not isdir(dir):
        return None, dir + ' does not exist.'
    result = {}
    for f in listdir(dir):
        fn = join(dir, f)
        if isfile(fn):
            with open(fn, 'r') as f:
                result[fn] = f.read()
    return result, ''


@app.route(baseurl + '/<string:cmd>', methods=['GET'])
def getinfo(cmd):
    ''' returns init, config, run input, run output.
    '''
    logger.debug('getr %s' % (cmd))
    global result
    ts = time.time()
    if cmd == 'init':
        with open(init[0], 'r') as f:
            result = f.read()
        w = {'result': result, 'message': '', 'timestamp': ts}
    elif cmd == 'config':
        with open(config[0], 'r') as f:
            result = f.read()
        w = {'result': result, 'message': '', 'timestamp': ts}
    elif cmd == 'input':
        result, msg = filesin(paths['inputdir'])
        w = {'result': result, 'message': msg, 'timestamp': ts}
    elif cmd == 'output':
        result, msg = filesin(paths['outputdir'])
        w = {'result': result, 'message': msg, 'timestamp': ts}
    else:
        result, msg = 'init, confg, input, ouput', 'get API'
        w = {'result': result, 'message': msg, 'timestamp': ts}

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
    if cmd == 'data':
        result, msg = genposttestprod(d)
    elif cmd == 'echo':
        indata = deserializeClassID(d)
        logger.debug(indata)
        result, msg = indata, ''
    elif cmd == 'run':
        result, msg = run(d)
    else:
        logger.error(cmd)
        abort(400)
        result = None
    ts = time.time()
    w = {'result': result, 'message': msg, 'timestamp': ts}
    s = serializeClassID(w)
    logger.debug(s[:] + ' ...')
    resp = make_response(s)
    resp.headers['Content-Type'] = 'application/json'
    return resp


@app.route(baseurl + '/<string:cmd>', methods=['PUT'])
def setup(cmd):
    """ PUT is used to initialize or configure the Processing Task Software
    (PST).
    """
    global result
    d = request.get_data()
    logger.debug(d)
    if cmd == 'init':
        try:
            result, msg = initPTS(d)
        except Exception as e:
            msg = str(e)
            logger.error(msg)
    elif cmd == 'config':
        result, msg = configPTS(d)
    else:
        logger.error(cmd)
        abort(400)
        result = None
    ts = time.time()
    w = {'result': result, 'message': msg, 'timestamp': ts}
    s = serializeClassID(w)
    logger.debug(s[:] + ' ...')
    resp = make_response(s)
    resp.headers['Content-Type'] = 'application/json'
    return resp


@app.route(baseurl + '/<string:cmd>', methods=['DELETE'])
def cleanup(cmd):
    """ DELETE is used to clean up the Processing Task Software
    (PST) to its initial configured state.
    """

    d = request.get_data()
    # print('&&&&&&&& ' + str(d))
    if cmd == 'clean':
        try:
            result, msg = cleanPTS(d)
        except Exception as e:
            msg = str(e)
            logger.error(msg)
            result = None
    else:
        logger.error(cmd)
        abort(400)
        result = None
    ts = time.time()
    w = {'result': result, 'message': msg, 'timestamp': ts}
    s = serializeClassID(w)
    logger.debug(s[:] + ' ...')
    resp = make_response(s)
    resp.headers['Content-Type'] = 'application/json'
    return resp


APIs = {'GET':
        {'func': 'getinfo',
         'cmds': {'init': 'initPTS file', 'config': 'configPTS file',
                  'input': filesin, 'output': filesin}
         },
        'PUT':
        {'func': 'setup',
         'cmds': {'init': initPTS, 'config': configPTS}
         },
        'POST':
        {'func': 'calcresult',
         'cmds': {'data': genposttestprod, 'echo': 'Echo',
                  'run': run}
         },
        'DELETE':
        {'func': 'cleanup',
         'cmds': {'clean': cleanPTS}
         }}


def makepublicAPI(ops):
    api = {}
    o = APIs[ops]
    for cmd in o['cmds'].keys():
        c = o['cmds'][cmd]
        desc = c.__doc__ if isinstance(c, types.FunctionType) else c
        api[desc] = url_for(o['func'],
                            cmd=cmd,
                            _external=True)
    #print('******* ' + str(api))
    return api


@app.route(baseurl + '/', methods=['GET'])
@app.route(baseurl + '/api', methods=['GET'])
def get_apis():
    logger.debug('APIs %s' % (APIs.keys()))
    ts = time.time()
    l = [(a, makepublicAPI(a)) for a in APIs.keys()]
    w = {'APIs': dict(l), 'timestamp': ts}
    logger.debug('ret %s' % (str(w)[:100] + ' ...'))
    return jsonify(w)


@app.errorhandler(400)
def bad_request(error):
    ts = time.time()
    w = {'error': 'Bad request.', 'message': str(error), 'timestamp': ts}
    return make_response(jsonify(w), 400)


@app.errorhandler(401)
def unauthorized(error):
    ts = time.time()
    w = {'error': 'Unauthorized. Authentication needed to modify.',
         'message': str(error), 'timestamp': ts}
    return make_response(jsonify(w), 401)


@app.errorhandler(404)
def not_found(error):
    ts = time.time()
    w = {'error': 'Not found.', 'message': str(error), 'timestamp': ts}
    return make_response(jsonify(w), 404)


@app.errorhandler(409)
def not_found(error):
    ts = time.time()
    w = {'error': 'Conflict. Updating.',
         'message': str(error), 'timestamp': ts}
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
