#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fdi.utils.getconfig import make_pool, getConfig

from fdi.pal.poolmanager import PoolManager, DEFAULT_MEM_POOL
from fdi.utils.common import trbk, fullname
from fdi.pal.context import Context, MapContext, RefContainer
from fdi.pal.productref import ProductRef
from fdi.pal.productstorage import ProductStorage
from fdi.pal.urn import Urn, parseUrn, parse_poolurl, makeUrn, UrnUtils
from fdi.pal.productpool import ProductPool
from fdi.pal.localpool import LocalPool
from fdi.pal.httpclientpool import HttpClientPool
from fdi.dataset.deserialize import deserialize
from fdi.pns.jsonio import commonheaders, auth_headers

from requests.auth import HTTPBasicAuth
import requests
import argparse
import os.path as op
import sys


def getPayload(aResponse, int_key=True):
    """ deserializes, if content_type is json, data or tex of responses from either the live server or the mock one.
    """

    x = aResponse.data if issubclass(
        aResponse.__class__, fwResponse) else aResponse.text
    if aResponse.headers['Content-Type'] == 'application/json':
        return deserialize(x, int_key=int_key)
    else:
        return x


rmk = '{"result": '
mmk = ', "msg": "'


def getresultjson(url, auth):
    x = requests.get(url, auth=auth)
    if not x.text.startswith(rmk):
        print(hkdata + ' must startswith '+rmk)
        sys.exit(1)
    r = x.text[len(rmk):]
    o = r.rsplit(mmk, 1)[0]
    # print(x.status_code, x.text)
    return o


def backup(pool, auth, fp0, tar):

    if tar:
        # make a backup tarfile
        tarf = clientpool.backup()
        fp = op.join(fp0, pool._poolname + '.tgz')
        print('backup to ', fp)
        with open(p, 'wb') as f:
            f.write(tarf)
        return
    # dump the contents using api
    print('backup to ', fp0)
    fullurl = pool._poolurl
    for hkdata in ['classes', 'tags', 'urns']:
        o = getresultjson(fullurl+'/hk/'+hkdata, auth)
        fp = op.join(fp0, hkdata + '.jsn')
        with open(fp, 'w') as hf:
            hf.write(o)

    urns = list(deserialize(o).keys())
    for u in urns:
        o = getresultjson(fullurl+'/'+u.split(':', 2)[-1], auth=auth)
        fp = op.join(fp0, '_'.join(u.rsplit(':', 2)[1:]))
        with open(fp, 'w') as hf:
            hf.write(o)


def restore(pool, auth, fp0, wipe=False):

    # restore from a backup tarfile
    fp = fp0
    with open(fp, 'rb') as f:
        tar = f.read()
    print('restore %s from ' % pool._poolurl, fp)
    lst = pool.restore(tar)
    # print(lst)
    return


if __name__ == '__main__':

    # default commandline options.
    pc = getConfig()
    verbose = False
    inputdir = None
    outputdir = None
    pool = ''
    onlyframes = -1
    wipe = False

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-u", "--poolurl", type=str,
                        default='', help='Backup from or restore to the pool by the pool name (used with config.py) or the pool URL given here. Default is not any pool.')
    parser.add_argument("-i", "--inputdir", type=str,
                        default=inputdir, help="Where to find saved data, relative to source dir. if not given, is resource/testdata of the package.")
    parser.add_argument("-o", "--outputdir", type=str,
                        default=outputdir, help='Output directory or poolname.')
    parser.add_argument('-U', '--username',
                        default=pc['username'], type=str, help='user name/ID')
    parser.add_argument('-P', '--password',
                        default=pc['password'], type=str, help='password')
    parser.add_argument("-n", "--number", type=int,
                        default=onlyframes, help='Only read this number of ?.')
    parser.add_argument("-t", "--tarfile",  action='store_true',
                        default=False, help="Backup to a gzipped tarfile by the server instead of getting every file in the pool.")
    parser.add_argument("-v", "--verbose", action='store_true',
                        default=verbose, help="Print more details.")

    args = parser.parse_args()
    pc['username'] = args.username
    pc['password'] = args.password
    verbose = args.verbose
    if args.verbose:
        print(args)
    if args.inputdir and args.outputdir:
        print(
            'You cannot backup (give "outputdir") and restore (give the "inputdir" at the same time.')
        sys.exit(-1)

    l = 0

    auth = HTTPBasicAuth(args.username, args.password)
    url = args.poolurl
    pstore = make_pool(url, auth=auth)
    clientpool = pstore.getPool(pstore.getPools(auth=auth, client=client)[0])
    print(clientpool)

    if args.outputdir is not None:
        backup(clientpool, auth, args.outputdir, args.tarfile)
    elif args.inputdir is None:
        print('Backup (give "outputdir") or restore (give the "inputdir").')
        sys.exit(-2)
    else:
        restore(clientpool, auth, args.inputdir)

# x = requests.get(url, auth=auth_headers)
# print(x.status_code, x.text)
