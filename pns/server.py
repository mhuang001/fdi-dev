#!flask/bin/python
# -*- coding: utf-8 -*-

from pprint import pformat
import datetime
import time
import sys
import pwd
import grp
from os.path import isfile, isdir, join
from os import listdir, chown
from pathlib import Path
import traceback
import types
from subprocess import Popen, PIPE, TimeoutExpired, run as srun
import pkg_resources
from flask import Flask, jsonify, abort, make_response, request, url_for
from flask_httpauth import HTTPBasicAuth

from pns.logdict import logdict
logdict['handlers']['file']['filename'] = '/tmp/pns-server.log'
import logging
import logging.config
# create logger
logging.config.dictConfig(logdict)
if __name__ == '__main__':
    logger = logging.getLogger()
else:
    logger = logging.getLogger(__name__)
logger.debug('logging level %d' % (logger.getEffectiveLevel()))

from pns.pnsconfig import pnsconfig as pc

# default configuration is provided. Copy pnsconfig.py to ~/local.py
import sys
from os.path import expanduser, expandvars
env = expanduser(expandvars('$HOME'))
# apache wsgi will return '$HOME' with no expansion
env = '/root' if env == '$HOME' else env
sys.path.insert(0, env)
try:
    from local import pnsconfig as pc
except Exception:
    pass

from dataset.metadata import Parameter, NumericParameter, MetaData
from dataset.product import Product, FineTime1, History
from dataset.dataset import GenericDataset, ArrayDataset, TableDataset
from dataset.serializable import serializeClassID
from dataset.deserialize import deserializeClassID
from pal.productref import ProductRef
from pal.urn import Urn

app = Flask(__name__)
auth = HTTPBasicAuth()


class status():
    successful = 0


def _execute(cmd, input=None, timeout=10):
    """ Executes a command on the server host in the pnshome directory and returns run status. Default imeout is 10sec.
    """
    logger.debug(cmd)
    sta = {'command': str(cmd)}
    cp = srun(cmd, input=input, stdout=PIPE, stderr=PIPE,
              cwd=pc['paths']['pnshome'], timeout=timeout,
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


def checkpath(path):
    logger.debug(path)
    p = Path(path).resolve()
    if p.exists():
        if not p.is_dir():
            msg = str(p) + ' is not a directory.'
            logger.error(msg)
            return None
    else:
        p.mkdir()
        un = pc['serveruser']
        try:
            uid = pwd.getpwnam(un).pw_uid
        except KeyError as e:
            msg = 'cannot set input/output dirs owner to ' + \
                un + '. check config. ' + str(e)
            logger.error(msg)
            return None
        try:
            gid = grp.getgrnam(un).gr_gid
        except KeyError as e:
            gid = -1
            logger.warn('input/output group unchanged. ' + str(e))
        try:
            chown(str(p), uid, gid)
        except Exception as e:
            msg = 'cannot set input/output dirs owner to ' + \
                un + '. check config. ' + str(e)
            logger.error(msg)
            return None

        logger.info(str(p) + ' directory has been made.')
    return p


def initPTS(d=None):
    """ Initialize the Processing Task Software by running the init script defined in the config. Execution on the server host is in the pnshome directory and run result and status are returned. If input/output directories cannot be created with serveruser as owner, Error401 will be given.
    """

    logger.debug(str(d))

    p = checkpath(pc['paths']['pnshome'])
    if p is None:
        abort(401)

    pi = checkpath(pc['paths']['inputdir'])
    po = checkpath(pc['paths']['outputdir'])
    if pi is None or po is None:
        abort(401)

    indata = deserializeClassID(d)

    if hasattr(indata, '__iter__') and 'timeout' in indata:
        timeout = indata['timeout']
    else:
        timeout = pc['timeout']

    stat = _execute(pc['scripts']['init'], timeout=timeout)
    return stat['returncode'], stat


def initTest(d=None):
    """     Renames the 'prog' script to "*.save" and points it to the "hello" script.
    """

    #hf = pkg_resources.resource_filename("pns.resources", "hello")
    timeout = pc['timeout']
    ni = pc['scripts']['prog'][0]
    cmd = ['mv', '-f', ni, ni + '.save']
    stat = _execute(cmd, timeout=timeout)
    cmd = ['ln', '-s', pc['paths']['pnshome'] + '/hello', ni]
    stat = _execute(cmd, timeout=timeout)
    return stat['returncode'], stat


def configPNS(d=None):
    """ Configure the PNS itself by replacing the pnsconfig var
    """
    global pc
    logger.debug(str(d))
    logger.debug('before configering pns ' + str(pc))
    try:
        indata = deserializeClassID(d)
        pc = indata['input']
    except Exception as e:
        re = -1
        msg = str(e)
    else:
        re = pc
        msg = ''
    logger.debug('after configering pns ' + str(pc))

    return re, msg


def configPTS(d=None):
    """ Configure the Processing Task Software by running the config script. Ref init PTS.
    """

    logger.debug(str(d))
    indata = deserializeClassID(d)

    if hasattr(indata, '__iter__') and 'timeout' in indata:
        timeout = indata['timeout']
    else:
        timeout = pc['timeout']

    stat = _execute(pc['scripts']['config'], timeout=timeout)
    return stat['returncode'], stat


def uploadScript(op, d=None):
    """
    """

    return -1, 'not mplemented'


def cleanPTS(d):
    """ Removing traces of past runnings the Processing Task Software.
    """
    # timeout is imported and needs to be declared global if referenced in ifs

    logger.debug(str(d))
    indata = deserializeClassID(d)

    if hasattr(indata, '__iter__') and 'timeout' in indata:
        timeout = indata['timeout']
    else:
        timeout = pc['timeout']

    stat = _execute(pc['scripts']['clean'], timeout=timeout)
    return stat['returncode'], stat


def run(d):
    """ Generates a product by running script defined in the config as prog. Execution on the server host is in the pnshome directory and run result and status are returned.
    """
    return 0, ''


def testrun(d):
    """  Run 'hello' for testing, and as an example.
    """
    pi = checkpath(pc['paths']['inputdir'])
    po = checkpath(pc['paths']['outputdir'])
    if pi is None or po is None:
        abort(401)

    global lupd

    indata = deserializeClassID(d)
    logger.debug(indata)
    runner, cause = indata['creator'], indata['rootcause']
    contents = indata['input']['theName'].data
    for f in pc['paths']['inputfiles']:
        fp = pi.joinpath(f)
        if fp.exists():
            logger.debug('infile mode 0%o ' % (fp.stat().st_mode))
        try:
            if fp.exists():
                fp.rename(str(fp) + '.old')
            with fp.open(mode="w+") as inf:
                inf.write(contents)
        except Exception as e:
            return -1, str(e) + ' '.join([x for x in
                                          traceback.extract_tb(e.__traceback__).format()])

    ######### run PTS ########
    if hasattr(indata, '__iter__') and 'timeout' in indata:
        timeout = indata['timeout']
    else:
        timeout = pc['timeout']

    stat = _execute(pc['scripts']['prog'], timeout=timeout)
    if stat['returncode'] != 0:
        return stat['returncode'], stat

    ######### output ########
    try:
        with po.joinpath(pc['paths']['outputfile']).open("r") as outf:
            res = outf.read()
    except Exception as e:
        return -1, str(e)

    x = Product(description="hello world pipeline product",
                creator=runner, rootCause=cause,
                instrument="hello", modelName="you know what!")
    x['theAnswer'] = GenericDataset(
        data=res, description='result from hello command')
    now = time.time()
    x.creationDate = FineTime1(datetime.datetime.fromtimestamp(now))
    x.type = 'test'
    x.history = History()
    return x, stat


def calc(d):
    """ generates result product directly using data on PNS.
    """
    return 0, ''


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
    input = indata['input']
    pname, pv = list(input.meta.items())[0]
    dname, dv = list(input.getDataWrappers().items())[0]
    # print(im == dv)  # this should be true
    x.meta[pname] = pv
    x[dname] = dv
    s1 = [dict(name='col1', unit='keV', column=[1, 4.4, 5.4E3]),
          dict(name='col2', unit='cnt', column=[0, 43.2, 2E3])]
    spec = TableDataset(data=s1)
    x.set('QualityImage', 'aQualityImage')
    x["Spectrum"] = spec
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


@app.route(pc['baseurl'] + '/<string:cmd>', methods=['GET'])
def getinfo(cmd):
    ''' returns init, config, run input, run output.
    '''
    logger.debug('getr %s' % (cmd))

    msg = ''
    ts = time.time()
    try:
        if cmd == 'init':
            with open(pc['scripts']['init'][0], 'r') as f:
                result = f.read()
        elif cmd == 'config':
            with open(pc['scripts']['config'][0], 'r') as f:
                result = f.read()
        elif cmd == 'prog':
            with open(pc['scripts']['prog'][0], 'r') as f:
                result = f.read()
        elif cmd == 'clean':
            with open(pc['scripts']['clean'][0], 'r') as f:
                result = f.read()
        elif cmd == 'input':
            result, msg = filesin(pc['paths']['inputdir'])
        elif cmd == 'output':
            result, msg = filesin(pc['paths']['outputdir'])
        elif cmd == 'pnsconfig':
            result, msg = pc, ''
        else:
            result, msg = 'init, confg, prog, input, ouput', 'get API'
    except Exception as e:
        result, msg = -1, str(e)
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
    return username == pc['node']['username'] and password == pc['node']['password']


@app.route(pc['baseurl'] + '/<string:cmd>', methods=['POST'])
def calcresult(cmd):

    logger.debug('pos ' + cmd)
    d = request.get_data()
    if cmd == 'calc':
        result, msg = calc(d)
    if cmd == 'testcalc':
        # see test_post() in test_all.py
        result, msg = genposttestprod(d)
    elif cmd == 'echo':
        # see test_mirror() in test_all.py
        indata = deserializeClassID(d)
        logger.debug(indata)
        result, msg = indata, ''
    elif cmd == 'run':
        result, msg = run(d)
    elif cmd == 'testrun':
        # see test_run() in test_all.py
        result, msg = testrun(d)
    else:
        logger.error(cmd)
        abort(400)
        result = None
    ts = time.time()
    w = {'result': result, 'message': msg, 'timestamp': ts}
    s = serializeClassID(w)
    logger.debug(s[:160] + ' ...')
    resp = make_response(s)
    resp.headers['Content-Type'] = 'application/json'
    return resp


@app.route(pc['baseurl'] + '/<string:cmd>', methods=['PUT'])
@app.route(pc['baseurl'] + '/<string:cmd>/<ops>', methods=['PUT'])
def setup(cmd):
    """ PUT is used to initialize or configure the Processing Task Software
    (PST).
    """

    d = request.get_data()
    logger.debug(d)
    if cmd == 'init':
        try:
            result, msg = initPTS(d)
        except Exception as e:
            msg = str(e)
            logger.error(msg)
            result = -1
    elif cmd == 'config':
        result, msg = configPTS(d)
    elif cmd == 'pnsconf':
        result, msg = configPNS(d)
    elif cmd == 'upload':
        if ops not in pc['scripts'].keys():
            logger.error('invalid operation type ' + ops)
            abort(400)
            result = None
        result, msg = uploadScript(ops, d)
    elif cmd == 'inittest':
        result, msg = initTest(d)
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


@app.route(pc['baseurl'] + '/<string:cmd>', methods=['DELETE'])
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
         'cmds': {'init': 'the initPTS file', 'config': 'the configPTS file',
                  'prog': 'the file running PTS', 'clean': 'the cleanPTS file',
                  'input': filesin, 'output': filesin,
                  'pnsconfig': 'PNS configuration'}
         },
        'PUT':
        {'func': 'setup',
         'cmds': {'init': initPTS, 'config': configPTS, 'pnsconf': configPNS, 'inittest': initTest}
         },
        'POST':
        {'func': 'calcresult',
         'cmds': {'calc': calc, 'testcalc': genposttestprod, 'echo': 'Echo',
                  'run': run, 'testrun': testrun}
         },
        'DELETE':
        {'func': 'cleanup',
         'cmds': {'clean': cleanPTS}
         }}


def makepublicAPI(ops):
    api = []
    o = APIs[ops]
    for cmd in o['cmds'].keys():
        c = o['cmds'][cmd]
        desc = c.__doc__ if isinstance(c, types.FunctionType) else c
        d = {}
        d['description'] = desc
        d['URL'] = url_for(o['func'],
                           cmd=cmd,
                           _external=True)
        api.append(d)
    #print('******* ' + str(api))
    return api


@app.route(pc['baseurl'] + '/', methods=['GET'])
@app.route(pc['baseurl'] + '/api', methods=['GET'])
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
