import mysql.connector
from mysql.connector import Error
from pnsconfig_ssa import pnsconfig as pc

def setuplogging():
    import logging.config
    import logging
    import logdict  # import logdict
    # create logger
    logging.config.dictConfig(logdict.logdict)
    return logging


logging = setuplogging()
logger = logging.getLogger()


def get_connector():
    try:
        conn = mysql.connector.connect(host = pc['mysql']['host'], user =pc['mysql']['user'], password = pc['mysql']['password'], database = pc['mysql']['database'])
        if conn.is_connected():
            logger.info("connect to database successfully!")
            return conn
    except Error as e:
        logger.error("Connect to database failed: " +str(e))
    return None

def compare_userinfo(username = '', password = ''):
    if username != '' and password != '':
        conn = get_connector()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM userinfo WHERE userName = '" + username + "' AND password = '" + password + "';" )
        record = cursor.fetchone()
        if len(record) != 1:
            logger.info("User : " + username + " auth failed")
            conn.close()
            return False
        else:
            conn.close()
            return True


if __name__ == '__main__':
    compare_userinfo('gsegment', 'e10adc3949ba59abbe56e057f20f883e')
