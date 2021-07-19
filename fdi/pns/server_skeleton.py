# -*- coding: utf-8 -*-

from ..utils.common import trbk, getUidGid
from ..utils import getconfig

import time
import sys
import functools
import os
from os import chown, chmod
from pathlib import Path
import logging
import types
from flask import Flask, jsonify, abort, make_response, request, url_for
from flask_httpauth import HTTPBasicAuth

# logdict['handlers']['file']['filename'] = '/tmp/server.log'


logger = logging.getLogger(__name__)


app = Flask(__name__)
# app.config.from_object('fdi.pns.config')
# try:
#     app.config.from_envvar('PNSCONFIG')
#     pc = app.config['FLASK_CONF']
# except RuntimeError:
#     pc = getconfig.getConfig()

# main() program is supposed to have get CONFIG ready when this model is imported.
pc = getconfig.getConfig()

logger.debug("pc= %s" % pc)
auth = HTTPBasicAuth()


def init_conf_clas(pc0):
    global pc

    from ..dataset.classes import Classes
    pc = pc0
    # effective group of current process
    uid, gid = getUidGid(pc['serveruser'])
    logger.info("Serveruser %s's uid %d and gid %d..." %
                (pc['serveruser'], uid, gid))
    # os.setuid(uid)
    # os.setgid(gid)

    # setup user class mapping
    clp = pc['userclasses']
    logger.debug('User class file '+clp)
    if clp == '':
        Classes.updateMapping()
    else:
        clpp, clpf = os.path.split(clp)
        sys.path.insert(0, os.path.abspath(clpp))
        # print(sys.path)
        pcs = __import__(clpf.rsplit('.py', 1)[
            0], globals(), locals(), ['PC'], 0)
        pcs.PC.updateMapping()
        Classes.updateMapping(pcs.PC.mapping)
        logger.debug('User classes: %d found.' % len(pcs.PC.mapping))
    return Classes


def setOwnerMode(p, username):
    """ makes UID and GID set to those of serveruser given in the config file. This function is usually done by the initPTS script.
    """

    logger.debug('set owner, group to %s, mode to 0o775' % username)

    uid, gid = getUidGid(username)
    if uid == -1 or gid == -1:
        return None
    try:
        chown(str(p), uid, gid)
        chmod(str(p), mode=0o775)
    except Exception as e:
        msg = 'cannot set input/output dirs owner to ' + \
            username + ' or mode. check config. ' + str(e) + trbk(e)
        logger.error(msg)
        return None

    return username


@functools.lru_cache(6)
def checkpath(path, un):
    """ Checks  the directories and creats if missing.

    path: str. can be resolved with Path.
    un: server user name
    """
    logger.debug('path %s user %s' % (path, un))

    p = Path(path).resolve()
    if p.exists():
        if not p.is_dir():
            msg = str(p) + ' is not a directory.'
            logger.error(msg)
            return None
        else:
            # if path exists and can be set owner and group
            if p.owner() != un or p.group() != un:
                msg = str(p) + ' owner %s group %s. Should be %s.' % \
                    (p.owner(), p.group(), un)
                logger.warning(msg)
    else:
        # path does not exist

        msg = str(p) + ' does not exist. Creating...'
        logger.debug(msg)
        p.mkdir(mode=0o775, parents=True, exist_ok=True)
        logger.info(str(p) + ' directory has been made.')

    #logger.info('Setting owner, group, and mode...')
    if not setOwnerMode(p, un):
        return None

    logger.debug('checked path at ' + str(p))
    return p


# import requests
# from http.client import HTTPConnection
# HTTPConnection.debuglevel = 1

# @auth.verify_password
# def verify(username, password):
#     """This function is called to check if a username /
#     password combination is valid.
#     """
#     if not (username and password):
#         return False
#     return username == pc['node']['username'] and password == pc['node']['password']
@auth.verify_password
def verify_password(username, password):
    logger.debug('verify user/pass')
    if not (username and password):
        return False
    elif username == pc['auth_user'] and password == pc['auth_pass']:
        return True
    else:
        return False
    # else:
    #     password = str2md5(password)
    #     try:
    #         conn = mysql.connector.connect(host = pc['mysql']['host'], port=pc['mysql']['port'], user =pc['mysql']['user'], password = pc['mysql']['password'], database = pc['mysql']['database'])
    #         if conn.is_connected():
    #             logger.info("connect to db successfully")
    #             cursor = conn.cursor()
    #             cursor.execute("SELECT * FROM userinfo WHERE userName = '" + username + "' AND password = '" + password + "';" )
    #             record = cursor.fetchall()
    #             if len(record) != 1:
    #                 logger.info("User : " + username + " auth failed")
    #                 conn.close()
    #                 return False
    #             else:
    #                 conn.close()
    #                 return True
    #         else:
    #             return False
    #     except Error as e:
    #         logger.error("Connect to database failed: " +str(e))


def makepublicAPI(o):
    """ Provides API specification for command given. """
    api = []

    for cmd, cs in o['cmds'].items():
        if not issubclass(cs.__class__, tuple):  # e.g. 'run':run
            c = cs
            kwds = {}
        else:  # e.g. 'sleep': (dosleep, dict(ops='1'))
            c, kwds = cs
        desc = c.__doc__ if isinstance(c, types.FunctionType) else c
        d = {}
        d['description'] = desc
        d['URL'] = url_for(o['func'],
                           cmd=cmd,
                           **kwds,
                           _external=True)
        api.append(d)
    # print('******* ' + str(api))
    return api


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
def conflict(error):
    ts = time.time()
    w = {'error': 'Conflict. Updating.',
         'message': str(error), 'timestamp': ts}
    return make_response(jsonify(w), 409)


logger.debug('END OF '+__file__)
