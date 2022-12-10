
from txrequests import Session
from twisted.internet import defer

import pprint
import logging


def setuplogging():
    import logging
    import logging.config
    from . import logdict

    # create logger
    logging.config.dictConfig(logdict.logdict)
    logging.getLogger("requests").setLevel(logging.WARN)
    logging.getLogger("urllib3").setLevel(logging.WARN)
    logging.getLogger("filelock").setLevel(logging.WARN)
    return logging


logging = setuplogging()
logger = logging.getLogger()

logger.setLevel(logging.INFO)
logger.debug('logging level %d' % (logger.getEffectiveLevel()))


def clean_board():
    importlib.invalidate_caches()
    # importlib.reload(Classes)
    from fdi.dataset.classes import Classes
    return Classes.mapping


def pc():
    """ get configuration.

    """
    from fdi.utils.getconfig import getConfig as getc
    pns = getc(force=True)
    logger.debug(json.dumps(pns))
    return pns


def new_user_read_write(pc=pc()):
    """
    GIVEN a User model
    https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
    """
    new_user = User(pc['username'], pc['password'], roles='read_write')
    headers = auth_headers(pc['username'], pc['password'])
    return new_user, headers


def server(live_or_mock=live_or_mock(), new_user_read_write=new_user_read_write()):
    """ Server data from r/w user, mock or alive.

    """
    aburl, ty = live_or_mock
    user, headers = new_user_read_write
    headers['server_type'] = ty
    yield aburl, headers


def tmp_remote_storage(server=server(), client=client(), auth=auth()):
    """ temporary servered pool with module scope """
    aburl, headers = server
    poolid = 'test_remote_pool'
    pool = PoolManager.getPool(
        poolid, aburl + '/' + poolid, auth=auth, client=client)
    pool.removeAll()
    ps = ProductStorage(pool, client=client, auth=auth)
    assert issubclass(ps.getPool(poolid).client.__class__,
                      (requests.Session, FlaskClient))
    return ps


ps = tmp_remote_storage()
aburl, header = server()
pool = ps.getPool(ps.getPools()[0])
poolurl = pool.poolurl

Number = 10
refs = []


@defer.inlineCallbacks
def main():
    with Session(maxthreads=10) as session:
        def bg_cb(sess, resp):
            # parse the json storing the result on the response object
            resp.data = resp.json()
            return resp

        d = session.get(aburl,
                        background_callback=bg_cb)
        # do some other stuff, send some more requests while this one works
        response = yield d
        print('response status {0}'.format(response.status_code))
        # data will have been attached to the response object in the background
        pprint.pprint(response.data)


if __name__ == '__main__':
    main()
