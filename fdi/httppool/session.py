# -*- coding: utf-8 -*-

from ..utils.getconfig import getConfig
from .model.user import SESSION

from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import requests
import secrets
from datetime import timedelta

pc = getConfig()

#### for clients #####

TIMEOUT = pc['requests_timeout']
# default RETRY_AFTER_STATUS_CODES = frozenset({413, 429, 503})
FORCED = (503, 504, 408, 413, 429)
# default DEFAULT_ALLOWED_METHODS = frozenset({'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PUT', 'TRACE'})
METHODS = ("POST", "PUT", "HEAD", "GET", "OPTIONS")
MAX_RETRY = 2


def requests_retry_session(
        retries=MAX_RETRY,
        backoff_factor=3,
        status_forcelist=FORCED,
        method_whitelist=METHODS,
        session=None,
        app=None
):
    """ session made with retries

    https://www.peterbe.com/plog/best-practice-with-retries-with-requests
    """
    session = session or requests.session()
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
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


#### for server #####

def init_session(app):
    if not SESSION:
        return None

    app.secret_key = secrets.token_hex()
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_COOKIE_SAMESITE"] = 'LAX'
    app.permanent_session_lifetime = timedelta(days=1)
    app.config["SESSION_TYPE"] = "filesystem"
    # set `retries` to `False` to disable retrying.
    session = requests_retry_session(
        retries=False, backoff_factor=0.1, app=app)
    # session = requests.Session(app)  #
    return session
