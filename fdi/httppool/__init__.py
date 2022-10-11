# -*- coding: utf-8 -*-

""" https://livecodestream.dev/post/python-flask-api-starter-kit-and-project-layout/ """

from .route.getswag import swag

from .route.httppool_server import checkpath, PM_S

from .._version import __version__
from ..utils import getconfig
from ..utils.common import getUidGid, trbk
from ..pal.poolmanager import PoolManager, DEFAULT_MEM_POOL

from flasgger import Swagger
from werkzeug.exceptions import HTTPException
from flask import Flask, make_response, jsonify
from werkzeug.routing import RequestRedirect
from werkzeug.routing import RoutingException, Map

import builtins
from datetime import timedelta
from os.path import expandvars
import sys
import json
import time
import os

# print(sys.path)
global logging


def setup_logging(level=None, extras=None):
    import logging
    from logging.config import dictConfig
    from logging.handlers import QueueListener
    import queue
    que = queue.Queue(-1)  # no limit on size

    if extras is None:
        extras = logging.WARNING
    fmt = dict(format='%(asctime)s.%(msecs)03d'
               ' %(process)d %(thread)6d '
               ' %(levelname)4s'
               ' %(filename)6s:%(lineno)3s'
               ' %(funcName)10s() - %(message)s',
               datefmt="%Y%m%d %H:%M:%S")
    dict_config = dictConfig({
        'version': 1,
        'formatters': {'default': fmt},
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
            }
        },
        "loggers": {
            "werkzeug": {
                "level": "INFO",
                "handlers": ["non_block"],
                "propagate": False
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi']
        },
        'disable_existing_loggers': False
    })

    if level is None:
        level = logging.WARN
    if level < logging.WARN:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logging_listener = QueueListener(
            que, handler, respect_handler_level=True)
        logging_listener.start()
    #logging.basicConfig(stream=sys.stdout, **fmt)
    # create logger
    logging.getLogger("requests").setLevel(extras)
    logging.getLogger("filelock").setLevel(extras)
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
        from ..dataset.classes import Classes
        return Classes
    else:
        clpp, clpf = os.path.split(clp)
        sys.path.insert(0, os.path.abspath(clpp))
        # print(sys.path)
        # get the 'ProjectClasses' attribute
        projectclasses = __import__(clpf.rsplit('.py', 1)[0],
                                    globals(), locals(),
                                    ['ProjectClasses'], 0)
        Clz = projectclasses.ProjectClasses
        lggr.debug('User classes: %d found.' % len(Clz.mapping))
        return Clz


def init_httppool_server(app):
    """ Init a global HTTP POOL """

    # get settings from ~/.config/pnslocal.py config
    pc = app.config['PC']
    # class namespace
    Classes = init_conf_classes(pc, app.logger)
    _bltn = dict((k, v) for k, v in vars(builtins).items() if k[0] != '_')
    Classes.mapping.add_ns(_bltn, order=-1)
    app.config['LOOKUP'] = Classes.mapping

    # client users
    from .model.user import getUsers
    app.config['USERS'] = getUsers(app)

    # PoolManager is a singleton
    if PM_S.isLoaded(DEFAULT_MEM_POOL):
        logger.debug('cleanup DEFAULT_MEM_POOL')
        PM_S.getPool(DEFAULT_MEM_POOL).removeAll()
    app.logger.debug('Done cleanup PoolManager.')
    app.logger.debug('ProcID %d. Got 1st request %s' %
                     (os.getpid(), str(app._got_first_request))
                     )
    PM_S.removeAll()

    # pool-related paths
    # the httppool that is local to the server
    scheme = 'server'
    _basepath = PM_S.PlacePaths[scheme]
    full_base_local_poolpath = os.path.join(_basepath, pc['api_version'])

    if checkpath(full_base_local_poolpath, pc['self_username']) is None:
        msg = 'Store path %s unavailable.' % full_base_local_poolpath
        app.logger.error(msg)
        return None

    app.config['POOLSCHEME'] = scheme

    # e.g. "/tmp/data/v0.13"
    app.config['FULL_BASE_LOCAL_POOLPATH'] = full_base_local_poolpath
    app.config['POOLURL_BASE'] = scheme + \
        '://' + full_base_local_poolpath + '/'


######################################
#### Application Factory Function ####
######################################

def create_app(config_object=None, level=None, debug=False):
    """ If args have logger level, use it; else if 
 use 'development' pnslocal.py config.
    """
    config_object = config_object if config_object else getconfig.getConfig()

    logging = setup_logging(level)
    logger = logging.getLogger('httppool_app')
    if level is None:
        level = config_object['loggerlevel']
        #level = logging.WARNING
    logger.setLevel(level)
    app = Flask('HttpPool', instance_relative_config=False,
                root_path=os.path.abspath(os.path.dirname(__file__)))
    app.logger = logger
    app.config_object = config_object

    if debug:
        level = logging.DEBUG
        logger.setLevel(level)
        logger.info('DEBUG mode %s' % (app.config['DEBUG']))
        from werkzeug.debug import DebuggedApplication
        app.wsgi_app = DebuggedApplication(app.wsgi_app, True)
        app.debug = True
        app.config['PROPAGATE_EXCEPTIONS'] = True
    elif 'proxy_fix' in app.config:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(
            app.wsgi_app, **app.config['proxy_fix']
        )
    # from flask.logging import default_handler
    # app.logger.removeHandler(default_handler)
    app.config['LOGGER_LEVEL'] = logger.getEffectiveLevel()

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
        app.permanent_session_lifetime = timedelta(minutes=30)

    @app.errorhandler(401)
    @app.errorhandler(403)
    def hadle_auth_error_codes(error):
        """ if verify_password returns False, this gets to run. """
        if error in [401, 403]:
            # send a login page
            app.logger("Error %d. Start login page..." % error)
            page = make_response(render_template(LOGIN_TMPLT))
            return page
        else:
            raise ValueError('Must be 401 or 403. Nor %s' % str(error))

    # hadlers for exceptions and some code
    add_errorhandlers(app)

    # Do not redirect a URL ends with no spash to URL/
    app.url_map.strict_slashes = False

    with app.app_context():
        init_httppool_server(app)
    logger.info('Server initialized. logging level ' +
                str(app.logger.getEffectiveLevel()))

    return app


# @app.errorhandler(RequestRedirect)
# def handle_redirect(error):
#     __import__('pdb').set_trace()

#     spec = 'redirect'

def add_errorhandlers(app):
    @app.errorhandler(Exception)
    def handle_excep(error):
        """ ref flask docs """
        ts = time.time()

        if issubclass(error.__class__, HTTPException):
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
