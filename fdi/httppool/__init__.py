# -*- coding: utf-8 -*-

""" https://livecodestream.dev/post/python-flask-api-starter-kit-and-project-layout/ """

from fdi.httppool.route.home import home_api, home_api2
from fdi.httppool.route.httppool_server import init_httppool_server, httppool_api

from fdi._version import __version__
from fdi.utils import getconfig
from flasgger import Swagger
from flask import Flask

import sys

#sys.path.insert(0, abspath(join(join(dirname(__file__), '..'), '..')))

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


######################################
#### Application Factory Function ####
######################################


def create_app(config_object=None, logger=None):

    if logger is None:
        logging = setup_logging()
        logging.getLogger()
        #logger = globals()['logger']
        logger = logging.getLogger()
    app = Flask(__name__, instance_relative_config=True)
    app.config['SWAGGER'] = {
        'title': 'FDI %s HTTPpool Server' % __version__,
    }
    swagger = Swagger(app)

    config_object = config_object if config_object else getconfig.getConfig()
    app.config['PC'] = config_object
    app.config['LOGGER_LEVEL'] = logger.getEffectiveLevel()
    #logging = setup_logging()
    with app.app_context():
        init_httppool_server()
    # initialize_extensions(app)
    # register_blueprints(app)

    app.register_blueprint(home_api, url_prefix='')
    app.register_blueprint(home_api2, url_prefix='')
    app.register_blueprint(httppool_api, url_prefix=config_object['baseurl'])

    return app
