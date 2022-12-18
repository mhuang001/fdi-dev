# -*- coding: utf-8 -*-

# from ..route.pools import pools_api
from ...utils.common import (logging_ERROR,
                             logging_WARNING,
                             logging_INFO,
                             logging_DEBUG
                             )

from flask import (abort,
                   Blueprint,
                   flash,
                   g,
                   make_response,
                   render_template,
                   request,
                   session)
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from flask_httpauth import HTTPBasicAuth

import datetime
import time
import functools
import logging

logger = logging.getLogger(__name__)

auth = HTTPBasicAuth()

SESSION = True
""" Enable session. """


LOGIN_TMPLT = ''  # 'user/login.html'
""" Set LOGIN_TMPLT to '' to disable the login page."""


user = Blueprint('user', __name__)


class User():

    def __init__(self, username,
                 password=None,
                 hashed_password=None,
                 roles=['read_only']):

        global logger

        self.username = username
        if hashed_password:
            if password:
                if logger.isEnabledFor(logging_WARNING):
                    logger.warning(
                        'Both password and hashed_password are given for %s. Password is igored.' % username)
                password = None
        elif password:
            hashed_password = self.hash_of(password)
        else:
            raise ValueError(
                'No password and no hashed_password given for ' + username)
        self.password = password
        self.registered_on = datetime.datetime.now()

        self.hashed_password = hashed_password
        self.roles = (roles,) if issubclass(
            roles.__class__, str) else tuple(roles)
        self.authenticated = False

    @functools.lru_cache(maxsize=1024)
    def is_correct_password(self, plaintext_password):

        return check_password_hash(self.hashed_password, plaintext_password)

    @staticmethod
    @functools.lru_cache(maxsize=64)
    def hash_of(s):
        return generate_password_hash(s)

    def __repr__(self):
        return f'<User: {self.username}>'

    def getCacheInfo(self):
        info = {}
        for i in ['is_correct_password', 'hash_of']:
            info[i] = getattr(self, i).cache_info()
        return info


def get_names2roles_mapping(pc):
    # pc is pnsconfig from config filea
    mapping = {'read_write': [], 'read_only': []}
    for authtype in ('rw_user', 'ro_user'):
        unames = pc[authtype]
        unames = unames if isinstance(unames, list) else [unames]
        for n in unames:
            if authtype == 'rw_user':
                mapping['read_write'].append(n)
            else:
                mapping['read_only'].append(n)
    return mapping


NAMES2ROLES = None


def getUsers(pc):
    """ Returns the USER DB from `config.py` ro local config file.

    Allows multiple user under the save role"""

    global NAMES2ROLES
    if NAMES2ROLES is None:
        NAMES2ROLES = get_names2roles_mapping(pc)
    users = dict(((u, User(u, None, hp,
                           [r for r, n in NAMES2ROLES.items() if u in n]))
                  for u, hp in ((pc['rw_user'], pc['rw_pass']),
                                (pc['ro_user'], pc['rw_pass']))
                  ))
    return users


SES_DBG = 0
""" debug msg for session """

if SESSION:
    @user.before_app_request
    def load_logged_in_user():
        logger = current_app.logger
        user_id = session.get('user_id')
        if SES_DBG and logger.isEnabledFor(logging_DEBUG):
            headers = dict(request.headers)
            cook = dict(request.cookies)

            logger.debug('S:%x "%s", %s, %s' %
                         (id(session), str(user_id),
                          str(headers.get('Authorization', '')),
                          str(cook.get('session', '')[:6])))
        if user_id is None:
            g.user = None
        else:
            g.user = current_app.config['USERS'][user_id]


@auth.get_user_roles
def get_user_roles(user):
    if issubclass(user.__class__, User):
        return user.roles
    else:
        return None


######################################
####  /login GET, POST  ####
######################################


@ user.route('/login/', methods=['GET', 'POST'])
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
    if logger.isEnabledFor(logging_DEBUG):
        msg = 'LOGIN meth=%s req_auth_nm= "%s"' % (request.method, reqanm)
        logger.debug(msg)

    if request.method == 'POST':
        rnm = request.form.get('username', None)
        rpas = request.form.get('password', None)
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug(f'Request form {rnm}')

        if not (rpas and rnm):
            msg = 'Bad username or password posted %s' % str(rnm)
            if logger.isEnabledFor(logging_WARNING):
                logger.warning(msg)
            if reqanm and reqaps:
                if logger.isEnabledFor(logging_WARNING):
                    msg = f'Username {reqanm} and pswd in auth header used.'
                    logger.warning(msg)
                rnm, rpas = reqanm, reqaps

        vp = verify_password(rnm, rpas, check_session=False)
        if vp in (False, None):
            if logger.isEnabledFor(logging_DEBUG):
                msg = f'Verifying {rnm} with password failed.'
                logger.debug(msg)
        else:
            if SESSION:
                session.clear()
                session['user_id'] = rnm
                session.new = True
                session.modified = True
            msg = 'User %s logged-in %s.' % (rnm, vp.roles)
            if logger.isEnabledFor(logging_DEBUG):
                logger.debug(msg)
            # return redirect(url_for('pools.get_pools_url'))
            if SESSION:
                flash(msg)
            from ..route.httppool_server import resp
            return resp(200, 'OK.', msg, ts, req_auth=True)
    elif request.method == 'GET':
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug('start login')
    else:
        if logger.isEnabledFor(logging_ERROR):
            logger.error('How come the method is ' + request.method)
    if LOGIN_TMPLT:
        if SESSION:
            flash(msg)
        else:
            if logger.isEnabledFor(logging_INFO):
                logger.info(msg)
        return make_response(render_template(LOGIN_TMPLT))
    else:
        abort(401)

######################################
####  /user/logout GET, POST  ####
######################################


@ user.route('/logout/', methods=['GET', 'POST'])
@ user.route('/logout', methods=['GET', 'POST'])
# @ auth.login_required(role=['read_only', 'read_write'])
def logout():
    """ Logging in on the server.

    :return: response made from http code, poolurl, message
    """

    logger = current_app.logger
    ts = time.time()
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug('logout')
    # session.get('user_id') is the name

    if SESSION and hasattr(g, 'user') and hasattr(g.user, 'username'):
        nm, rl = g.user.username, g.user.roles
        msg = 'User %s logged-out %s.' % (nm, rl)
        res = 'OK. Bye, %s (%s).' % (nm, rl)
    else:
        msg = 'User logged-out.'
        res = 'OK. Bye.'
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug(msg)
    if SESSION:
        session.clear()
        g.user = None
        session.new = True
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
    no SESSION  not enabled           not empty  cleartext approve
   In session  w/ 'user_id'  ''|None not empty  valid      new session, r/t new u
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

    if SES_DBG and logger.isEnabledFor(logging_DEBUG):
        logger.debug('%s %s %s %s' % (username, len(password) * '*',
                     'chk' if check_session else 'nochk',
                                      'Se' if SESSION else 'noSe'))

    if check_session:
        if SESSION:
            has_session = 'user_id' in session and hasattr(
                g, 'user') and g.user is not None
            if has_session:
                user = g.user
                if SES_DBG and logger.isEnabledFor(logging_DEBUG):
                    logger.debug(f'g.usr={user.username}')
                gname = user.username
                newu = current_app.config['USERS'].get(username, None)
                # first check if the username is actually unchanged and valid
                if newu is not None and newu.is_correct_password(password):
                    if gname == username:
                        if logger.isEnabledFor(logging_DEBUG):
                            logger.debug(f"Same session.")
                        return user
                        #################
                    else:
                        if logger.isEnabledFor(logging_INFO):
                            logger.info(f"New session {username}.")
                        session.clear()
                        session['user_id'] = username
                        session.modified = True
                        return newu
                        #################
                if logger.isEnabledFor(logging_DEBUG):
                    logger.debug(
                        f"Unknown {username} or Null or anonymous user, or new user '{username}' has invalid password.")
                return False
                #################
            else:
                # SESSION enabled but has not valid user_id
                if logger.isEnabledFor(logging_DEBUG):
                    logger.debug('no session.'
                                 'has %s "user_id". %s g. g.user= %s' % (
                                     ('' if 'user_id' in session else 'no'),
                                     ('' if hasattr(g, 'user') else 'no'), (g.get('user', 'None'))))
                if username == '':
                    if logger.isEnabledFor(logging_DEBUG):
                        logger.debug(f"Anonymous user.")
                    return None
                    #################
                newu = current_app.config['USERS'].get(username, None)
                if newu is None:

                    if logger.isEnabledFor(logging_DEBUG):
                        logger.debug(f"Unknown user {username}")
                    return False
                    #################
                if newu.is_correct_password(password):
                    if logger.isEnabledFor(logging_INFO):
                        logger.info(
                            f'Approved new user {username}. Start new session')
                    session.clear()
                    session['user_id'] = username
                    session.modified = True
                    return newu
                    #################
                else:
                    if logger.isEnabledFor(logging_DEBUG):
                        logger.debug(
                            f"new user '{username}' has invalid password.")
                    __import__("pdb").set_trace()

                    return False
                    #################
        else:
            # SESSION not enabled. Use clear text passwd
            newu = current_app.config['USERS'].get(username, None)
            if newu and newu.is_correct_password(password):
                if logger.isEnabledFor(logging_INFO):
                    logger.info('Approved new user {username} w/o session')
                return newu
                #################
            else:
                if logger.isEnabledFor(logging_DEBUG):
                    logger.debug(
                        f"Null or anonymous user, or new user '{username}' has invalid password.")
                return False
                #################
    else:
        # check_session is False. called by login to check formed name/pass
        if username == '':
            if logger.isEnabledFor(logging_DEBUG):
                logger.debug('LOGIN: check anon')
            return None
            #################
        newu = current_app.config['USERS'].get(username, None)
        if newu is None:
            if logger.isEnabledFor(logging_DEBUG):
                logger.debug(f"LOGIN: Unknown user {username}")
            return False
            #################
        if newu.is_correct_password(password):
            if logger.isEnabledFor(logging_INFO):
                logger.info('LOGIN Approved {username}')
            return newu
            #################
        else:
            if logger.isEnabledFor(logging_DEBUG):
                logger.debug('LOGIN False for {username}')
            return False
            #################


######################################
####  /register GET, POST  ####
######################################


@user.route('/register', methods=('GET', 'POST'))
def register():
    ts = time.time()
    from ..route.httppool_server import resp
    return resp(300, 'FAILED', 'Not available.', ts)


if LOGIN_TMPLT:
    @auth.error_handler
    def handle_auth_error_codes(error=401):
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
#     return username == pc['username'] and password == pc['password']

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


def login_required1(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return 401, 'FAILED', "This operation needs authorization."

        return view(**kwargs)

    return wrapped_view
