# -*- coding: utf-8 -*-

from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from flask_httpauth import HTTPBasicAuth

import datetime
import operator

auth = HTTPBasicAuth()


class User():

    def __init__(self, name, passwd, role='read_only'):

        self.username = name
        self.password = passwd
        self.registered_on = datetime.datetime.now()

        self.hashed_password = generate_password_hash(passwd)
        self.role = role
        self.authenticated = False

    def is_correct_password(self, plaintext_password):

        return check_password_hash(self.hashed_password, plaintext_password)

    def __repr__(self):
        return f'<User: {self.username}>'


uspa = operator.attrgetter('username', 'password')


def getUsers(pc):
    xusers = {
        "rw": generate_password_hash(pc['node']['username']),
        "ro": generate_password_hash(pc['node']['password'])
    }
    pn = pc['node']
    users = {
        pn['username']: User(pn['username'], pn['password'], 'read_write'),
        pn['ro_username']:  User(
            pn['ro_username'], pn['ro_password'], 'read_only')
    }
    return users


@auth.get_user_roles
def get_user_roles(user):
    return user.role


@auth.verify_password
def verify_password(username, password):
    users = current_app.config['USERS']
    # return users[username]
    current_app.logger.debug('verify user/pass "%s" "%s" vs. %s' % (
        username, password, str(users)))
    if username in users and users[username].password == password:
        current_app.logger.debug('approved '+username)
        return users[username]
    else:
        return False

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
