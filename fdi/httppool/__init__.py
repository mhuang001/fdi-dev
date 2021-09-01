# -*- coding: utf-8 -*-

""" https://livecodestream.dev/post/python-flask-api-starter-kit-and-project-layout/ """

from .route.getswag import swag
from .route.pools import pools_api
from .model.user import getUsers

from .route.httppool_server import data_api, checkpath

from .._version import __version__
from ..utils import getconfig
from ..utils.common import getUidGid
from ..pal.poolmanager import PoolManager as PM, DEFAULT_MEM_POOL

from flasgger import Swagger
from flask import Flask

import builtins
from collections import ChainMap
import sys
import os

# sys.path.insert(0, abspath(join(join(dirname(__file__), '..'), '..')))

# print(sys.path)
global logging


def setup_logging(level=None):
    import logging
    if level is None:
        level = logging.WARN
    # create logger
    logging.basicConfig(stream=sys.stdout,
                        format='%(asctime)s'
                        ' %(process)d %(thread)6d '
                        ' %(levelname)4s'
                        ' [%(filename)6s:%(lineno)3s'
                        ' %(funcName)10s()] - %(message)s',
                        datefmt="%Y%m%d %H:%M:%S")
    logging.getLogger("requests").setLevel(level)
    logging.getLogger("filelock").setLevel(level)
    if sys.version_info[0] > 2:
        logging.getLogger("urllib3").setLevel(level)
    return logging

########################################
#### Config initialization Function ####
########################################


def init_conf_classes(pc, lggr):

    from ..dataset.classes import Classes

    # setup user class mapping
    clp = pc['userclasses']
    lggr.debug('User class file '+clp)
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
        lggr.debug('User classes: %d found.' % len(pcs.PC.mapping))
    return Classes


def init_httppool_server(app):
    """ Init a global HTTP POOL """

    import logging
    app.logger = logging.getLogger(__name__)
    app.logger.setLevel(app.config['LOGGER_LEVEL'])

    # local.py config
    pc = app.config['PC']
    # class namespace
    Classes = init_conf_classes(pc, app.logger)
    lookup = ChainMap(Classes.mapping, globals(), vars(builtins))
    app.config['LOOKUP'] = lookup

    # users
    # effective group of current process
    uid, gid = getUidGid(pc['serveruser'])
    app.logger.info("Serveruser %s's uid %d and gid %d..." %
                    (pc['serveruser'], uid, gid))
    # os.setuid(uid)
    # os.setgid(gid)
    app.config['USERS'] = getUsers(pc)

    # PoolManager is a singleton
    if PM.isLoaded(DEFAULT_MEM_POOL):
        logger.debug('cleanup DEFAULT_MEM_POOL')
        PM.getPool(DEFAULT_MEM_POOL).removeAll()
    app.logger.debug('Done cleanup PoolManager.')
    app.logger.debug('ProcID %d. Got 1st request %s' % (os.getpid(),
                                                        str(app._got_first_request))
                     )
    PM.removeAll()

    # pool-related paths
    # the httppool that is local to the server
    scheme = 'server'
    _basepath = PM.PlacePaths[scheme]
    poolpath_base = os.path.join(_basepath, pc['api_version'])

    if checkpath(poolpath_base, pc['serveruser']) is None:
        app.logger.error('Store path %s unavailable.' % poolpath_base)
        sys.exit(-2)

    app.config['POOLSCHEME'] = scheme
    app.config['POOLPATH_BASE'] = poolpath_base
    app.config['POOLURL_BASE'] = scheme + '://' + poolpath_base + '/'


######################################
#### Application Factory Function ####
######################################


def create_app(config_object=None, logger=None):

    if logger is None:
        logging = setup_logging()
        logging.getLogger()
        # logger = globals()['logger']
        logger = logging.getLogger()

    app = Flask(__name__, instance_relative_config=True)
    app.config['SWAGGER'] = {
        'title': 'FDI %s HTTPpool Server' % __version__,
        'universion': 3,
        'openapi': '3.0.2',
    }
    swagger = Swagger(app, config=swag, merge=True)
    #swagger = Swagger(app)

    config_object = config_object if config_object else getconfig.getConfig()
    app.config['PC'] = config_object
    app.config['LOGGER_LEVEL'] = logger.getEffectiveLevel()
    #logging = setup_logging()
    with app.app_context():
        init_httppool_server(app)
    # initialize_extensions(app)
    # register_blueprints(app)

    app.register_blueprint(pools_api, url_prefix=config_object['baseurl'])
    app.register_blueprint(data_api, url_prefix=config_object['baseurl'])

    return app
