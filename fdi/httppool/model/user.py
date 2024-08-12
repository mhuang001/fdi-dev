# -*- coding: utf-8 -*-

from ..session import SESSION
from .. import ctx
from ...pal import poolmanager as pm_mod
from ...pal.poolmanager import PM_S_from_g
from ...utils.common import (logging_ERROR,
                             logging_WARNING,
                             logging_INFO,
                             logging_DEBUG
                             )
from ...utils.getconfig import getConfig
from ...utils.colortext import (ctext,
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
from flask import (abort,
                   Blueprint,
                   current_app,
                   flash,
                   g,
                   make_response,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   session)
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from flask_httpauth import HTTPBasicAuth

import datetime
import time
from collections import defaultdict
import functools
import logging

logger = logging.getLogger(__name__)

auth = HTTPBasicAuth()

LOGIN_TMPLT = ''  # 'user/login.html'
""" Set LOGIN_TMPLT to '' to disable the login page."""

from ..session import SES_DBG

user_api = Blueprint('user', __name__)


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
    """ returns a mapping of e.g. {'read_write':[names]..} """
    # pc is pnsconfig from config files
    mapping = defaultdict(set)
    for authtype in ('rw_user', 'ro_user', 'admin'):
        unames = getConfig(authtype)
        # can be a list.
        unames = unames if isinstance(unames, list) else [unames]
        for n in unames:
            if authtype in ('rw_user', 'admin'):
                mapping[n].add('read_write')
                if authtype == 'admin':
                    for r in ('read_write', 'locker', 'all_doer'):
                        mapping[n].add(r)
            else:
                mapping[n].add('read_only')
    return mapping


NAMES2ROLES = None


def getUsers(pc):
    """ Returns the USER DB from `config.py` ro local config file.

    Allows multiple user under the same role"""

    global NAMES2ROLES
    if NAMES2ROLES is None:
        NAMES2ROLES = get_names2roles_mapping(pc)
    users = {}

    #_pc = ((pc['rw_user'], pc['rw_pass']),
    #       (pc['ro_user'], pc['ro_pass']))
    _gpc = (
        (getConfig('rw_user'), getConfig('rw_pass')),
        (getConfig('ro_user'), getConfig('ro_pass')),
        (getConfig('admin_user'), getConfig('admin_pass')),
    )
    for u, p in _gpc:
        if not issubclass(u.__class__, list):
            u = [u]
        if not issubclass(p.__class__, list):
            p = [p]
        for usernames, hashed_pwd in zip(u, p):
            if not usernames:
                continue
            roles = NAMES2ROLES[usernames]
            users[usernames] = User(usernames, None, hashed_pwd, roles)

    return users
    # users = dict(((u, User(u, None, hashed_pwd,
    #                        roles=[r for r, names in NAMES2ROLES.items() if u in names]))
    #               for u, hashed_pwd in ((pc['rw_user'], pc['rw_pass']),
    #                            (pc['ro_user'], pc['ro_pass']))
    #               ))



if SESSION:

    def set_user_session(username, pools=None, session=None, new=False, logger=logger):
        """ set session user to username if username is different from the session one.
        If the user id is not valid, `NameError` will be thrown.
        """
        if session is None:
            logger.debug('No session. Return.')
            return

        PM_S = PM_S_from_g(g)
        _c = None
        if logger.isEnabledFor(logging_DEBUG):
            _c = ctx(PM_S=PM_S, app=current_app, session=session, request=request, auth=auth)
            logger.debug(_c)

        # if not username:
        #     logger.info(f'Null or blank is not a valid session user id.')
        #     return
        
        ccu = current_app.config['USERS']
        if username not in ccu:
            logger.info(f'{username} is not a valid login id.')
            return

        if getattr(getattr(g, 'user', ''), 'username', '') == username:
            logger.info(f'{username} already the session user.')
            return
        else:
            session['user_id'] = username
            g.user = ccu[username]
            # this will trigger session cookie-remaking
            session.new = new
            current_app.config['ACCESS']['usrcnt'][username] += 1
            #load_logged_in_user(username)
        
            from ..session import set_session_pools
            set_session_pools(session, PM_S, old_ctx=_c)

            # logger.debug(f'END of set_usr_ses GPL m')

        
    # def load_logged_in_user(username):
    #     """ put session user ID to g.user.

    #     leave restoring the user's pools to session tokens.
    #     """
    #     logger = current_app.logger
        
    #     if not SESSION:
    #         if logger.isEnabledFor(logging_DEBUG):
    #             logger.warning('Called with no SESSION')
    #         return

    #     PM_S = PM_S_from_g(g)
    #     assert id(PM_S._GlobalPoolList.maps[0]) == id(pm_mod._PM_S._GlobalPoolList.maps[0])
    #     ccu = current_app.config['USERS']
    #     #if g is None or not hasattr(g, 'user') or g.user is None or g.user is None or g.user.username == username:
    #     try:
    #         if username not in ccu or g.user.username == username:
    #             logger.info(f'{username} is bad username or already the session user.')
    #             return
    #     except AttributeError:
    #         pass
    #     __import__("pdb").set_trace()

    #     g.user = ccu[username]            
    #     # if user_id:
    #     #     if 'registered_pools' not in session:
    #     #         session['registered_pools'] = {}
    #     #     pools = session.get('registered_pools', {})
    #     #     # pools = current_app.config.get('POOLS', {}).get('user_id', {})
    #     # else:
    #     #    pools = {}

    #     if SES_DBG and logger.isEnabledFor(logging_DEBUG):
    #         _d = f"Updated g.usr {_YELLOW}{g.user}"
    #         _c = (ctx(PM_S=PM_S, app=current_app, session=session, request=request, auth=auth))
    #         logger.debug(f"{_BLUE}Load_Usr, {_d} {_c}")

    @user_api.after_app_request
    def save_user(resp):

        logger = current_app.logger

        if not SESSION:
            if logger.isEnabledFor(logging_DEBUG):
                logger.debug('Called with no SESSION')
            return resp

        gu = getattr(g, 'user', None)
        if not gu or 'user_id' not in session:
            gu = None
            session.pop('user_id', '')
            if SES_DBG and logger.isEnabledFor(logging_DEBUG):
                logger.debug('Clear any user in sess and g.')
            return resp
        if gu.username == session['user_id']:
            if SES_DBG and logger.isEnabledFor(logging_DEBUG):
                logger.debug('No need to save g.user.')
            return resp

        session['user_id'] = gu.username
        session.modified = True

        PM_S = PM_S_from_g(g)
        assert id(PM_S._GlobalPoolList.maps[0]) == id(pm_mod._PM_S._GlobalPoolList.maps[0])
        
        if SES_DBG and logger.isEnabledFor(logging_DEBUG):
            user_id = session['user_id']
            _d = (f"Updated Ses Uid {_YELLOW}{user_id}")
            logger.debug('%s %s Save_Ses U "%s" snt %d, %s' %
                         (_d, _BLUE, str(user_id),
                          current_app.config['ACCESS']['usrcnt'][user_id],
                          ctx(PM_S=PM_S, app=current_app, session=session, request=request, auth=auth)))

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


@user_api.route('/login/', methods=['POST', 'GET'])
@user_api.route('/login', methods=['POST', 'GET'])
# @auth.login_required(role=['read_only', 'read_write'])
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
    msg = ''
    try:
        reqanm = request.authorization['username']
        reqaps = request.authorization['password']
    except (AttributeError, TypeError):
        reqanm = reqaps = ''
    if logger.isEnabledFor(logging_DEBUG):
        msg = 'LOGIN meth=%s req_auth_nm,ps= "%s" %s' % (
            request.method, reqanm,'*' * len(reqaps))
        logger.debug(msg)

    from ..route.httppool_server import resp

    logger.info(request.method)
    if request.method == 'GET':
        # guser = getattr(g, 'user', None)
        # if 1:    #guser is None and  (request.authorization is None or not request.authorization.get('username', '')):

        if request.authorization is None or \
           not request.authorization.get('username', ''):
            msg = 'Username and password please.'
            if SESSION:
                if LOGIN_TMPLT:
                    flash(msg)
                    return make_response(render_template(LOGIN_TMPLT))
            return resp(401, 'Authentication needed.', msg, ts, req_auth=True)
        rnm = request.authorization.get('username', '')
        rpas = request.authorization.get('passwd', '')
            
    elif request.method == 'POST':
        rnm = request.form.get('username', None)
        rpas = request.form.get('password', None)
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug(f'Request form {rnm}')
    else:
        msg = f'The method should be GET or POST, not {request.method}.'
        if logger.isEnabledFor(logging_ERROR):
            logger.error(msg)
        return resp(409, FAILED, msg, ts)

    if 1:
        if request.authorization is None:
            if getattr(g, 'user', None) is None:
                # not logged_in
                rnm = rpas = None
            else:
                # still logged in
                # use User as the password
                rnm, rpas = g.user.username, g.user
        else:
            if getattr(g, 'user', None) is None:
                # not logged_in
                rnm = request.authorization.get('username', None)
                rpas = request.authorization.get('password', None)
            else:
                # still logged in XXX take new
                rnm = request.authorization.get('username', None)
                rpas = request.authorization.get('password', None)
                if rnm is None:
                    # use User as the password
                    rnm, rpas = g.user.username, g.user

        if logger.isEnabledFor(logging_DEBUG):
            logger.debug(f'Request auth {rnm}')


    vp = verify_password(rnm, rpas, check_session=True)
    if vp not in (False, None):
        msg = f'User {vp} logged-in {vp.roles}.'
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug(msg)
        # return redirect(url_for('pools.get_pools_url'))
        if SESSION:
            if LOGIN_TMPLT:
                flash(msg)
        return resp(200, 'OK.', msg, ts)
    else:
        msg = f'Verifying {rnm} with password failed.'
        if logger.isEnabledFor(logging_INFO):
            logger.info(msg)
        if SESSION:
            if LOGIN_TMPLT:
                flash(msg)
                return make_response(render_template(LOGIN_TMPLT))
        return resp(401, 'Authentication needed.', 'Username and password please.', ts, req_auth=True)


######################################
####        logout GET, POST      ####
######################################


@user_api.route('/logout/', methods=['GET', 'POST'])
@user_api.route('/logout', methods=['GET', 'POST'])
# @auth.login_required(role=['read_only', 'read_write'])
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
        #__import__("pdb").set_trace()
        r = request.cookies
        session['user_id'] = None
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
        return redirect(url_for('pools.get_pools_url'))


@ auth.verify_password
def verify_password(username, password, check_session=True):
    """ Call back.

    ref: https://flask-httpauth.readthedocs.io/en/latest/index.html

        must return the user object if credentials are valid,
        or True if a user object is not available. In case of
        failed authentication, it should return None or False.

    `check_session`=`True` ('u/k' means unknown)

    = =========== ============= ======= ========== ========= =======================
    n state          `session`   `g`     username  password      action
    = =========== ============= ======= ========== ========= =======================
    0 no Session  no 'user_id'          not empty  valid     new session, r/t new u
    1 no Session  no 'user_id'          not empty  invalid   login, r/t `False`
    2 no Session  no 'user_id'          ''                   r/t None
    3 no Session  no 'user_id'          None, u/k            login, r/t `False`
    4 no SESSION  not enabled           not empty  cleartext approve
    5 In session  w/ 'user_id'  '' None diff knwn  valid     new ses, r/t new u
    6 In session  w/ 'user_id'  '' None empty          --    no session, r/t none
    7 In session  w/ 'user_id'  --      not empty  invalid   login, return `False`
    8 In session  w/ 'user_id'  user    diff knwn    valid   clos ol sess,new session, r/t new u
    9 In session  w/ 'user_id'  user    == user      valid   same sess, rt same user
    A In session  w/ 'user_id'  user    None ""              login, return `False`
    B                                   unknown              same
    = =========== ============= ======= ========== ========= =======================

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
    password : str or User
        from header.
    """
    logger = current_app.logger
    PM_S = PM_S_from_g(g)
    assert id(PM_S._GlobalPoolList.maps[0]) == id(pm_mod._PM_S._GlobalPoolList.maps[0])
    if 0: #password:
        __import__("pdb").set_trace()
        
    if SES_DBG and logger.isEnabledFor(logging_DEBUG):
        logger.debug('%s =U= %s %s %s %s %s' % (
            _HIWHITE, username, '' if password is None else (len(password) * '*'),
            'check' if check_session else 'nochk',
            session.get('user_id','NO SESS USR') if SESSION else 'noSess',
            getattr(g, 'user','NO g USR')))
        _c = ctx(PM_S=PM_S, app=current_app, session=session, request=request, auth=auth)
        logger.debug(_c)
            
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
                if newu is not None and ((password is user) or newu.is_correct_password(password)):
                    if gname == username:
                        # case 9
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
                        # case 5 case 8
                        # headers do not agree with cookies token. take header's
                        from ..session import close_session
                        close_session(session, PM_S, _c)
                        if logger.isEnabledFor(logging_INFO):
                            logger.info(f"New session {username}")
                        
                        set_user_session(
                            username, session=session, new=True, logger=logger)
                        return newu
                        #################
                if logger.isEnabledFor(logging_DEBUG):
                    logger.debug(
                        f"Unknown {username} or Null or anonymous user, or new user '{username}' has invalid password.")
                # case 7, A, B
                return False
                #################
            else:
                # SESSION enabled but has not valid user_id
                stat = 'session. %s "user_id". %s g. g.user= %s. ' % (
                    ('w/' if 'user_id' in session else 'w/o'),
                    ('' if hasattr(g, 'user') else 'no'),
                    (g.get('user', 'None')))
                if username in (None, ''):
                    if logger.isEnabledFor(logging_DEBUG):
                        logger.debug(f"{stat}Anonymous user.")
                    return None
                    #################
                if logger.isEnabledFor(logging_DEBUG):
                    logger.debug(ctx(PM_S=PM_S, app=current_app, session=session, request=request, auth=auth))

                newu = current_app.config['USERS'].get(username, None)
                if newu is None:
                    # case 6
                    if logger.isEnabledFor(logging_DEBUG):
                        logger.debug(f"{stat}Unknown user {username}")
                    return False
                    #################
                
                if newu.is_correct_password(password):
                    # case 5
                    if logger.isEnabledFor(logging_INFO):
                        logger.info(
                            f"{stat}Approved user {username}. Start session.")

                    set_user_session(newu.username, pools=None,
                                     session=session, new=True, logger=logger)
                    return newu
                    #################
                else:
                    # case 7
                    if logger.isEnabledFor(logging_DEBUG):
                        logger.debug(
                            f"{stat}new user '{username}' has invalid password.")
                    return False
                    #################
        else:
            # SESSION not enabled. Use clear text passwd
            newu = current_app.config['USERS'].get(username, None)
            if newu and newu.is_correct_password(password):
                # case 0
                if logger.isEnabledFor(logging_INFO):
                    logger.info(f'Approved new user {username} w/o session')
                return newu
                #################
            else:
                # case 1, 3
                if logger.isEnabledFor(logging_DEBUG):
                    logger.debug(
                        f"Null or anonymous user, or new user '{username}' has invalid password.")
                return False
                #################
    else:
        # check_session is False. called by login to check formed name/pass
        if username == '':
            # case 2
            if logger.isEnabledFor(logging_DEBUG):
                logger.debug('LOGIN: check anon')
            return None
            #################
        newu = current_app.config['USERS'].get(username, None)
        if newu is None:
            # case 3
            if logger.isEnabledFor(logging_DEBUG):
                logger.debug(f"LOGIN: Unknown user {username}")
            return False
            #################
        if newu.is_correct_password(password):
            # case 0
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


@user_api.route('/register', methods=('GET', 'POST'))
def user_register():
    ts = time.time()
    from ..route.httppool_server import resp
    return resp(300, 'FAILED', 'Not available.', ts)


#@auth.error_handler
def handle_auth_error_codes(error=401):
    """ if verify_password returns False, this gets to run.

    Note that this is decorated with flask_httpauth's `error_handler`, not flask's `errorhandler`.
    """
    #__import__("pdb").set_trace()

    if error in [401, 403]:
        # send a login page
        msg = "Error %d. Start login page..." % error if error == 401 else  "Error %d. Need extra authorization." % error
        current_app.logger.debug(msg)
        if LOGIN_TMPLT:
            page = make_response(render_template(LOGIN_TMPLT))
            return page
        else:
            return error, msg
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
