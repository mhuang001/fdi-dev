# -*- coding: utf-8 -*-


from ..utils.getconfig import getConfig
from ..utils.common import lls
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

        
def set_session_pools(session, PM_S, old_ctx):

    logger = current_app.logger

    if not SESSION:
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug('Called with no SESSION')
        return

    GPL = PM_S._GlobalPoolList
    pools = session.get('registered_pools', {})
    nfound = 0
    for pn, pu in pools.items():
        if 0: #'ol_1' in pn:
            __import__("pdb").set_trace()

        if pn not in GPL:
            logger.info(f'{_RED}{pn} is not found in GPL.')
            #code, po, msg = register_pool(
            #    pn, current_app.config['USERS'][username], poolurl=pu)
            #assert po is GPL[pn]
        else:
            nfound += 1
            #assert pn in GPL
            gpu = GPL[pn]._poolurl
            if SES_DBG and logger.isEnabledFor(logging_DEBUG):
                logger.debug(f'GPL.p/u {lls(gpu,20)}{"==" if gpu == pu else "!="}cookie p/u {lls(pu,20)}.')
    logger.info(f"{nfound} of {len(pools)} pools in cookie found in GPL.") 
    if SES_DBG and logger.isEnabledFor(logging_DEBUG):
        from . import ctx
        from .model.user import auth
        _c1 = ctx(PM_S=PM_S, app=current_app, session=session, request=request, auth=auth)
        logger.debug(f"{_BLUE}Load_Ses {nfound} pools, {'ctx unchanged.' if old_ctx == _c1 else _c1}")
    return 

@session_api.before_app_request
def b4req_session():
    """ Every session keeps record of what pools it had
    registered in the last request, everyone makes the
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

    GPL = PM_S._GlobalPoolList

    if SES_DBG and logger.isEnabledFor(logging_DEBUG):
        from . import ctx
        from .model.user import auth
        _c = (ctx(PM_S=PM_S, app=current_app, session=session,
                   request=request, auth=auth))
        logger.debug(f"{_c}")
    #

        
def close_session(session, PM_S, old_ctx):

    logger = current_app.logger

    if not SESSION:
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug('Called with no SESSION')
        return resp

    # save session pools
    GPL = PM_S.getMap().maps[0]
    _d = {} if len(GPL) == 0 else dict((pn, x._poolurl) for pn, x in GPL.items())        
    session['registered_pools'] = _d
    session.modified = True

    # del g.user
    g.user = None
    
    _m = ''
    if SES_DBG and logger.isEnabledFor(logging_DEBUG):
        from . import ctx
        from .model.user import auth
        _c2 = ctx(PM_S=PM_S, app=current_app, session=session,
                  request=request, auth=auth)
        _m = 'ctx unchanged.' if old_ctx == _c2 else _c2
    logger.debug(f"{_YELLOW}Updated SesPools {' '.join(session['registered_pools'])}. {_m}")


@session_api.after_app_request
def aftreq_session(resp):

    logger = current_app.logger

    if not SESSION:
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug('Called with no SESSION')
        return resp

    PM_S = PM_S_from_g(g)
    _c = None
    if SES_DBG and logger.isEnabledFor(logging_DEBUG):
        from . import ctx
        from .model.user import auth
        _c = ctx(PM_S=PM_S, app=current_app, session=session,
                         request=request, auth=auth)
        logger.debug(_c)

    close_session(session, PM_S, _c)
    
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


