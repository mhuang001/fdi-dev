#! /usr/bin/python3.6

from fdi.pns.httppool_server import app
import sys
import os
import logging

# don't log to file. server will do the logging
logging.basicConfig(stream=sys.stdout,
                    format='%(levelname)4s'
                           ' -[%(filename)6s:%(lineno)3s'
                           ' -%(funcName)10s()] - %(message)s',
                    datefmt="%Y%m%d %H:%M:%S")
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# where user classes can be found
sys.path.insert(0, os.path.dirname(__file__))


app.secret_key = 'anything you wish'

application = app


def xapplication(req_environ, start_response):
    req_environ['SERVER_IP_ADDR'] = os.environ['SERVER_IP_ADDR']
    req_environ['SERVER_PORT'] = os.environ['SERVER_PORT']
    req_environ['PNSCONFIG'] = os.environ['PNSCONFIG']
    return app(req_environ, start_response)
