# -*- coding: utf-8 -*-


from ..utils.getconfig import getConfig
from ..pal.poolmanager import PM_S_from_g
from ..utils.colortext import (ctext,
                               _CYAN,
                               _GREEN,
                               _HIWHITE,
                               _WHITE_RED,
                               _YELLOW,
                               _MAGENTA,
                               _BLUE_DIM,
                               _BLUE,
                               _RED,
                               _BLACK_RED,
                               _RESET
                               )
from ..utils.common import (logging_ERROR,
                             logging_WARNING,
                             logging_INFO,
                             logging_DEBUG
                             )

from flask import g, Blueprint, jsonify, request, current_app, url_for, abort, session
from flask.sessions import SessionMixin
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import requests
import secrets
from datetime import timedelta

pc = getConfig()

SESSION = True
SES_DBG = pc['ses_dbg']

session_api = Blueprint('session', __name__)

# enable session

#### for clients #####

TIMEOUT = pc['requests_timeout']
# default RETRY_AFTER_STATUS_CODES = frozenset({413, 429, 503})
FORCED = None #(503, 504, 408, 413, 429)
# default DEFAULT_ALLOWED_METHODS = frozenset({'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PUT', 'TRACE'})
# METHODS = ("POST", "PUT", "HEAD", "GET", "OPTIONS")
METHODS = ("GET",)
# 0 means disabled
MAX_RETRIES = 0

@session_api.before_app_request
def b4req_session():
    """ Every session keeps record of what pools it had
    registered is the last request, everyone make the
    record when leaving a request, and registers when
    entering a request when current Poolmanager does not
    have the pool.
    """
    #from .route.pools import register_pool

    logger = current_app.logger

    PM_S = PM_S_from_g(g)
    
    if not SESSION:
        if logger.isEnabledFor(logging_DEBUG):
            logger.warning('Called with no SESSION')
        return

    pools = session.get('registered_pools', {})
    GPL = PM_S._GlobalPoolList

    if SES_DBG and logger.isEnabledFor(logging_DEBUG):
        from . import ctx
        from .model.user import auth
        _c =  (ctx(PM_S=PM_S, app=current_app, session=session,
                   request=request, auth=auth))
        logger.debug(f"{_c}")
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
            gpu = GPL[pn]._poolurl
            logger.info(f'GPL.purl {gpu}{"==" if gpu == pu else "!="}cookie {pu}.')

    if SES_DBG and logger.isEnabledFor(logging_DEBUG):
        from .model.user import auth
        from . import ctx
        _c =  (ctx(PM_S=PM_S, app=current_app, session=session, request=request, auth=auth))
        logger.debug(f"{_BLUE}Load_Ses, {_c}")
    return 

@session_api.after_app_request
def aftreq_session(resp):

    logger = current_app.logger

    if not SESSION:
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug('Called with no SESSION')
        return resp

    PM_S = PM_S_from_g(g)

    if SES_DBG and logger.isEnabledFor(logging_DEBUG):
        from . import ctx
        from .model.user import auth
        logger.debug(ctx(PM_S=PM_S, app=current_app, session=session,
                         request=request, auth=auth))

    GPL = PM_S.getMap().maps[0]
    session['registered_pools'] = dict((pn, x._poolurl) for pn, x in GPL.items())
    session.modified = True
    logger.debug(f"Updated SesPools {_YELLOW}{' '.join(session['registered_pools'])}")

    if SES_DBG and logger.isEnabledFor(logging_DEBUG):
        logger.debug(ctx(PM_S=PM_S, app=current_app, session=session,
                         request=request, auth=auth))
    
    return resp


def requests_retry_session(
        retries=MAX_RETRIES,
        backoff_factor=3,
        status_forcelist=FORCED,
        method_whitelist=METHODS,
        session=None,
        app=None
):
    """ session made with retries

    https://www.peterbe.com/plog/best-practice-with-retries-with-requests
    """
    session = session if session is not None else requests.session()

    if retries:

        retry = Retry(
            total=retries,
            read=retries,
            status=retries,
            connect=retries,
            other=None,
            redirect=5,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            raise_on_redirect=False,
            raise_on_status=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
    return session


#### for server #####
class Session(dict, SessionMixin):
    pass

def init_session(app):
    if not SESSION:
        return None

    sess = Session()
    app.secret_key = secrets.token_hex()
    app.config["SESSION_PERMANENT"] = True
    app.config["SESSION_REFRESH_EACH_REQUEST"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = 'LAX'
    app.permanent_session_lifetime = timedelta(days=1)
    app.config["SESSION_TYPE"] = "filesystem"
    # set `retries` to `False` to disable retrying.
    session = requests_retry_session(
        retries=False, backoff_factor=0.1, app=app, session=sess)
    # session = requests.Session(app)  #
    return session


