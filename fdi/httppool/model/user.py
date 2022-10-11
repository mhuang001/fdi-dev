# -*- coding: utf-8 -*-

#from ..route.pools import pools_api

from flask import (
    Blueprint, flash, g, make_response, redirect, render_template, request, session, url_for
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, Response
from flask_httpauth import HTTPBasicAuth

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
        current_app.logger.debug('session %x user_id = %s' %
                                 (id(session), str(user_id)))

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
    except (AttributeError, TypeError):
        reqanm = ''
    msg = 'LOGIN meth=%s req_auth_nm= %s' % (request.method, reqanm)
    logger.debug(msg)

    if request.method == 'POST':
        rnm = request.form['username']
        rpas = request.form['password']
        logger.debug(f'Request form {rnm}')

        if 0 and reqanm and rnm != reqanm:
            msg = f'Username {rnm} POSTed does not match {reqanm} in auth header. Logging out first...'
            logger.warning(msg)
            return logout()

        vp = verify_password(rnm, rpas, check_session=False)
        if vp in (False, None):
            msg = f'Verifying {rnm} with password failed.'
            logger.debug(msg)
        else:
            if SESSION:
                session.clear()
                session['user_id'] = rnm
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

    from ..route.httppool_server import resp

    return resp(200, res, msg, ts)


@auth.verify_password
def verify_password(username, password, check_session=True):
    """ Call back.

    ref: https://flask-httpauth.readthedocs.io/en/latest/index.html

        must return the user object if credentials are valid,
        or True if a user object is not available. In case of 
        failed authentication, it should return None or False. 

    `check_session`=`True`

    =========== ============= ======= ========== ========= =============
    state          `session`   `g`     username  password      action
    =========== ============= ======= ========== ========= =============
    no Session  no 'user_id'          not empty  valid     new  session
    no Session  no 'user_id'          not empty  invalid   login
    no Session  no 'user_id'          ''                   return None
    no Session  no 'user_id'          None                 login
    In session  w/ 'user_id'  ''|None not empty  valid     new session
    In session  w/ 'user_id'  user    diff n/em  valid     new session
    In session  w/ 'user_id'  ''|None ''                   return None
    In session  w/ 'user_id'  user               invalid   keep session
    In session  w/ 'user_id'  user    None *               keep session
    In session  w/ 'user_id'  user    same user  valid     keep session
    =========== ============= ======= ========== ========= =============

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
    """

    logger = current_app.logger

    if check_session:
        if SESSION:
            has_session = 'user_id' in session and hasattr(
                g, 'user') and g.user is not None
            if has_session:
                user = g.user
                gname = user.username
                if gname != username:
                    newu = current_app.config['USERS'].get(username, None)
                    if newu is None:
                        logger.debug(
                            f"Unknown user {username}. Keep existing session {gname}")
                        return user
                    else:
                        logger.debug(f"New session {username}.")
                        session.clear()
                        session['user_id'] = username
                        return newu
                else:
                    logger.debug(f"Keep existing session {gname}")
                    return user
            else:
                # has no session
                if username == '':
                    logger.debug(f"Anonymous user.")
                    return None
                newu = current_app.config['USERS'].get(username, None)
                if newu is None:
                    logger.debug(f"Unknown user {username}")
                    return False
                else:
                    logger.debug('Approved. Start new session:'+username)
                    session.clear()
                    session['user_id'] = username
                    return newu
        else:
            pass
    else:
        # check_session is False. called by login to check formed name/pass
        if username == '':
            logger.debug('L anon')
            return None
        newu = current_app.config['USERS'].get(username, None)
        if newu is None:
            logger.debug(f"L Unknown user {username}")
            return False
        else:
            logger.debug('Approved {username}')
            return newu

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
