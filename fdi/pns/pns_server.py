# -*- coding: utf-8 -*-

from ..utils.common import trbk, trbk2, getUidGid, lls
from ..utils.run_proc import run_proc
from ..dataset.deserialize import deserialize
from ..dataset.serializable import serialize
from ..dataset.dataset import GenericDataset
from ..dataset.tabledataset import TableDataset
from ..dataset.product import Product
from ..dataset.finetime import FineTime1
from ..dataset.baseproduct import History

import datetime
import time
import pwd
import grp
import os
from os.path import isfile, isdir, join
from os import listdir
from pathlib import Path
from subprocess import Popen, PIPE, TimeoutExpired, run as srun
from flask import abort, make_response, request, jsonify
import filelock
import sys
import logging

# from .logdict import logdict
# '/var/log/pns-server.log'
# logdict['handlers']['file']['filename'] = '/tmp/server.log'


from .server_skeleton import init_conf_clas, makepublicAPI, checkpath, app
from ..utils import getconfig
pc = getconfig.getConfig()

logger = logging.getLogger(__name__)


@app.before_first_request
def init_pns_module():
    global Classes, pc

    Classes = init_conf_clas(pc)
    from ..dataset.classes import Classes

    ptsuid, ptsgid = getUidGid(pc['ptsuser'])
    uid, gid = getUidGid(pc['ptsuser'])
    sgroup = os.getgrouplist(pc['serveruser'], gid)
    if ptsgid not in sgroup:
        logger.error('ptsuser %s must be in the group of serveruser %s %s.' %
                     (pc['ptsuser'], pc['serveruser'], str(sgroup)))
        sys.exit(2)


def _execute(cmd, input=None, timeout=10):
    """ Executes a command on the server host in the pnshome directory and returns run status. Default imeout is 10sec. Run as user set byas.
    returns {return code, msg}
    """

    logger.debug('%s inp:%s tout: %d' %
                 (str(cmd), str(input), timeout))
    pwdir = pc['paths']['pnshome']
    as_user = pc['ptsuser']

    sta = run_proc(cmd, as_user, pwdir, timeout)
    return sta

    cp = srun(cmd, input=input, stdout=PIPE, stderr=PIPE,
              cwd=pc['paths']['pnshome'], timeout=timeout,
              encoding='utf-8', shell=True)  # universal_newlines=True)
    sta['stdout'], sta['stderr'] = cp.stdout, cp.stderr
    sta['returncode'] = cp.returncode
    return sta


def initPTS(d=None):
    """ Initialize the Processing Task Software by running the init script defined in the config. Execution on the server host is in the pnshome directory and run result and status are returned. If input/output directories cannot be created with serveruser as owner, Error401 will be given.
    """

    logger.debug(str(d))
    checkpath.cache_clear()

    pnsh = pc['paths']['pnshome']
    p = checkpath(pnsh, pc['serveruser'])
    if p is None:
        abort(401)

    pi = checkpath(pc['paths']['inputdir'], pc['serveruser'])
    if pi is None:
        abort(401)
    po = checkpath(pc['paths']['outputdir'], pc['serveruser'])
    if po is None:
        abort(401)

    indata = deserialize(d)

    if hasattr(indata, '__iter__') and 'timeout' in indata:
        timeout = indata['timeout']
    else:
        timeout = pc['timeout']

    stat = _execute(pc['scripts']['init'], timeout=timeout)
    return stat['returncode'], stat


def testinit(d=None):
    """     Renames the 'init' 'config' 'run' 'clean' scripts to '.save' and points it to the '.ori' scripts.
    """

    checkpath.cache_clear()

    pnsh = pc['paths']['pnshome']
    p = checkpath(pnsh, pc['serveruser'])
    if p is None:
        abort(401)

    pi = checkpath(pc['paths']['inputdir'], pc['serveruser'])
    po = checkpath(pc['paths']['outputdir'], pc['serveruser'])
    if pi is None or po is None:
        abort(401)

    # hf = pkg_resources.resource_filename("pns.resources", "runPTS")
    timeout = pc['timeout']
    scpts = [x[0] for x in pc['scripts'].values()]
    logger.debug('mv -f and ln -s :' + str())
    for ni in scpts:
        try:
            p = Path(ni)
            if not p.is_symlink:
                p.rename(ni + '.save')
            if not p.samefile(ni + '.ori'):
                p.unlink()
                p.symlink_to(ni + '.ori')
        except Exception as e:
            msg = 'rename or ln failed ' + str(e) + trbk(e)
            return -1,  msg
    return 0, ''


def configPNS(d=None):
    """ Configure the PNS itself by replacing the pnsconfig var
    """
    global pc
    logger.debug(str(d)[: 80] + '...')
    # logger.debug('before configering pns ' + str(pc))
    try:
        indata = deserialize(d)
        pc = indata['input']
    except Exception as e:
        re = -1
        msg = trbk2(e)
        logger.warning(trbk(e))
    else:
        re = pc
        msg = ''
    # logger.debug('after configering pns ' + str(pc))

    return re, msg


def configPTS(d=None):
    """ Configure the Processing Task Software by running the config script. Ref init PTS.
    """

    logger.debug(str(d))
    indata = deserialize(d)

    if hasattr(indata, '__iter__') and 'timeout' in indata:
        timeout = indata['timeout']
    else:
        timeout = pc['timeout']

    stat = _execute(pc['scripts']['config'], timeout=timeout)
    return stat['returncode'], stat


def uploadScript(op, d=None):
    """
    """

    return -1, 'not implemented'


def cleanPTS(d):
    """ Removing traces of past runnings the Processing Task Software.
    """
    # timeout is imported and needs to be declared global if referenced in ifs

    logger.debug(str(d))
    indata = deserialize(d)

    if hasattr(indata, '__iter__') and 'timeout' in indata:
        timeout = indata['timeout']
    else:
        timeout = pc['timeout']

    stat = _execute(pc['scripts']['clean'], timeout=timeout)
    return stat['returncode'], stat


def defaultprocessinput(data):
    """
    puts all undecoded json to every files.
    """

    pi = Path(pc['paths']['inputdir'])

    for f in data:
        fp = pi.joinpath(f)
        if fp.exists():
            logger.debug('infile mode 0%o ' % (fp.stat().st_mode))
            fp.rename(str(fp) + '.old')
        with fp.open(mode=data[f]['mode']) as inf:
            inf.write(data[f]['contents'])
    logger.debug(str(list(data.keys())) + ' written.')


def defaultprocessoutput(filemode):
    """
    reads each of the files and returns the contents in a filename indexed dict.
    """
    res = {}
    po = Path(pc['paths']['outputdir'])
    for fn in filemode:
        with po.joinpath(fn).open(mode=filemode[fn]) as outf:
            res[fn] = outf.read()
    logger.debug(str(list(res.keys())) + ' read.')
    return res


def testrun(d):
    """ server self-test: test run() with selected input/output.
    """
    logger.debug('for hello')

    def processinput(d, indata):
        """ put json decoded input.theName to file 'infile'
        """
        contents = indata['input']['theName'].data
        defaultprocessinput({'infile': {'contents': contents, 'mode': 'w+'}})

    def processoutput(d, indata):
        """ Read every file in pc.paths.output and put their contents in a dict. process the result to required form -- a product
        """
        res = defaultprocessoutput({'outfile': 'r'})

        runner, cause = indata['creator'], indata['rootcause']
        x = Product(description="test pipeline product",
                    creator=runner, rootCause=cause,
                    instrument="hello", modelName="you know what!")
        x['theAnswer'] = GenericDataset(
            data=res['outfile'], description='result from runPTS command')
        x.type = 'test'
        x.history = History()
        now = time.time()
        x.creationDate = FineTime1(datetime.datetime.fromtimestamp(now))
        return x

    return run(d, processinput, processoutput)


def run(d, processinput=None, processoutput=None):
    """  Generates a product by running script defined in the config under 'run'. Execution on the server host is in the pnshome directory and run result and status are returned.
    """

    global lupd

    pnsh = pc['paths']['pnshome']
    p = checkpath(pnsh, pc['serveruser'])
    if p is None:
        abort(401)

    pi = checkpath(pc['paths']['inputdir'], pc['serveruser'])
    po = checkpath(pc['paths']['outputdir'], pc['serveruser'])
    if pi is None or po is None:
        abort(401)

    indata = deserialize(d)

    try:
        if processinput is not None:
            processinput(d, indata)
        else:
            r1 = {'contents': indata['input'].toString(),
                  'mode': 'w+'}
            p = indata['input'].meta['pointing'].value.components
            r2 = {'contents': str(p[0]) + ' ' + str(p[1]),
                  'mode': 'w+'}
            data = {pc['paths']['inputfiles'][0]: r1,
                    pc['paths']['inputfiles'][1]: r2}
            defaultprocessinput(data)
    except Exception as e:
        return -1,  str(e) + trbk(e)

    ######### run PTS ########
    if hasattr(indata, '__iter__') and 'timeout' in indata:
        timeout = indata['timeout']
    else:
        timeout = pc['timeout']

    stat = _execute(pc['scripts']['run'], timeout=timeout)
    if stat['returncode'] != 0:
        return stat['returncode'], stat

    ######### output ########
    try:
        if processoutput is not None:
            x = processoutput(d, indata)
        else:
            n = len(pc['paths']['outputfiles'])
            fm = dict(zip(pc['paths']['outputfiles'], ['r'] * n))
            x = defaultprocessoutput(fm)
    except Exception as e:
        return -1, str(e) + trbk(e)

    return x, stat


def calc(d):
    """ generates result product directly using data on PNS.
    """
    return 0, ''


def genposttestprod(d):
    """ generate post test product.


    put the 1st input (see maketestdata in test_pns.py)
    parameter to metadata
    and 2nd to the product's dataset
    """

    indata = deserialize(d)
    # logger.debug(indata)

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
    # add some random dataset for good measure
    s1 = TableDataset(data=[('col1', [1, 4.4, 5.4E3], 'eV'),
                            ('col2', [0, 43.2, 2E3], 'cnt')
                            ])
    x['spectrum'] = s1
    now = time.time()
    x.creationDate = FineTime1(datetime.datetime.fromtimestamp(now))
    x.type = 'test'
    x.history = History()
    return x, ''


def dosleep(indata, ops):
    """ run 'sleep [ops]' in the OS. ops is 3 if not given.

    indata: possible {'timeout':xx}
    """
    logger.debug('dosleep %s, %s' % (str(indata), str(ops)))

    try:
        t = float(ops)
    except ValueError as e:
        t = 3
    if hasattr(indata, 'items') and 'timeout' in indata:
        timeout = indata['timeout']
    else:
        timeout = pc['timeout']

    stat = _execute(['sleep', str(t)], timeout=timeout)
    if stat['returncode'] != 0:
        return stat['returncode'], stat
    return 0, stat


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


@app.route(pc['baseurl'] + '/', methods=['GET'])
def get_apis():
    """ Makes a page for APIs described in module variable APIs. """

    logger.debug('APIs %s' % (APIs.keys()))
    l = [(a, makepublicAPI(o)) for a, o in APIs.items()]
    return jsonify(dict(l))


# @app.route(pc['baseurl'] + '/<string:cmd>', methods=['GET'])
def getinfo(cmd):
    ''' returns init, config, run input, run output.
    '''
    logger.debug('getr %s' % (cmd))

    msg = ''
    ts = time.time()

    try:
        if cmd == '' or cmd == 'api':
            return get_apis()
        elif cmd == 'init':
            with open(pc['scripts']['init'][0], 'r') as f:
                result = f.read()
            msg = "OK"
        elif cmd == 'config':
            with open(pc['scripts']['config'][0], 'r') as f:
                result = f.read()
            msg = "OK"
        elif cmd == 'run':
            with open(pc['scripts']['run'][0], 'r') as f:
                result = f.read()
            msg = "OK"
        elif cmd == 'clean':
            with open(pc['scripts']['clean'][0], 'r') as f:
                result = f.read()
            msg = "OK"
        elif cmd == 'input':
            result, msg = filesin(pc['paths']['inputdir'])
        elif cmd == 'output':
            result, msg = filesin(pc['paths']['outputdir'])
        elif cmd == 'pnsconfig':
            result, msg = pc, ''
        else:
            result, msg = -1, cmd + ' is not valid.'
    except Exception as e:
        result, msg = -1, str(e) + trbk(e)
    return result, msg


def calcresult(cmd, ops=''):
    d = request.get_data()
    if cmd == 'calc':
        result, msg = calc(d)
    elif cmd == 'testcalc':
        # see test_post() in test_all.py
        result, msg = genposttestprod(d)
    elif cmd == 'echo':
        # see test_mirror() in test_all.py
        indata = deserialize(d)
        # logger.debug(indata)
        result, msg = indata, ''
    # elif cmd == 'rmpool':
    #     # remove a pool
    #     ops = pc['poolprefix'] + '/' + ops
    #     if ops in pstore.getPool():
    #         pstore.getPools().remove(ops)
    #         result = ''
    #         msg = 'Pool ' + ops + ' remove OK.'
    #     else:
    #         result = 'FAILED'
    #         msg = 'Unable to remove pool : ' + ops + ' caused by ' + ops + ' not found.'
    else:
        # the following need to be locked
        pnsh = pc['paths']['pnshome']
        # check if it is locked with timeout==0
        lock = filelock.FileLock(pnsh + '/.lock', timeout=0)
        try:
            lock.acquire()
        except filelock.Timeout as e:
            logger.debug('busy')
            abort(409, 'pns is busy')
        with lock:
            if cmd == 'run':
                result, msg = run(d)
            elif cmd == 'testrun':
                # see test_testrun() in test_all.py
                result, msg = testrun(d)
            elif cmd == 'sleep':
                # sleep in the OS for ops seconds
                indata = deserialize(d)
                result, msg = dosleep(indata, ops)
            else:
                logger.error(cmd)
                abort(400)
                result = None
                msg = lls(result, 155)
    return result, msg


@app.route(pc['baseurl'] + '/<string:cmd>', methods=['GET', 'POST'])
@app.route(pc['baseurl'] + '/<string:cmd>/<string:ops>', methods=['POST'])
def get_post(cmd, ops=''):
    """ get and post.

    GET: returns init, config, run input, run output.
    POST:
    """

    logger.debug(request.method + ' ' + cmd + ' ' + ops)
    if request.method == 'POST':
        result, msg = calcresult(cmd, ops=ops)
    elif request.method == 'GET':
        if cmd in ['', '/', 'api']:
            return getinfo(cmd)
        result, msg = getinfo(cmd)
    else:
        raise RuntimeError('strange ' + request.method)
    ts = time.time()
    w = {'result': result, 'message': msg, 'timestamp': ts}
    s = serialize(w)
    logger.debug('serialized result: '+lls(s, 160))
    resp = make_response(s)
    resp.headers['Content-Type'] = 'application/json'
    return resp


@app.route(pc['baseurl'] + '/<string:cmd>', methods=['PUT'])
@app.route(pc['baseurl'] + '/<string:cmd>/<ops>', methods=['PUT'])
def setup(cmd, ops=''):
    """ PUT is used to initialize or configure the Processing Task Software
    (PST).
    """

    d = request.get_data()
    # logger.debug(d)

    # the following need to be locked
    pnsh = pc['paths']['pnshome']
    # check if it is locked with timeout==0
    lock = filelock.FileLock(pnsh + '/.lock', timeout=0)
    try:
        lock.acquire()
    except filelock.Timeout as e:
        logger.debug('busy')
        abort(409, 'pns is busy')
    with lock:
        checkpath.cache_clear()
        if cmd == 'init':
            try:
                result, msg = initPTS(d)
            except Exception as e:
                msg = str(e) + trbk(e)
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
        elif cmd == 'testinit':
            result, msg = testinit(d)
        else:
            logger.error(cmd)
            abort(400)
    ts = time.time()
    w = {'result': result, 'message': msg, 'timestamp': ts}
    s = serialize(w)
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
            msg = str(e) + trbk(e)
            logger.error(msg)
            result = None
    else:
        logger.error(cmd)
        abort(400)
        result = None
    ts = time.time()
    w = {'result': result, 'message': msg, 'timestamp': ts}
    s = serialize(w)
    logger.debug(s)
    resp = make_response(s)
    resp.headers['Content-Type'] = 'application/json'
    return resp


# API specification for this module
APIs = {'GET':
        {'func': 'get_post',
         'cmds': {'': get_apis, 'api': get_apis,
                  'init': 'the initPTS file', 'config': 'the configPTS file',
                  'run': 'the file running PTS', 'clean': 'the cleanPTS file',
                  'input': filesin, 'output': filesin,
                  'pnsconfig': 'PNS configuration'}
         },
        'PUT':
        {'func': 'setup',
         'cmds': {'init': initPTS, 'config': configPTS, 'pnsconf': configPNS, 'testinit': testinit}
         },
        'POST':
        {'func': 'get_post',
         'cmds': {'calc': calc, 'testcalc': genposttestprod,
                  'run': run, 'testrun': testrun,
                  'echo': 'Echo',
                  'sleep': (dosleep,  dict(ops='3'))}
         },
        'DELETE':
        {'func': 'cleanup',
         'cmds': {'clean': cleanPTS}
         }}


logger.debug('END OF '+__file__)
