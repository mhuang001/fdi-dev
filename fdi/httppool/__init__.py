
# -*- coding: utf-8 -*-

""" https://livecodestream.dev/post/python-flask-api-starter-kit-and-project-layout/ """

from .route.getswag import swag

from .._version import __version__
from ..utils import getconfig
from ..utils.common import (getUidGid,
                            trbk,
                            logging_ERROR,
                            logging_WARNING,
                            logging_INFO,
                            logging_DEBUG
                            )

from ..pal.poolmanager import PoolManager, DEFAULT_MEM_POOL

from flasgger import Swagger
from werkzeug.exceptions import HTTPException
from flask import Flask, make_response, jsonify
from werkzeug.routing import RequestRedirect
from werkzeug.routing import RoutingException, Map

import builtins
from datetime import timedelta
from os.path import expandvars
from weakref import WeakValueDictionary, getweakrefcount
import functools
from pathlib import Path
import sys
import json
import time
import os

# print(sys.path)
global logger

LOGGING_NORMAL = logging_INFO
""" routine logging level."""


class PM_S(PoolManager):
    """Made to provid a different `_GlobalPoolList` useful for testing as a mock"""
    _GlobalPoolList = WeakValueDictionary()
    """ Another Global centralized dict that returns singleton -- the same -- pool for the same ID."""


def setup_logging(level=None, extras=None, tofile=None):
    import logging
    from logging.config import dictConfig
    from logging.handlers import QueueListener
    import queue
    que = queue.Queue(-1)  # no limit on size

    if extras is None:
        extras = LOGGING_NORMAL
    short = dict(format='%(asctime)s.%(msecs)03d'
                 ' %(levelname)4s'
                 ' %(filename)6s:%(lineno)3s'
                 ' - %(message)s',
                 datefmt="%y%m%d %H:%M:%S")
    detailed = dict(format='%(asctime)s.%(msecs)03d'
                    ' %(process)d %(thread)6d '
                    ' %(levelname)4s'
                    ' %(filename)6s:%(lineno)3s'
                    ' %(funcName)10s() - %(message)s',
                    datefmt="%Y%m%d %H:%M:%S")
    basedict = {
        'version': 1,
        'formatters': {'default': detailed, 'short': short},
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default'
            },
            'non_block': {
                'class': 'logging.handlers.QueueHandler',
                # 'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default',
                'queue': que,
            },

        },
        "loggers": {
            "werkzeug": {
                "level": LOGGING_NORMAL,
                "handlers": ["non_block"],
                "propagate": False
            }
        },
        'root': {
            'level': LOGGING_NORMAL,
            'handlers': ['wsgi']
        },
        'disable_existing_loggers': False
    }
    if tofile:
        basedict['handlers']['stream'] = {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            #level   : INFO
            #filters: [allow_foo]
            'stream': open(tofile, 'a')
        }
        basedict['root']['handlers'].append('stream')
    dict_config = dictConfig(basedict)

    if level is None:
        level = LOGGING_NORMAL
    if level < LOGGING_NORMAL:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logging_listener = QueueListener(
            que, handler, respect_handler_level=True)
        logging_listener.start()
    #logging.basicConfig(stream=sys.stdout, **detailed)
    # create logger
    if 0:
        for mod in ("requests", "filelock", ):
            logging.getLogger(mod).setLevel(extras)
        # logging.getLogger("werkzeug").setLevel(extras)
        if sys.version_info[0] > 2:
            logging.getLogger("urllib3").setLevel(extras)
    return logging

########################################
#### Config initialization Function ####
########################################


def init_conf_classes(pc, lggr):

    # setup user class mapping
    clp = pc['userclasses']
    lggr.debug('User class file '+clp)
    if clp == '':
        from ..dataset.classes import Classes as clz
        _bltn = dict((k, v) for k, v in vars(builtins).items() if k[0] != '_')
        clz.mapping.add_ns(_bltn, order=-1)
        return clz
    else:
        clpp, clpf = os.path.split(clp)
        sys.path.insert(0, os.path.abspath(clpp))
        # print(sys.path)
        # get the 'ProjectClasses' attribute
        projectclasses = __import__(clpf.rsplit('.py', 1)[0],
                                    globals(), locals(),
                                    ['ProjectClasses'], 0)
        clz = projectclasses.ProjectClasses
        lggr.debug('User classes: %d found.' % len(clz.mapping))
        return clz


SET_OWNER_MODE = False


@functools.lru_cache(6)
def checkpath(path, un):
    """ Checks  the directories and creats if missing.

    path: str. can be resolved with Path.
    un: server user name
    """
    #logger = current_app.logger

    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('path %s user %s' % (path, un))

    p = Path(path).resolve()
    if p.exists():
        if not p.is_dir():
            if logger.isEnabledFor(logging_ERROR):
                msg = str(p) + ' is not a directory.'
                logger.error(msg)
            return None
        else:
            # if path exists and can be set owner and group
            if p.owner() != un or p.group() != un:
                if logger.isEnabledFor(logging_WARNING):
                    msg = str(p) + ' owner %s group %s. Should be %s.' % \
                        (p.owner(), p.group(), un)
                    logger.warning(msg)
    else:
        # path does not exist

        if logger.isEnabledFor(logging_DEBUG):
            msg = str(p) + ' does not exist. Creating...'
            logger.debug(msg)
        p.mkdir(mode=0o775, parents=True, exist_ok=True)
        if logger.isEnabledFor(logging_INFO):
            logger.info(str(p) + ' directory has been made.')

    # logger.info('Setting owner, group, and mode...')
    if SET_OWNER_MODE and not setOwnerMode(p, un, logger):
        if logger.isEnabledFor(logging_INFO):
            logger.info('Cannot set owner %s to %s.' % (un, str(p)))
        return None

    return p


def setOwnerMode(p, username, logger):
    """ makes UID and GID set to those of self_username given in the config file. This function is usually done by the init script.
    """

    logger.debug('set owner, group to %s, mode to 0o775' % username)

    uid, gid = getUidGid(username)
    if uid == -1 or gid == -1:
        logger.debug(f'user {username} uid={uid} gid{gid}')
        return None
    try:
        os.chown(str(p), uid, gid)
        os.chmod(str(p), mode=0o775)
    except Exception as e:
        code, result, msg = excp(
            e,
            msg='cannot set dirs owner to ' +
            username + ' or mode. check config. ')
        logger.error(msg)
        return None

    return username


def init_httppool_server(app):
    """ Init a global HTTP POOL """

    # get settings from ~/.config/pnslocal.py config
    pc = app.config['PC']
    logger = app.logger
    # class namespace
    Classes = init_conf_classes(pc, logger)
    app.config['LOOKUP'] = Classes.mapping

    # client users
    from .model.user import getUsers
    app.config['USERS'] = getUsers(app)

    # PoolManager is a singleton
    if PM_S.isLoaded(DEFAULT_MEM_POOL):
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug('cleanup DEFAULT_MEM_POOL')
        PM_S.getPool(DEFAULT_MEM_POOL).removeAll()
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('Done cleanup PoolManager.')
        logger.debug('ProcID %d. Got 1st request %s' %
                     (os.getpid(), str(app._got_first_request))
                     )
    PM_S.removeAll()

    # pool-related paths
    # the httppool that is local to the server
    scheme = 'server'
    _basepath = PM_S.PlacePaths[scheme]
    # this is SERVER_LOCAL_POOLPATH/data
    full_base_local_poolpath = os.path.join(_basepath, pc['api_version'])

    if checkpath(full_base_local_poolpath, pc['self_username']) is None:
        msg = 'Store path %s unavailable.' % full_base_local_poolpath
        logger.error(msg)
        return None

    app.config['POOLSCHEME'] = scheme

    # e.g. "/tmp/data/v0.13"
    app.config['FULL_BASE_LOCAL_POOLPATH'] = full_base_local_poolpath
    app.config['POOLURL_BASE'] = scheme + \
        '://' + full_base_local_poolpath + '/'


######################################
#### Application Factory Function ####
######################################

LOGGING_DETAILED = logging_DEBUG


def create_app(config_object=None, debug=LOGGING_NORMAL, logstream=None):
    """ If args have logger level, use it; else if 
 use 'development' pnslocal.py config.

    :debug: level if `int`, name of modules that are set to givren level.
    """
    config_object = config_object if config_object else getconfig.getConfig()

    global logger
    _d = os.environ.get('PNS_DEBUG', debug)

    if isinstance(_d, str):
        try:
            _d = int(_d)
        except TypeError:
            # must come from env -- ',' separated module list
            _d = _d.split(',')
    if isinstance(_d, list):
        debug_picked = _d
        level_picked = LOGGING_DETAILED
    else:
        # level number in str
        level_picked = _d
        debug_picked = []
    debug_picked.append('')
    logging = setup_logging(level=level_picked,
                            extras=int(config_object['logger_level_extras']),
                            tofile=logstream)
    logger = logging.getLogger('fdi.httppool_app')

    debug = (level_picked < logging_INFO)
    if debug_picked:
        for mod in debug_picked:
            mod = mod.strip()
            if not mod:
                continue
            if mod.startswith('='):
                logging.getLogger(mod[1:]).setLevel(LOGGING_NORMAL)
            else:
                logging.getLogger(mod).setLevel(level_picked)
    if 0:  # turn off picked as server code use current_app.logger!
        level = LOGGING_NORMAL
    else:
        level = level_picked
    logger.setLevel(level)
    # app = Flask('HttpPool', instance_relative_config=False,
    #            root_path=os.path.abspath(os.path.dirname(__file__)))
    app = Flask(__name__.split('.')[0], instance_relative_config=False,
                root_path=os.path.abspath(os.path.dirname(__file__)))
    app.logger = logger
    app.config_object = config_object
    app.config['LOGGER_LEVEL'] = level

    if os.environ.get('UW_DEBUG', False) in (1, '1', 'True', True):
        from remote_pdb import RemotePdb
        RemotePdb('127.0.0.1', 4444).set_trace()

    if debug:
        from werkzeug.debug import DebuggedApplication
        app.wsgi_app = DebuggedApplication(app.wsgi_app, True)
        app.debug = True
        logger.info('DEBUG mode %s' % (app.config['DEBUG']))
        app.config['PROPAGATE_EXCEPTIONS'] = True
    elif 'proxy_fix' in app.config:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(
            app.wsgi_app, **app.config['proxy_fix']
        )
    # from flask.logging import default_handler
    # app.logger.removeHandler(default_handler)

    app.config['SWAGGER'] = {
        'title': 'FDI %s HTTPpool Server' % __version__,
        'universion': 3,
        'openapi': '3.0.4',
        'specs_route': '/apidocs/',
        'url_prefix': config_object['api_base']
    }
    swag['servers'].insert(0, {
        'description': 'As in config file and server command line.',
        'url': config_object['scheme']+'://' +
        config_object['self_host'] + ':' +
        str(config_object['self_port']) +
        config_object['baseurl']
    })
    swagger = Swagger(app, config=swag, merge=True)
    # swagger.config['specs'][0]['route'] = config_object['api_base'] + s1
    app.config['PC'] = config_object

    # initialize_extensions(app)
    # register_blueprints(app)

    from .model.user import user, SESSION
    app.register_blueprint(user, url_prefix=config_object['baseurl'])

    from .route.pools import pools_api
    app.register_blueprint(pools_api, url_prefix=config_object['baseurl'])
    from .route.httppool_server import data_api
    app.register_blueprint(data_api, url_prefix=config_object['baseurl'])

    # for sessions
    if SESSION:
        import secrets
        app.secret_key = secrets.token_hex()
        app.permanent_session_lifetime = timedelta(days=1)

    from .model.user import LOGIN_TMPLT
    if LOGIN_TMPLT:
        @app.errorhandler(401)
        @app.errorhandler(403)
        def handle_auth_error_codes(error):
            """ if verify_password returns False, this gets to run. """
            if error in [401, 403]:
                # send a login page
                if app.logger.isEnabledFor(logging_ERROR):
                    app.logger.error("Error %d. Start login page..." % error)
                page = make_response(render_template(LOGIN_TMPLT))
                return page
            else:
                raise ValueError('Must be 401 or 403. Nor %s' % str(error))

    # handlers for exceptions and some code
    add_errorhandlers(app)

    # Do not redirect a URL ends with no spash to URL/
    app.url_map.strict_slashes = False

    # with app.app_context():
    init_httppool_server(app)
    logger.info('Server initialized. logging level ' +
                str(app.logger.getEffectiveLevel()))

    return app


def add_errorhandlers(app):
    @app.errorhandler(Exception)
    def handle_excep(error):
        """ ref flask docs """
        ts = time.time()

        if issubclass(error.__class__, HTTPException) and error.code == 429:
            msg = "429 "
            error.code = 401
            response = make_response('', error)
        elif issubclass(error.__class__, HTTPException):
            if error.code == 409:
                spec = "Conflict or updating. "
            elif error.code == 500 and error.original_exception:
                error = error.original_exception
            else:
                spec = ''
            response = error.get_response()
            t = ' Traceback: ' + trbk(error)
            msg = '%s%d. %s, %s\n%s' % \
                (spec, error.code, error.name, error.description, t)
        elif issubclass(error.__class__, Exception):
            response = make_response()
            t = 'Traceback: ' + trbk(error)
            msg = '%s. %s.\n%s' % (error.__class__.__name__,
                                   str(error), t)
        else:
            response = make_response('', error)
            msg = ''
        w = {'result': 'FAILED', 'msg': msg, 'time': ts}
        response.data = json.dumps(w)
        response.content_type = 'application/json'
        return response
