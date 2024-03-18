# -*- coding: utf-8 -*-

""" https://livecodestream.dev/post/python-flask-api-starter-kit-and-project-layout/ """

# from traceback_with_variables import activate_by_import

from .route.getswag import swag

from .._version import __version__, __revision__
from ..utils import getconfig
from ..pal.poolmanager import DEFAULT_MEM_POOL, PM_S_from_g

from .session import init_session, SESSION, SES_DBG

from ..utils.common import (getUidGid,
                            trbk,
                            logging_ERROR,
                            logging_WARNING,
                            logging_INFO,
                            logging_DEBUG, lls
                            )
from ..utils.colortext import (ctext,
                               _CYAN,
                               _GREEN,
                               _HIWHITE,
                               _WHITE_RED,
                               _YELLOW,
                               _MAGENTA,
                               _BLUE,
                               _RED,
                               _BLACK_RED,
                               _RESET
                               )

from flasgger import Swagger
from werkzeug.exceptions import HTTPException
from flask import Flask, make_response, jsonify, request, current_app, g, session, app as _app
from werkzeug.routing import RequestRedirect
from werkzeug.routing import RoutingException, Map

import builtins
from os.path import expandvars
import functools
from pathlib import Path
import sys
import json
import time
import os
from collections import defaultdict

# print(sys.path)
global logger

LOGGING_NORMAL = logging_INFO
""" routine logging level."""

LOGGING_DETAILED = logging_DEBUG
""" usually set to debugging """

cnt = 0
_BASEURL = ''

PC = None
""" debug msg for session """

app = Flask(__name__.split('.')[0], instance_relative_config=False,
            root_path=os.path.abspath(os.path.dirname(__file__)))

def setup_logging(level=LOGGING_NORMAL, extras=None, tofile=None):
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
            # level   : INFO
            # filters: [allow_foo]
            'stream': open(tofile, 'a')
        }
        basedict['root']['handlers'].append('stream')
    dict_config = dictConfig(basedict)

    if level < LOGGING_NORMAL:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logging_listener = QueueListener(
            que, handler, respect_handler_level=True)
        logging_listener.start()
    # logging.basicConfig(stream=sys.stdout, **detailed)
    # create logger
    if 1:
        for mod in ("requests", "filelock", "_GPL"):
            logging.getLogger(mod).setLevel(extras)
        # logging.getLogger("werkzeug").setLevel(extras)
        if sys.version_info[0] > 2:
            logging.getLogger("urllib3").setLevel(extras)
    return logging

# for those who cannot wait for create_app to set up  logging
logging = setup_logging()

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
def checkpath(path, un=None):
    """ Checks  the directories and creats if missing.

    Parameters
    ----------
    path : str
        can be resolved with `Path`.
    un: str, None
        server user name set in the config file as, and is default to when set as `None`, `self_username`.
    """

    # logger = current_app.logger
    if un is None:
        un = getconfig.getConfig('self_username')
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


def init_httppool_server(app, preload, g):
    """ Init a global HTTP POOL """

    # get settings from ~/.config/pnslocal.py config
    pc = app.config['PC']
    logger = app.logger
    # class namespace
    Classes = init_conf_classes(pc, logger)
    app.config['LOOKUP'] = Classes.mapping
    global SES_DBG

    from ..utils.lock import makeLock
    # client users
    from .model.user import getUsers
    app.config['USERS'] = getUsers(pc)

    sid = hex(os.getpid())
    app.config['LOCKS'] = dict((op, makeLock('FDI_Pool'+sid, op))
                               for op in ('r', 'w'))

    # setup UNLOADED pools in poolmanager
    PM_S = init_poolmanager(app, g, pc, preload)

    
def init_poolmanager(app, g, pc, preload):

    # PoolManager is a singleton. get PM_S from 

    # with app.app_context():
    #    PM_S = PM_S_from_g(g)
    PM_S = PM_S_from_g(g)
    if PM_S.isLoaded(DEFAULT_MEM_POOL):
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug('cleanup DEFAULT_MEM_POOL')
        PM_S.getPool(DEFAULT_MEM_POOL).removeAll()
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('Done cleanup PoolManager.')
        logger.debug('ProcID %d. Got 1st request %s' %
                     (os.getpid(), str(app._got_first_request))
                     )
    try:
        PM_S.removeAll(include_read_only=False)
    except KeyError:
        pass
    app.config['POOLMANAGER'] = PM_S

    if preload:
        # initialize read-only pools
        from ..pal.productstorage  import ProductStorage
        ps = ProductStorage(poolmanager=PM_S)
        PM_S.getMap().UNLOADED.update(pc['read_only_pools'])

        logger.info('PM_S initializing..'+hex(id(PM_S._GlobalPoolList.maps[0])) + ' ' + str(PM_S()))
    
    # pool-related paths
    # the httppool that is local to the server
    scheme = 'server'

    # this is something like SERVER_LOCAL_POOLPATH, /.../v0.16
    # os.path.join(_basepath, pc['api_version'])
    full_base_local_poolpath = PM_S.PlacePaths[scheme]

    if checkpath(full_base_local_poolpath) is None:
        msg = 'Store path %s unavailable.' % full_base_local_poolpath
        logger.error(msg)
        return None

    app.config['POOLSCHEME'] = scheme

    # e.g. "/tmp/data/v0.16"
    app.config['FULL_BASE_LOCAL_POOLPATH'] = full_base_local_poolpath
    app.config['POOLURL_BASE'] = scheme + \
        '://' + full_base_local_poolpath + '/'
    return PM_S

######################################
#### Application Factory Function ####
######################################


def create_app(config_object=None, level=None, logstream=None, preload=False):
    """ If args have logger level, use it; else if debug is `True` set to 20
 use 'development' pnslocal.py config.

    :level: logging level. default `None`
    """
    config_object = config_object if config_object else getconfig.getConfig()

    global logger
    global _BASEURL
    
    
    _BASEURL = config_object['baseurl']
    _d = os.environ.get('PNS_DEBUG', None)
    _d = level if level else _d if _d else LOGGING_NORMAL

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
    if 0 and debug_picked:
        for mod in debug_picked:
            mod = mod.strip()
            if not mod:
                continue
            if mod.startswith('='):
                logging.getLogger(mod[1:]).setLevel(logging_WARNING)
            else:
                logging.getLogger(mod).setLevel(level_picked)

        level = LOGGING_NORMAL
    else:
        level = level_picked
    logger.setLevel(level)
    # app = Flask('HttpPool', instance_relative_config=False,
    #            root_path=os.path.abspath(os.path.dirname(__file__)))
    global app
    app.logger = logger
    app.config_object = config_object
    app.config['LOGGER_LEVEL'] = level

    if os.environ.get('UW_DEBUG', False) in (1, '1', 'True', True):
        from remote_pdb import RemotePdb
        #RemotePdb('127.0.0.1', 4444).set_trace()
        RemotePdb('localhost', 4444).set_trace()


    if debug:
        from werkzeug.debug import DebuggedApplication
        app.wsgi_app = DebuggedApplication(app.wsgi_app, True)
        app.debug = True
        logger.info('DEBUG mode %s' % (app.config['DEBUG']))
        app.config['PROPAGATE_EXCEPTIONS'] = True
    elif 'proxy_fix' in app.config_object:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, **app.config_object['proxy_fix'])

    app.config['PREFERRED_URL_SCHEME'] = config_object['scheme']
    #app.config['SERVER_NAME'] = f"{config_object['self_host']}:{config_object['self_port']}"
    app.config['APPLICATION_ROOT'] = config_object['baseurl']
    with app.test_request_context():
        app.config['REQUEST_BASE_URL'] = request.base_url

    # from flask.logging import default_handler
    # app.logger.removeHandler(default_handler)

    app.config['SWAGGER'] = {
        'title': 'FDI %s HTTPpool Server' % __revision__,
        'universion': 3,
        'openapi': '3.0.4',
        'specs_route': '/apidocs/',
        'url_prefix': _BASEURL
    }
    swag['servers'].insert(0, {
        'description': 'For clients external to CSDB.',
        'url': f"{config_object['url_aliases']['http']}"
        })
    swagger = Swagger(app, config=swag, merge=True)
    # swagger.config['specs'][0]['route'] = _BASEURL + s1
    app.config['PC'] = config_object

    # initialize_extensions(app)
    # register_blueprints(app)
    from .session import session_api
    app.register_blueprint(session_api, url_prefix=_BASEURL)

    from .model.user import user_api
    app.register_blueprint(user_api, url_prefix=_BASEURL)

    from .route.pools import pools_api
    app.register_blueprint(pools_api, url_prefix=_BASEURL)
    
    from .route.httppool_server import data_api
    app.register_blueprint(data_api, url_prefix=_BASEURL)

    from .model.user import LOGIN_TMPLT
    if 0: # LOGIN_TMPLT:
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
                raise ValueError('Must be 401 or 403. Not %s' % str(error))

    # handlers for exceptions and some code
    #add_errorhandlers(app)

    # Do not redirect a URL ends with no spash to URL/
    app.url_map.strict_slashes = False

    app.config['POOLS'] = {}
    app.config['ACCESS'] = {'usrcnt': defaultdict(int)}
    with app.app_context():
        # Flask proxy, NOT module variable holding initialized session
        session = init_session(current_app)
        init_httppool_server(current_app, preload, g)
    logger.info('Server initialized. logging level ' +
                str(app.logger.getEffectiveLevel()))
    app.config['SERVER_LOCKED'] = False
    
    return app

if 1:
    @app.before_request
    def b4req():
        global cnt
        #global session
        #global PM_S
        
        PM_S = PM_S_from_g(g)
        cnt += 1

        logger = current_app.logger

        locked = app.config['SERVER_LOCKED']

        if 0 and locked:
            if app.logger.isEnabledFor(logging_DEBUG):
                    app.logger.debug(f"System locked: {locked}")
            
            return jsonify ({"result": "BUSY",
                             "msg": "Server initializing or in maintenance.",
                             "ts": time.time()}), 409

        if logger.getEffectiveLevel() < logging.WARNING: 
            a = lls(request.view_args,50)
            # remove leading e.g. /fdi/v0.16
            s = request.path.split(_BASEURL)
            p = s[0] if len(s) == 1 else s[1] if s[0] == '' else request.path
            method = request.method
            if method == 'POST':
                d = f"data={lls(request.data,50)}"
            else:
                d = ''
            l = 'locked' if locked else 'notlocked'
            info = f"{cnt} {l}{_WHITE_RED}>>> [{method}] {lls(p, 50)}, {a}, {d}"
            if logger.getEffectiveLevel() < logging.INFO:
                #if SES_DBG and logger.isEnabledFor(logging_DEBUG):
                c = ctx(PM_S=PM_S, app=current_app, session=session, request=request, auth=None)
                info += c
            logger.info(info)

        pools = session.get('registered_pools', {})

        if SES_DBG and logger.isEnabledFor(logging_DEBUG):
            from .model.user import auth
            _c =  (ctx(PM_S=PM_S, app=current_app, session=session,
                       request=request, auth=auth))
            logger.debug(f"{_c}")
        if 0:
            GPL = PM_S.getMap().maps[0]
            for pn, pu in pools.items():
                if 0: #'ol_1' in pn:
                    __import__("pdb").set_trace()

                if pn not in GPL:
                    logger.info(f'{_RED}{pn} is not found in GPL.')
                    #code, po, msg = register_pool(
                    #    pn, current_app.config['USERS'][username], poolurl=pu)
                    #ssert po is GPL[pn]
                else:
                    #assert pn in GPL
                    logger.info(f'GPL.purl{"==" if GPL[pn]._poolurl == pu else "!="}cookie.')

        return

    @app.after_request
    def aftreq(resp):

        PM_S = PM_S_from_g(g)
        
        c = ctx(PM_S=None, app=current_app, session=session, request=request, auth=None)
        logger.debug(c)
        if  0:
            #from .model.user import save_registered_pools
            #resp = save_registered_pools(resp)
            GPL = PM_S.getMap().maps[0]
            session['registered_pools'] = dict((pn, x._poolurl) for pn, x in GPL.items())
            session.modified = True
            logger.debug(f"Updated SesPools{_YELLOW}{' '.join(session['registered_pools'])}")

        return resp

def ctx(PM_S, app, session, request, auth, **kwds):
    G = hex(id(PM_S.getMap().maps[0]))[-4:] if PM_S else "nul"
    _a = hex(id(app))[-4:]
    _r = hex(id(request))[-4:]
    _s = hex(id(session))[-4:]
    #_g = hex(id(g._get_current_object()))[-4:]
    _g = hex(id(g))[-4:]
    _ps = ' '.join(map(str, map(list,PM_S.getMap().maps))) if PM_S else "nul"
    _u = f"auth.cuser{auth.current_user()}" if auth else "no-auth"
    if hasattr(request, 'authorization'):
        _u += f" req.ausr={request.authorization['username']}" if request.authorization else "none"
    else:
        _u += "no-autho"
    m = f"{_MAGENTA}GPL:{_HIWHITE}{G} {_GREEN}{_ps}{_MAGENTA}, app:{_a} req:{_r} sess:{_HIWHITE}{_s}{_MAGENTA} g:{_g}"
    headers = dict(request.headers)
    cook = dict(request.cookies)
    user_id = getattr(session,'user_id', 'None')
    guser = getattr(g,'user', 'No g usr')
    m += (f" {_BLUE}Ses'{user_id}'>{current_app.config['ACCESS']['usrcnt'][user_id]} {headers.get('Authorization', '')[:12]}, gusr={guser} cookie.ses={cook.get('session', 'None')[-5:]}")
    return m

def add_errorhandlers(app):
    @app.errorhandler(Exception)
    def handle_excep(error):
        """ ref flask docs """

        ts = time.time()
        if issubclass(error.__class__, HTTPException):
            # https://flask.palletsprojects.com/en/latest/errorhandling/#generic-exception-handlers
            return error
        # non-HTTP exceptions:
            response = error.get_response()
            t = ' Traceback: ' + trbk(error)
            msg = '%s%d. %s, %s\n%s' % \
                (spec, error.code, error.name, error.description, t)
        elif issubclass(error.__class__, Exception):
            response = make_response(str(error), 500)
            t = 'Traceback: ' + trbk(error)
            msg = '%s. %s.\n%s' % (error.__class__.__name__,
                                   str(error), t)
        else:
            response = make_response('', error)
            msg = 'Untreated error type.'
        w = {'result': 'FAILED', 'msg': msg, 'time': ts}
        response.data = json.dumps(w)
        response.content_type = 'application/json'
        return response
