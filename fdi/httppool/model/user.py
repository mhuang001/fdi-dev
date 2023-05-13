# -*- coding: utf-8 -*-

from ...utils.common import (logging_ERROR,
                             logging_WARNING,
                             logging_INFO,
                             logging_DEBUG
                             )
from flask import (abort,
                   Blueprint,
                   current_app,
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
import copy
import functools
import logging

logger = logging.getLogger(__name__)

auth = HTTPBasicAuth()

SESSION = True
""" Enable session. """


LOGIN_TMPLT = 'user/login.html'
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
    @functools.lru_cache(maxsize=512)
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
    """ returns a mapping of {'read_write':[names]..} """
    # pc is pnsconfig from config files
    mapping = {'read_write': [], 'read_only': []}
    for authtype in ('rw_user', 'ro_user'):
        unames = pc[authtype]
        # can be a list.
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

    Allows multiple user under the same role"""

    global NAMES2ROLES
    if NAMES2ROLES is None:
        NAMES2ROLES = get_names2roles_mapping(pc)
    users = {}
    for usernames, hashed_pwd in ((pc['rw_user'], pc['rw_pass']),
                                  (pc['ro_user'], pc['ro_pass'])):
        for u in usernames:
            roles = NAMES2ROLES[u]
            users[u] = User(u, None, hashed_pwd, roles)
    return users
    # users = dict(((u, User(u, None, hashed_pwd,
    #                        roles=[r for r, names in NAMES2ROLES.items() if u in names]))
    #               for u, hashed_pwd in ((pc['rw_user'], pc['rw_pass']),
    #                            (pc['ro_user'], pc['ro_pass']))
    #               ))


SES_DBG = 1
""" debug msg for session """

if SESSION:

    def set_user_session(username, pools=None, session=None, new=False, logger=logger):
        from ..route.pools import register_pool
        from ...pal.poolmanager import PM_S

        if session is None:
            logger.debug('No session. Return.')
            return

        if not pools:
            pools = session.get('registered_pools', {})

        GPL = PM_S.getMap()
        m = 0
        if logger.isEnabledFor(logging_DEBUG):
            s = hex(id(session)) + str(session) + str(pools)
            m = f'PM_GLB_id={ hex(id(PM_S._GlobalPoolList))[-5:]} {s}'

        session['user_id'] = username
        for pn, pu in pools.items():
            if not pn in GPL:
                code, po, msg = register_pool(
                    pn, current_app.config['USERS'][username], poolurl=pu)
                assert po is GPL[pn]
            assert pn in GPL
            assert GPL[pn]._poolurl == pu

        if not username:
            g.user = None
        else:
            g.user = current_app.config['USERS'][username]

        session.new = new
        current_app.config['ACCESS']['usrcnt'][username] += 1
        session.modified = True

        logger.debug(
            f'LDUSR tcf2 {PM_S.isLoaded("test_csdb_fdi2")} GPL {GPL.data} m={m}')

    @user.before_app_request
    def load_logged_in_user():
        logger = current_app.logger

        if not SESSION:
            if logger.isEnabledFor(logging_DEBUG):
                logger.warning('Called with no SESSION')
            return

        user_id = session.get('user_id', '')
        if user_id:
            if 'registered_pools' not in session:
                session['registered_pools'] = {}
            pools = session.get('registered_pools', {})
            # pools = current_app.config.get('POOLS', {}).get('user_id', {})
        else:
            pools = {}

        if SES_DBG and logger.isEnabledFor(logging_DEBUG):
            from ...pal.poolmanager import PM_S
            headers = dict(request.headers)
            cook = dict(request.cookies)
            if logger.isEnabledFor(logging_DEBUG):
                gl = 'PM_GLB_id=%s' % hex(id(PM_S._GlobalPoolList))[-4:]
                # sid = hex(id(current_app.config['POOLS']))[-4:],
                logger.debug('Ses"%s">%d %s, %s, %s' %
                             (str(user_id),
                              current_app.config['ACCESS']['usrcnt'][user_id],
                              str(headers.get('Authorization', '')),
                              str(cook.get('session', '')[-6:]),
                              str(pools)[:]) + gl)

    @user.after_app_request
    def save_registered_pools(resp):
        logger = current_app.logger

        if not SESSION:
            if logger.isEnabledFor(logging_DEBUG):
                logger.debug('Called with no SESSION')
            return resp

        user_id = session.get('user_id', None)

        if not user_id:
            return resp

        from ...pal.poolmanager import PM_S
        GPL = PM_S.getMap()
        # session['registered_pools']
        if SES_DBG and logger.isEnabledFor(logging_DEBUG):
            hdr = ''  # dict(resp.headers)
            gl = 'PM_GLB_id=%s' % hex(id(GPL))[-4:]
            logger.debug(' Ses"%s"<%d %s, %s, %s' %
                         (str(user_id),
                          current_app.config['ACCESS']['usrcnt'][user_id],
                          str(hdr),
                          str(session.get('registered_pools', {})), gl))
            # print(f"$$$ {session}")
        return resp


@auth.get_user_roles
def get_user_roles(user):
    if issubclass(user.__class__, User):
        return user.roles
    else:
        return None


######################################
####  /login GET, POST            ####
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
    serialize_out = True
    ts = time.time()
    FAILED = '"FAILED"' if serialize_out else 'FAILED'
    acu = auth.current_user()

    try:
        reqanm = request.authorization['username']
        reqaps = request.authorization['password']
    except (AttributeError, TypeError):
        reqanm = reqaps = ''
    if logger.isEnabledFor(logging_DEBUG):
        msg = 'LOGIN meth=%s req_auth_nm= "%s"' % (
            request.method, '*' * len(reqanm))
        logger.debug(msg)

    from ..route.httppool_server import resp

    if request.method == 'POST':
        rnm = request.form.get('username', None)
        rpas = request.form.get('password', None)
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug(f'Request form {rnm}')

        # if not (rpas and rnm):
        #     msg = 'Bad username or password posted %s' % str(rnm)
        #     if logger.isEnabledFor(logging_WARNING):
        #         logger.warning(msg)
        #     if reqanm and reqaps:
        #         if logger.isEnabledFor(logging_WARNING):
        #             msg = f'Username {reqanm} and pswd in auth header used.'
        #             logger.warning(msg)
        #         rnm, rpas = reqanm, reqaps
        # vp = verify_password(rnm, rpas, check_session=False)

        vp = verify_password(rnm, rpas, check_session=True)
        if vp in (False, None):
            if logger.isEnabledFor(logging_DEBUG):
                msg = f'Verifying {rnm} with password failed.'
                logger.debug(msg)
            return resp(401, FAILED, msg, ts, req_auth=True)
        else:
            msg = 'User %s logged-in %s.' % (vp, vp.roles)
            if logger.isEnabledFor(logging_DEBUG):
                logger.debug(msg)
            # return redirect(url_for('pools.get_pools_url'))
            if SESSION:
                if LOGIN_TMPLT:
                    flash(msg)
            return resp(200, 'OK.', msg, ts, req_auth=True)
    elif request.method == 'GET':
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug('start login')
    else:
        msg = f'The method should be GET or POST, not {request.method}.'
        if logger.isEnabledFor(logging_ERROR):
            logger.error(msg)
        raise resp(409, FAILED, msg, ts)
    if SESSION:
        if LOGIN_TMPLT:
            flash(msg)
            return make_response(render_template(LOGIN_TMPLT))
    else:
        if logger.isEnabledFor(logging_INFO):
            logger.info(msg)
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
        # session.clear()
        g.user = None
        g.pools = None
        session.modified = True

    from ..route.httppool_server import resp

    # return resp(200, res, msg, ts)
    msg = 'Welcome to Poolserver.'
    if LOGIN_TMPLT:
        if SESSION:
            flash(msg)
        else:
            if logger.isEnabledFor(logging_INFO):
                logger.info(msg)
        return make_response(render_template(LOGIN_TMPLT))
    else:
        abort(401, msg)


@ auth.verify_password
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
    In session  w/ 'user_id'  ''|None different   valid      new session, r/t new u
    ..                                not same
    In session  w/ 'user_id'          not empty  invalid   login, return `False`
    In session  w/ 'user_id'  user    == user      valid   login, return same user
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

    Parameters
    ----------
    username : str
    password : str
        from header.
    """
    logger = current_app.logger
    from ...pal.poolmanager import PM_S

    if SES_DBG and logger.isEnabledFor(logging_DEBUG):
        logger.debug('%s %s %s %s' % (username, '' if password is None else (len(password) * '*'),
                     'check' if check_session else 'nochk',
                                      'Sess' if SESSION else 'noSess'))
    if check_session:
        __import__("pdb").set_trace()

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
                        # username is from header AUTHR..
                        if logger.isEnabledFor(logging_DEBUG):
                            pools = dict((p, o._poolurl)
                                         for p, o in PM_S.getMap().items())
                            logger.debug(f"Same session {pools}.")
                        set_user_session(
                            username, session=session, logger=logger)
                        return user
                        #################
                    else:
                        # headers do not agree with cookies token
                        if logger.isEnabledFor(logging_INFO):
                            logger.info(f"New session {username}")
                        set_user_session(
                            username, session=session, logger=logger)
                        return newu
                        #################
                if logger.isEnabledFor(logging_DEBUG):
                    logger.debug(
                        f"Unknown {username} or Null or anonymous user, or new user '{username}' has invalid password.")
                return False
                #################
            else:
                # SESSION enabled but has not valid user_id
                stat = 'session. %s "user_id". %s g. g.user= %s. ' % (
                    ('w/' if 'user_id' in session else 'w/o'),
                    ('' if hasattr(g, 'user') else 'no'),
                    (g.get('user', 'None')))
                if username == '':
                    if logger.isEnabledFor(logging_DEBUG):
                        logger.debug(f"{stat}Anonymous user.")
                    return None
                    #################
                newu = current_app.config['USERS'].get(username, None)
                if newu is None:
                    if logger.isEnabledFor(logging_DEBUG):
                        logger.debug(f"{stat}Unknown user {username}")
                    return False
                    #################
                if newu.is_correct_password(password):
                    if logger.isEnabledFor(logging_INFO):
                        logger.info(
                            f"{stat}Approved user {username}. Start session.")
                    set_user_session(newu.username, pools=None,
                                     session=session, new=False, logger=logger)
                    return newu
                    #################
                else:
                    if logger.isEnabledFor(logging_DEBUG):
                        logger.debug(
                            f"{stat}new user '{username}' has invalid password.")
                    return False
                    #################
        else:
            # SESSION not enabled. Use clear text passwd
            newu = current_app.config['USERS'].get(username, None)
            if newu and newu.is_correct_password(password):
                if logger.isEnabledFor(logging_INFO):
                    logger.info(f'Approved new user {username} w/o session')
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
####  /register GET, POST         ####
######################################


@user.route('/register', methods=('GET', 'POST'))
def user_register():
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
