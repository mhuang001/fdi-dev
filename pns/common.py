# -*- coding: utf-8 -*-
import os
import errno
from pprint import pprint, pformat
# import urllib2
import urllib.request
import urllib.error as ue
import json

from pns.logdict import logdict
import logging
import logging.config
# create logger
logging.config.dictConfig(logdict)
logger = logging.getLogger(__name__)
logger.debug('level %d' % (logger.getEffectiveLevel()))


if 0:
    print(logger.propagate)
    print(logger.disabled)
    print(logger.filters)
    print(logger.hasHandlers())
    print(logger.handlers)
    print(logger.level)

from dataset.product import Product, FineTime1, History
from dataset.metadata import Parameter, NumericParameter, MetaData
from dataset.dataset import GenericDataset, ArrayDataset, TableDataset
from dataset.deserialize import deserializeClassID
from dataset.serializable import serializeClassID

commonheaders = {
    'Accept': 'application/json',
    'Accept-Charset': 'utf-8',
    'Accept-Encoding': 'identity',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    "Content-type": 'application/json'
}


def getJsonObj(url, headers=None, usedict=False):
    """ return object from url. url can be http or file.
    translate keys and values from string to
    number if applicable. Return None if fails.
    Not using requests.get() as it cannot open file:/// w/o installing
    https://pypi.python.org/pypi/requests-file
    """
    logger.debug('url: %s' % (url))
    i = 1
    while True:
        try:
            # python 2
            # stri = urllib2.urlopen(urllib2.Request(url), timeout=15).read()
            # python3
            stri = urllib.request.urlopen(
                url, timeout=15).read().decode('utf-8')
            #logger.debug('stri ' + stri)
            break
        except Exception as e:
            logger.debug(e)
            if issubclass(e.__class__, ue.HTTPError):
                ret = e
                return None
            if i >= 1:
                logger.error("Give up " + url + " after %d tries." % i)
                return None
            else:
                i += 1
    # print(url,stri)
    # ret = json.loads(stri, parse_float=Decimal)
    # ret = json.loads(stri, cls=Decoder,
    #               object_pairs_hook=collections.OrderedDict)
    ret = deserializeClassID(stri, dglobals=globals(), usedict=usedict)
    #logger.debug(pformat(ret, depth=6)[:] + '...')
    logger.debug(str(ret)[:160] + '...')
    return ret


import requests
from http.client import HTTPConnection
# HTTPConnection.debuglevel = 1


def postJsonObj(url, obj, headers):
    """ posts object to url. Returns None if fails.
    """
    js = serializeClassID(obj)
    # %s obj %s headers %s' % (url, obj, headers))
    logger.debug(url + js[:160])

    i = 1
    while True:
        try:
            # python3
            r = requests.post(url, data=js, headers=headers, timeout=15)
            stri = r.text
            # print('ps textx %s\nstatus %d\nheader %s' % (stri, r.status_code, r.headers))
            break
        except Exception as e:
            logger.debug(e)
            if i >= 1:
                logger.error("Give up POST " + url + " after %d tries." % i)
                return None
            else:
                i += 1

    # ret = json.loads(stri, parse_float=Decimal)
    # ret = json.loads(stri, cls=Decoder)
    ret = deserializeClassID(stri, dglobals=globals())
    logger.debug(pformat(ret, depth=6)[:160] + '...')
    return ret


def putJsonObj(url, obj, headers):
    """ puts object to url. Returns None if fails.
    """
    js = serializeClassID(obj)
    # %s obj %s headers %s' % (url, obj, headers))
    logger.debug(url + js[:260]+'...')

    try:
        # python3
        r = requests.put(url, data=js, headers=headers, timeout=15)
        stri = r.text
    except Exception as e:
        logger.debug(e)
        logger.error("Give up PUT " + url)
        return None

    ret = deserializeClassID(stri, dglobals=globals())
    logger.debug(pformat(ret, depth=6)[:260] + '...')
    return ret


def postJsonObj2(url, obj, headers):
    """ post object to url. Return None if fail.
    """
    logger.debug('postJsonObj url %s obj %s headers %s' % (url, obj, headers))
    #
    data = urllib.parse.urlencode(obj).encode()
    # print('o', obj, 'd', data)
    i = 1
    while True:
        try:
             # python3
            req = urllib.request.Request(url, data=data, headers=headers)
            stri = urllib.request.urlopen(
                req, timeout=15).read().decode('utf-8')
            # ret = json.loads(stri, parse_float=Decimal)
            ret = json.loads(stri, cls=Decoder)
            break
        except Exception as e:
            print(e)
            if i >= 5:
                logger.error("Give up POST " + url + " after %d tries." % i)
                return None
            else:
                i += 1
    # print(url,stri)
    logger.debug(pformat(ret, depth=3)[:170] + '...')
    return ret


def writeJsonObj(o, fn):
    """ Write an object to file fn in json safely
    Return True if successful else False
    """
    for i in range(5):
        try:
            f = open(fn, 'w')
        except OSError:
            logger.warn('unable to open %f for writing. %d' % (fn, i))
    if i == 5:
        logger.error('unable to open %f for writing.' % (fn))
        return False
    json.dump(o, f)
    f.close()
    return True


def addslash(path):
    """ add a slash at the end of path if there is not one.
    """
    logger.debug('%s' % (path))
    if path[-1] != '/':
        path += '/'
    return path


def mkdir(f, mode=0o755):
    """ mkdir for one or multi-level paths. ignore if dir exists.
    raise exception on other errors.
    """
    logger.debug('%s %o' % (f, mode))
    path = ''
    for i in f.split('/'):
        if i == '':
            continue
        path += (i + '/')
        loger.debug(path)
        try:
            os.mkdir(path, mode)
        except OSError as e:
            if e.errno == errno.EEXIST:  # file exists error?
                pass  # logger.info('%s exists' % (path))
            else:
                raise(e)  # re-raise the exception
            os.chmod(path, mode)


if 0 and __name__ == '__main__':
    test_readtable_volume()
