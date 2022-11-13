# -*- coding: utf-8 -*-

#from ..route.pools import pools_api

from flask import (
    Blueprint, flash, g, make_response, redirect, render_template, request, session, url_for
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, Response
from flask_httpauth import HTTPBasicAuth

import requests

import datetime
import time
import functools
import logging

logger = logging.getLogger(__name__)

auth = HTTPBasicAuth()

SESSION = True


user = Blueprint('user', __name__)


class User():

    def __init__(self, name,
                 password=None,
                 hashed_password=None,
                 role='read_only'):

        global logger

        self.username = name
        if hashed_password:
            if password:
                __import__('pdb').set_trace()

                logger.warning(
                    'Both password and hashed_password are given for %s. Password is igored.' % name)
                password = None
        elif password:
            hashed_password = self.hash_of(password)
        else:
            raise ValueError(
                'No password and no hashed_password given for ' + name)
        self.password = password
        self.registered_on = datetime.datetime.now()

        self.hashed_password = hashed_password
        self.role = role if issubclass(role.__class__, str) else tuple(role)
        self.authenticated = False

    def is_correct_password(self, plaintext_password):

        return check_password_hash(self.hashed_password, plaintext_password)

    @staticmethod
    @functools.lru_cache(maxsize=64)
    def hash_of(s):
        return generate_password_hash(s)

    def __repr__(self):
        return f'<User: {self.username}>'


def getUsers(app):
    """ Returns the USER DB from `config.py` ro local config file. """

    # pnsconfig from config file
    users = dict(((u['username'],
                  User(u['username'],
                       hashed_password=u['hashed_password'],
                       role=u['roles'])
                   ) for u in app.config['PC']['USERS']))

    return users


if SESSION:
    @user.before_app_request
    def load_logged_in_user():
        user_id = session.get('user_id')
        headers = str(request.headers)
        current_app.logger.debug('S:%x "%s"\n%s\n%s' %
                                 (id(session), str(user_id), str(headers), str(request.cookies)))
        if user_id is None:
            g.user = None
        else:
            g.user = current_app.config['USERS'][user_id]


@auth.get_user_roles
def get_user_roles(user):
    if issubclass(user.__class__, User):
        return user.role
    else:
        return None


LOGIN_TMPLT = 'user/login.html'


######################################
####  /login GET, POST  ####
######################################


@ user.route('/login', methods=['GET', 'POST'])
# @ auth.login_required(role=['read_only', 'read_write'])
def login():
    """ Logging in on the server.

    :return: response made from http code, poolurl, message
    """
    global logger
    logger = current_app.logger
    ts = time.time()
    acu = auth.current_user()

    try:
        reqanm = request.authorization['username']
        reqanm = request.authorization['passwd']
    except (AttributeError, TypeError):
        reqanm = reqaps = ''
    msg = 'LOGIN meth=%s req_auth_nm= "%s"' % (request.method, reqanm)
    logger.debug(msg)
    if reqanm == 'ro':
        __import__("pdb").set_trace()

    if request.method == 'POST':
        rnm = request.form.get('username', None)
        rpas = request.form.get('password', None)
        logger.debug(f'Request form {rnm}')

        if not (rpas and rnm):
            msg('Bad username or password posted %s' % str(rnm))
            logger.warning(msg)
            if reqanm and reqaps:
                msg = f'Username {reqanm} and pswd in auth header used.'
                logger.warning(msg)
                rnm, rpas = reqanm, reqaps

        vp = verify_password(rnm, rpas, check_session=False)
        if vp in (False, None):
            msg = f'Verifying {rnm} with password failed.'
            logger.debug(msg)
        else:
            if SESSION:
                session.clear()
                session['user_id'] = rnm
                session.modified = True
            msg = 'User %s logged-in %s.' % (rnm, vp.role)
            logger.debug(msg)
            # return redirect(url_for('pools.get_pools_url'))
            if SESSION:
                flash(msg)
            from ..route.httppool_server import resp
            return resp(200, 'OK.', msg, ts, req_auth=True)
    elif request.method == 'GET':
        logger.debug('start login page')
    else:
        logger.warning('How come the method is ' + request.method)
    if SESSION:
        flash(msg)
    return make_response(render_template(LOGIN_TMPLT))


######################################
####  /user/logout GET, POST  ####
######################################


@ user.route('/logout', methods=['GET', 'POST'])
# @ auth.login_required(role=['read_only', 'read_write'])
def logout():
    """ Logging in on the server.

    :return: response made from http code, poolurl, message
    """

    logger = current_app.logger
    ts = time.time()
    logger.debug('logout')
    # session.get('user_id') is the name

    if SESSION and hasattr(g, 'user') and hasattr(g.user, 'username'):
        nm, rl = g.user.username, g.user.role
        msg = 'User %s logged-out %s.' % (nm, rl)
        res = 'OK. Bye, %s (%s).' % (nm, rl)
    else:
        msg = 'User logged-out.'
        res = 'OK. Bye.'
    logger.debug(msg)
    if SESSION:
        session.clear()
        g.user = None
        session.modified = True

    from ..route.httppool_server import resp

    return resp(200, res, msg, ts)


@auth.verify_password
def verify_password(username, password, check_session=True):
    """ Call back.

    ref: https://flask-httpauth.readthedocs.io/en/latest/index.html

        must return the user object if credentials are valid,
        or True if a user object is not available. In case of 
        failed authentication, it should return None or False. 

    `check_session`=`True` ('u/k' means unknown)

    =========== ============= ======= ========== ========= ==================
    state          `session`   `g`     username  password      action
    =========== ============= ======= ========== ========= ==================
    no Session  no 'user_id'          not empty  valid     new session, r/t new u
    no Session  no 'user_id'          not empty  invalid   login, r/t `False`
    no Session  no 'user_id'          ''                   r/t None
    no Session  no 'user_id'          None, u/k            login, r/t `False`
    In session  w/ 'user_id'  ''|None not empty  valid     new session, r/t new u
    ..                                not same 
    In session  w/ 'user_id'          not empty  invalid   login, return `False`
    In session  w/ 'user_id'  user    None ""              login, return `False`
    ..                                u/k
    =========== ============= ======= ========== ========= ==================

    `check_session`=`False`

    ========== ========= =========  ================
     in USERS  username  password    action
    ========== ========= =========  ================
     False                          return False
     True      not empty  valid     return user
     True      not empty  invalid   return False
               ''                   return None
               None                 return False
    ========== ========= =========  ================

    No SESSION:

    > return `True`
    """

    logger = current_app.logger
    logger.info(f'!!!! {username} {password} chk={check_session} Se={SESSION}')
    if check_session:
        if SESSION:
            has_session = 'user_id' in session and hasattr(
                g, 'user') and g.user is not None
            if has_session:
                logger.info(f'has_session usr=%s g.u={g.user}' % (
                    session.get("user_id", "None")))
                user = g.user
                gname = user.username
                newu = current_app.config['USERS'].get(username, None)
                # first check if the username is actually unchanged and valid
                if newu is not None and newu.is_correct_password(password):
                    if gname == username:
                        logger.debug(f"Same session {gname}.")
                    else:
                        logger.debug(f"New session {username}.")
                        session.clear()
                        session['user_id'] = username
                        session.modified = True
                    return newu
                logger.debug(
                    f"Unknown {username} or Null or anonymous user, or new user '{username}' has invalid password.")
                return False
            else:
                # has no session
                logger.info('no session. has %s "user_id". has %s g. g.user= %s' % (
                    ('' if 'user_id' in session else 'no'), ('' if hasattr(g, 'user') else 'no'), (g.get('user', 'None'))))
                if username == '':
                    logger.debug(f"Anonymous user.")
                    return None
                newu = current_app.config['USERS'].get(username, None)
                if newu is None:
                    logger.debug(f"Unknown user {username}")
                    return False
                if newu.is_correct_password(password):
                    logger.debug('Approved. Start new session:'+username)
                    session.clear()
                    session['user_id'] = username
                    session.modified = True                    
                    return newu
                else:
                    return False
        else:
            # No session at all
            return True
    else:
        # check_session is False. called by login to check formed name/pass
        if username == '':
            logger.debug('Lcheck anon')
            return None
        newu = current_app.config['USERS'].get(username, None)
        if newu is None:
            logger.debug(f"L Unknown user {username}")
            return False
        if newu.is_correct_password(password):
            logger.debug('Approved {username}')
            return newu
        else:
            return False

    __import__('pdb').set_trace()

    # Anonymous users not allowed

    # go to login page when no username is given
    if username == '':
        msg = 'username is "".'
        logger.debug(msg)
        return False

    has_session = 'user_id' in session and hasattr(
        g, 'user') and g.user is not None
    if has_session and check_session:
        user = g.user
    else:
        user = current_app.config['USERS'].get(username, None)

    logger.debug('verify user/pass "%s" "%s" vs. %s' % (
        str(username), str(password), str(user)))

    if user is None:
        msg = 'Unrecognized or wrong username "%s"' % (username)
        logger.debug(msg)
        return False

    if user.is_correct_password(password):
        if SESSION and check_session:
            session.clear()
            session['user_id'] = username
            logger.debug('Approved login with new session.'+username)
            session.modified = True
        else:
            logger.debug('Approved login '+username)
        return user
    else:
        logger.warning('Incorrect password by '+username)

    msg = 'Incorrect username or password.'
    return False

######################################
####  /register GET, POST  ####
######################################


@user.route('/register', methods=('GET', 'POST'))
def register():
    ts = time.time()
    from ..route.httppool_server import resp
    return resp(300, 'FAILED', 'Not available.', ts)


@auth.error_handler
def hadle_auth_error_codes(error=401):
    """ if verify_password returns False, this gets to run.
    Note that this is decorated with flask_httpauth's `error_handler`, not flask's `errorhandler`.
    """

    if error in [401, 403]:
        # send a login page
        current_app.logger.debug("Error %d. Start login page..." % error)
        page = make_response(render_template(LOGIN_TMPLT))
        return page
    else:
        raise ValueError('Must be 401 or 403. Nor %s' % str(error))


# open text passwd
# @auth.verify_password
# def verify(username, password):
#     """This function is called to check if a username /
#     password combination is valid.
#     """
#     pc = current_app.config['PC']
#     if not (username and password):
#         return False
#     return username == pc['node']['username'] and password == pc['node']['password']

    # if 0:
    #        pass
    # elif username == pc['auth_user'] and password == pc['auth_pass']:

    # else:
    #     password = str2md5(password)
    #     try:
    #         conn = mysql.connector.connect(host = pc['mysql']['host'], port=pc['mysql']['port'], user =pc['mysql']['user'], password = pc['mysql']['password'], database = pc['mysql']['database'])
    #         if conn.is_connected():
    #             current_app.logger.info("connect to db successfully")
    #             cursor = conn.cursor()
    #             cursor.execute("SELECT * FROM userinfo WHERE userName = '" + username + "' AND password = '" + password + "';" )
    #             record = cursor.fetchall()
    #             if len(record) != 1:
    #                 current_app.logger.info("User : " + username + " auth failed")
    #                 conn.close()
    #                 return False
    #             else:
    #                 conn.close()
    #                 return True
    #         else:
    #             return False
    #     except Error as e:
    #         current_app.logger.error("Connect to database failed: " +str(e))
