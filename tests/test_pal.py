
from fdi.dataset.arraydataset import ArrayDataset

from fdi.pal.mempool import MemPool
from fdi.pal.poolmanager import PoolManager, DEFAULT_MEM_POOL
from fdi.utils.common import trbk, fullname
from fdi.pal.context import Context, MapContext, RefContainer
from fdi.pal.productref import ProductRef
from fdi.pal.productstorage import ProductStorage
from fdi.pal.urn import Urn, parseUrn, parse_poolurl, makeUrn, UrnUtils
from fdi.pal.productpool import ProductPool
from fdi.pal.localpool import LocalPool
from fdi.pal.httpclientpool import HttpClientPool
from fdi.pal.context import Context
from fdi.pal.query import AbstractQuery, MetaQuery
from fdi.dataset.deserialize import deserialize
from fdi.dataset.product import Product
from fdi.dataset.baseproduct import BaseProduct
from fdi.dataset.eq import deepcmp
from fdi.dataset.classes import Classes
from fdi.dataset.metadata import MetaData, Parameter
from fdi.dataset.finetime import FineTime1
from fdi.dataset.testproducts import TP
from fdi.utils.checkjson import checkjson
from fdi.pns.fdi_requests import save_to_server, read_from_server, delete_from_server

# from flask import request as
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError
from urllib3.exceptions import NewConnectionError
import itertools
import random
import timeit
import pytest
import copy
import traceback
from pprint import pprint
import json
import shutil
import getpass
import os
import weakref
import gc
from os import path as op
import glob


import sys

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
else:
    PY3 = False


Test_Pool_Name = __name__.replace('.', '_')
defaultpoolPath = '/tmp/fditest'

if __name__ == '__main__' and __package__ == 'tests':
    # run by python -m tests.test_dataset

    Test_Pool_Name = 'test_pal'

    pass

else:
    # run by pytest

    # This is to be able to test w/ or w/o installing the package
    # https://docs.python-guide.org/writing/structure/
    from pycontext import fdi

    from logdict import logdict
    import logging
    import logging.config
    # create logger
    logging.config.dictConfig(logdict)
    logger = logging.getLogger()
    logger.debug('logging level %d' %
                 (logger.getEffectiveLevel()))
    logging.getLogger("filelock").setLevel(logging.WARNING)


def checkgeneral(v):
    # can always add attributes
    t = 'random'
    v.testattr = t
    assert v.testattr == t
    try:
        m = v.notexists
    except AttributeError as e:
        assert str(e).split()[-1] == "'notexists'", traceback.print_exc()
    except:
        traceback.print_exc()
        assert false


def test_UrnUtils():
    prd = Product(description='pal test')
    a1 = 'file'      # scheme
    a2 = '/e:'            # place
    b1, b2 = '/tmp/foo', 'name'
    a3 = b1 + '/' + b2               # /tmp/foo/name
    a4 = fullname(prd)           # fdi.dataset.Product
    a5 = 43
    s = a1 + '://' + a2          # file:///e:
    poolurl = s + a3                   # file:///e:/tmp/foo/name
    r = a4 + ':' + str(a5)       # fdi.dataset.Product:43
    rp = a4 + '_' + str(a5)      # fdi.dataset.Product_43
    urn = 'urn:' + b2 + ':' + r  # urn:name:fdi.dataset.Product:43
    urn1 = 'urn:' + b2 + ':' + a4+':'+str(a5-1)
    # utils
    assert parseUrn(urn) == (b2, a4, a5)
    assert UrnUtils.isUrn(urn)
    assert UrnUtils.getProductId(urn) == a5
    assert UrnUtils.getPoolId(urn) == b2
    assert UrnUtils.getLater(urn1, urn) == urn
    assert UrnUtils.getClassName(urn) == a4
    assert UrnUtils.getClass(urn).__name__ == a4.split('.')[-1]
    assert UrnUtils.extractRecordIDs([urn, urn1]) == [a5, a5-1]

    # assert UrnUtils.getPool(urn,pools)
    # assert UrnUtils.containsUrn(urn, pool)
    assert UrnUtils.checkUrn(urn)
    with pytest.raises(ValueError):
        UrnUtils.checkUrn(urn+'r')

    # poolurl
    poolpath, scheme, place, poolname, un, pw = parse_poolurl(
        poolurl, poolhint=b2)
    assert poolpath == a2 + b1
    assert scheme == a1
    assert place == ''
    assert poolname == b2
    # assert (un, pw) == ('foo', 'bar')
    # implicit pool is the last segment
    poolpath, scheme, place, poolname, un, pw = parse_poolurl(
        'file:///c:/tmp/mypool/v3/')
    assert poolpath == '/c:/tmp/mypool'
    assert scheme == 'file'
    assert place == ''
    assert poolname == 'v3'
    # explicit poolname. the first distinctive substring
    poolpath, scheme, place, poolname, un, pw = parse_poolurl(
        'file:///c:/tmp/mypool/v3/', 'my')
    assert poolpath == '/c:/tmp'
    assert scheme == 'file'
    assert place == ''
    assert poolname == 'mypool/v3'

    # https scheme. pool parameter is given in a urn
    poolpath, scheme, place, poolname, un, pw = parse_poolurl(
        'https://127.0.0.1:5000/v3/mypool/v2', 'urn:mypool/v2:foo.KProduct:43')
    assert poolpath == '/v3'
    assert scheme == 'https'
    assert place == '127.0.0.1:5000'
    assert poolname == 'mypool/v2'


def test_Urn():
    prd = BaseProduct(description='pal test')
    a1 = 'file'      # scheme
    a2 = '/e:'            # place
    b1, b2 = '/tmp/foo', 'name'
    a3 = b1 + '/' + b2               # /tmp/foo/name
    a4 = fullname(prd)           # fdi.dataset.BaseProduct
    a5 = 43
    s = a1 + '://' + a2          # file:///e:
    poolurl = s + a3                   # file:///e:/tmp/foo/name
    r = a4 + ':' + str(a5)       # fdi.dataset.BaseProduct:43
    rp = a4 + '_' + str(a5)      # fdi.dataset.BaseProduct_43
    urn = 'urn:' + b2 + ':' + r  # urn:name:fdi.dataset.BaseProduct:43
    urn1 = 'urn:' + b2 + ':' + a4+':'+str(a5-1)
    # constructor
    # urn only
    v = Urn(urn=urn)
    assert v.getPoolId() == b2
    assert v.getUrnWithoutPoolId() == r
    assert v.getIndex() == a5
    assert v.getUrn() == urn
    assert v.getScheme() is None
    assert v.getPlace() is None
    assert v.getPoolpath() is None

    # urn with poolurl
    v = Urn(urn=urn, poolurl=poolurl)
    assert v.getPoolId() == b2  #
    assert v.getUrnWithoutPoolId() == r
    assert v.getIndex() == a5
    assert v.getUrn() == urn
    assert v.getScheme() == a1
    assert v.getPlace() == ''
    assert v.getPoolpath() == a2 + b1
    # urn with components
    v = Urn(cls=prd.__class__, poolname=b2, index=a5)
    assert v.getPoolId() == b2
    assert v.getUrnWithoutPoolId() == r
    assert v.getIndex() == a5
    assert v.getUrn() == urn
    assert v.getScheme() is None
    assert v.getPlace() is None
    assert v.getPoolpath() is None
    # no urn then other args must all be given
    with pytest.raises(ValueError):
        v = Urn(cls=prd.__class__, poolname=b2)

    # no-arg constructor
    v = Urn()
    v.urn = urn
    assert v.getPoolId() == b2
    assert v.getUrnWithoutPoolId() == r
    assert v.getIndex() == a5
    assert v.getUrn() == urn
    assert v.getScheme() is None
    assert v.getPlace() is None
    assert v.getPoolpath() is None
    v = Urn()
    v.setUrn(urn=urn, poolurl=poolurl)
    assert v.getPoolId() == b2
    assert v.getUrnWithoutPoolId() == r
    assert v.getIndex() == a5
    assert v.getUrn() == urn
    assert v.getScheme() == a1
    assert v.getPlace() == ''
    assert v.getPoolpath() == a2 + b1

    # access
    assert v.getUrn() == v.urn
    assert v.getPool() == v.pool
    assert v.getTypeName() == a4
    assert v.getPlace() == v.place

    checkjson(v)


def transpath(direc, poolpath):
    """ direc must have a leading / if base_local_poolpath is defined in config """

    return poolpath+'/'+direc


def rmlocal(d):
    if op.exists(d):
        try:
            # print(os.stat(d))
            shutil.rmtree(d)
        except Exception as e:
            print(str(e) + ' ' + trbk(e))
            raise
        assert not op.exists(d)


def cleanup(poolurl=None, poolname=None):
    """ remove pool from disk and memory"""

    if poolurl or poolname:
        name_url = [(poolname, poolurl)]
    else:
        name_url = []
        for pn, pool in PoolManager.getMap().items():
            name_url.append((pn, pool._poolurl))
    for pname, purl in name_url:
        direc, schm, place, pn, un, pw = parse_poolurl(purl, pname)
        if schm in ['file', 'server']:
            d = direc + '/' + pn
            rmlocal(d)
        elif schm == 'mem':
            if PoolManager.isLoaded(DEFAULT_MEM_POOL):
                PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
        elif schm in ['http', 'https']:
            pass
        elif schm in ['csdb']:
            pass
        else:
            assert False
        # correct way
        try:
            p = PoolManager.getPool(pname, poolurl)
            p.removeAll()
        except (RuntimeError, ValueError):
            pass

        PoolManager.remove(pname)
        try:
            del p
        except NameError:
            pass
        gc.collect()


def test_PoolManager():
    defaultpoolName = Test_Pool_Name
    defaultpoolUrl = 'file://' + defaultpoolPath + '/' + defaultpoolName
    cleanup(defaultpoolUrl, defaultpoolName)
    # class methods

    assert PoolManager.size() == 0
    # This creates a pool and returns it if the pool of given name does not exist
    pool = PoolManager.getPool(defaultpoolName, defaultpoolUrl)
    assert PoolManager.size() == 1
    assert defaultpoolName in PoolManager.getMap()
    # print('GlobalPoolList#: ' + str(id(pm.getMap())) + str(pm))
    PoolManager.remove('not_exists', ignore_error=True)
    with pytest.raises(KeyError):
        PoolManager.remove('not_exists')
    PoolManager.removeAll()
    assert PoolManager.size() == 0
    assert weakref.getweakrefcount(pool) == 0
    # print(weakref.getweakrefs(pool), id(pool), 'mmmm pool')
    del pool

    # initiate
    pm = PoolManager()
    assert len(pm) == 0
    p1 = pm.getPool(defaultpoolName, defaultpoolUrl)
    # print(weakref.getweakrefs(p1), id(p1), 'mmmm p1')
    for k, v in pm.items():
        assert isinstance(v, ProductPool)
    assert defaultpoolName in pm
    PG = PoolManager._GlobalPoolList
    assert PoolManager.isLoaded(defaultpoolName) == 1
    del v
    assert PoolManager.isLoaded(defaultpoolName) == 1
    # print(weakref.getweakrefs(PG[defaultpoolName]), id(
    #    PG[defaultpoolName]), 'mmm GL')
    pr = weakref.ref(p1)
    assert pr() == p1
    assert weakref.getweakrefcount(pr()) == 2
    # print(weakref.getweakrefs(PG[defaultpoolName]),
    #      id(PG[defaultpoolName]), 'mmm+r')
    del p1
    assert pr()
    # print(weakref.getweakrefs(PG[defaultpoolName]),
    #      id(PG[defaultpoolName]), 'mmmm del p1')
    assert weakref.getweakrefcount(PG[defaultpoolName]) == 2
    gc.collect()
    # print(weakref.getweakrefs(PG[defaultpoolName]),
    #      id(PG[defaultpoolName]), 'mmmm gc')
    assert weakref.getweakrefcount(PG[defaultpoolName]) == 2  # why ?
    del pr
    # print(weakref.getweakrefs(PG[defaultpoolName]),
    #      id(PG[defaultpoolName]), 'mmmm del r')
    assert weakref.getweakrefcount(PG[defaultpoolName]) == 1
    assert pm.remove(defaultpoolName) == 0

    # http pool gets registered
    with pytest.raises(NewConnectionError):
        ph = pm.getPool(poolurl='http://h.edu/foo')
    assert not PoolManager.isLoaded('foo')
    with pytest.raises(KeyError):
        assert PoolManager.remove('foo') == 1


def checkdbcount(expected_cnt, poolurl, prodname, currentSN, usrpsw, *args, csdb=None, **kwds):
    """ init_count files in pool and entries in class db.

    expected_cnt, currentSN: expected number of prods and currentSN in pool for products named prodname
    """
    poolpath, schm, place, poolname, un, pw = parse_poolurl(poolurl)
    scheme = schm.lower()
    if scheme in ['file', 'server']:
        path = op.join(poolpath, poolname)
        assert sum(1 for x in glob.glob(
            op.join(path, prodname + '*[0-9]'))) == expected_cnt
        cp = op.join(path, 'dTypes.jsn')
        if op.exists(cp) or expected_cnt != 0:
            with open(cp, 'r') as fp:
                js = fp.read()
            cread = deserialize(js, int_key=True)
            if currentSN is None:
                assert cread[prodname]['currentSN'] == currentSN
                # number of items is expected_cnt
            assert len(cread[prodname]['sn']) == expected_cnt
    elif scheme == 'mem':
        mpool = PoolManager.getPool(poolurl=poolurl).getPoolSpace()
        if mpool is None or len(mpool) == 0:
            # wiped
            assert expected_cnt == 0
            assert currentSN is None
            return
        ns = [n for n in mpool if prodname in n]
        assert len(ns) == expected_cnt, len(ns)
        if currentSN is None:
            assert mpool['dTypes'][prodname]['currentSN'] == currentSN
        # for this class there are  how many prods
        assert len(mpool['dTypes'][prodname]['sn']) == expected_cnt
    elif scheme in ['http', 'https']:
        auth = HTTPBasicAuth(*usrpsw)
        # count
        cpath = poolname + '/' + 'count/' + prodname
        api_baseurl = scheme + '://' + place + poolpath + '/'
        url = api_baseurl + cpath
        x = requests.get(url, auth=auth)
        assert 'Recorded' in x.text
        count = int(x.json()['result'])
        assert count == expected_cnt
        # counting files. Append a '/'
        cpath = poolname + '/' + 'counted/' + prodname + '/'
        api_baseurl = scheme + '://' + place + poolpath + '/'
        url = api_baseurl + cpath
        x = requests.get(url, auth=auth)
        assert 'Counted' in x.text
        count = int(x.json()['result'])
        assert count == expected_cnt

        # count all
        cpath = poolname + '/' + 'count'
        api_baseurl = scheme + '://' + place + poolpath + '/'
        url = api_baseurl + cpath
        x = requests.get(url, auth=auth)
        assert 'Recorded' in x.text
        count = int(x.json()['result'])
        assert count >= expected_cnt

        # count all with couting
        cpath = poolname + '/' + 'counted' + '/'
        api_baseurl = scheme + '://' + place + poolpath + '/'
        url = api_baseurl + cpath
        x = requests.get(url, auth=auth)
        assert 'Counted' in x.text
        count1 = int(x.json()['result'])
        assert count1 >= expected_cnt

        assert count == count1

        # sn
        if currentSN is None:
            return
        spath = poolname + '/' + 'hk/dTypes'
        url = api_baseurl + spath
        x = requests.get(url, auth=auth)
        csn = x.json()['result'][prodname]['currentSN']
        assert csn == currentSN

    elif scheme in ['csdb']:
        test_pool = PoolManager.getPool(poolname)
        # a, b = csdb
        # assert test_pool == csdb
        pinfo = test_pool.getPoolInfo()
        count = test_pool.getCount(prodname)
        assert count == expected_cnt
        if currentSN is None:
            return
        for cl in pinfo[poolname]['_classes']:
            if cl['productTypeName'] == prodname:
                sn = cl['sn']
                assert cl['currentSn'] == currentSN
                break
    else:
        assert False, 'bad pool scheme'


def test_ProductRef():
    defaultpoolName = Test_Pool_Name
    defaultpoolUrl = 'file://' + defaultpoolPath + '/' + defaultpoolName
    cleanup(defaultpoolUrl, defaultpoolName)
    prd = Product()
    a1 = 'file'
    a2 = defaultpoolPath
    a3 = defaultpoolName
    a4 = fullname(prd)
    a5 = 0
    s = a1 + '://' + a2   # file:///tmp
    p = s + '/' + a3  # a pool URL
    r = a4 + ':' + str(a5)  # a resource
    u = 'urn:' + a3 + ':' + r    # a URN
    cleanup(p, a3)

    cleanup('mem:///' + DEFAULT_MEM_POOL, DEFAULT_MEM_POOL)

    # in memory
    # A productref created from a single product will result in a memory pool urn, and the metadata won't be loaded.
    v = ProductRef(prd)
    # only one prod in memory pool
    checkdbcount(1, 'mem:///' + DEFAULT_MEM_POOL, a4, 0, '')
    assert v.urn == 'urn:' + DEFAULT_MEM_POOL + ':' + a4 + ':' + str(0)
    assert v.meta is None
    assert v.product == prd
    # run again will get a different urn from the new instance in the pool
    r = ProductRef(prd)
    assert v != r

    # construction

    ps = ProductStorage(a3, poolurl=p)
    prd = Product()
    rfps = ps.save(prd)
    pr = ProductRef(urn=rfps.urnobj, poolname=a3)
    assert rfps == pr
    assert rfps.getMeta() == pr.getMeta()
    uobj = Urn(urn=u)
    assert pr.urnobj == uobj
    # load given metadata
    met = MetaData()
    met['foo'] = Parameter('bar')
    prm = ProductRef(urn=u, meta=met)
    assert prm.meta['foo'].value == 'bar'
    # This does not obtain metadata
    pr = ProductRef(urn=rfps.urnobj)
    assert rfps == pr
    assert rfps.getMeta() != pr.getMeta()
    assert pr.urnobj == uobj
    assert pr.getPoolname() == a3
    assert rfps.getPoolname() is not None
    # load from a storage.
    pr = ps.load(u)
    assert rfps == pr
    assert rfps.getMeta() == pr.getMeta()
    assert pr.getPoolname() == rfps.getPoolname()

    # parent
    # nominal ops
    b1 = Product(description='abc')
    b2 = MapContext(description='3c273')
    pr.addParent(b1)
    pr.addParent(b2)
    assert b1 in list(pr.parents)
    assert b2 in list(pr.parents)

    pr.removeParent(b1)
    assert b1 not in list(pr.parents)
    # access
    assert pr.urnobj.getTypeName() == a4
    assert pr.urnobj.getIndex() == a5
    # this is tested in ProdStorage
    # assert pr.product == p

    checkjson(pr)


def test_ProductStorage_init():
    defaultpoolname = Test_Pool_Name
    poolpath = '/tmp/fditest'
    defaultpoolurl = 'file://' + poolpath + '/' + defaultpoolname
    cleanup(defaultpoolurl, defaultpoolname)
    newpoolname = 'new_' + Test_Pool_Name
    newpoolurl = 'file://' + poolpath + '/' + newpoolname
    cleanup(newpoolurl, newpoolname)

    # Constructor
    # no default pool
    ps = ProductStorage()
    with pytest.raises(IndexError):
        p1 = ps.getPools()[0]
    # with poolurl the pool is constructed
    ps = ProductStorage(poolurl=defaultpoolurl)
    # There is no product
    assert ps.isEmpty()
    # get the pool object
    pspool = ps.getPool(defaultpoolname)
    assert len(pspool.getProductClasses()) == 0
    # check syntax: construct a storage with a poolobj
    pool = LocalPool(poolurl=defaultpoolurl)
    ps2 = ProductStorage(pool)
    assert ps.getPools() == ps2.getPools()
    # wrong poolname
    with pytest.raises(TypeError):
        psbad = ProductStorage(defaultpoolurl)

    # register pool
    # with a storage that already has a pool

    ps2.register(newpoolname, newpoolurl)
    assert op.exists(transpath(newpoolname, poolpath))
    assert len(ps2.getPools()) == 2
    assert ps2.getPools()[1] == newpoolname

    # multiple storages pointing to the same pool will get exception
    # with pytest.raises(TypeError):
    ps2 = ProductStorage()


def getCurrSnCount(csdb_c, prodname):
    pinfo = csdb_c if issubclass(csdb_c.__class__, dict) else \
        csdb_c.getPoolInfo()
    init_sn, init_count = 0, 0
    for pool in pinfo.values():
        poolclass = pool['_classes']
        if prodname in poolclass:
            init_sn = poolclass[prodname]['currentSn']
            # XXX was the issue xaused " - 1" fixed?
            init_count = len(poolclass[prodname]['sn'])
            break
    return init_sn, init_count, pinfo


def check_prodStorage_func_for_pool(thepoolname, thepoolurl, *args):
    ps = ProductStorage(poolurl=thepoolurl)
    p1 = ps.getPools()[0]
    # get the pool object
    pspool = ps.getPool(p1)
    x = Product(description="This is my product example",
                instrument="MyFavourite", modelName="Flight")
#    y = MapContext(description='Keep it all un context.')
    pcq = fullname(x)
    mcq = fullname(MapContext)

    is_csdb = thepoolurl.startswith('csdb://')
    if is_csdb:
        csdb = PoolManager.getPool(thepoolname)
        init_sn, init_count, pinfo = getCurrSnCount(csdb, pcq)
        init_sn_m, init_count_m, _ = getCurrSnCount(pinfo, mcq)
        logger.debug('1...', init_count, init_sn, init_count_m, init_sn_m)

    # save
    ref = ps.save(x)
    s0, s1 = tuple(ref.urn.rsplit(':', 1))
    assert s0 == 'urn:' + thepoolname + ':' + pcq
    # not saving thie one
    # ref_m = ps.save(y)
    init_count, init_count_m = 0, 0
    if is_csdb:
        __import__("pdb").set_trace()

        currentsn2, count2, pinfo2 = getCurrSnCount(csdb, pcq)
        # m is unchanged
        currentsn_m2, count_m2, pinfo_m2 = getCurrSnCount(pinfo2, mcq)
        logger.debug('2...', count2, currentsn2, count_m2, currentsn_m2)

        assert count2 == init_count + 1
        assert currentsn2 == init_sn + 1
        assert init_count_m == init_count_m
        assert currentsn_m2 == init_sn_m

        # XXX this 1 is due to a bug in csdb implementation
        init_sn += 1
        init_sn_m += 1
    else:
        init_sn = 0
        init_count = 0
        init_sn_m = 0
        init_count_m = 0

    # ps has 1 prod
    assert init_sn == int(s1)
    checkdbcount(init_count+1, thepoolurl, pcq, init_sn + 0, *args)
    # checkdbcount(init_count_m+0, thepoolurl, mcq, init_sn_m + 0, *args)

    # save more
    # one by one
    q = 3
    x2, ref2 = [], []

    for d in range(q):
        # The 1st one is a mapcontext, rest product
        tmp = Product(description='x' + str(d)
                      ) if d > 0 else MapContext(description='x0')
        x2.append(tmp)
        ref2.append(ps.save(tmp, tag='t' + str(d)))

    checkdbcount(init_count + q, thepoolurl, pcq,
                 init_sn + q - 1, *args)
    checkdbcount(init_count_m+1, thepoolurl, mcq, init_sn_m+0, *args)
    # save many in one go
    m, x3 = 2, []
    n = q + m
    for d in range(q, n):
        tmp = Product(description='x' + str(d))
        x3.append(tmp)
    ref2 += ps.save(x3, tag='all-tm')  # ps has n+1 prods
    x2 += x3  # there are n prods in x2
    # check refs
    assert len(ref2) == n
    checkdbcount(init_count+n, thepoolurl, pcq, init_sn + n - 1, *args)
    checkdbcount(init_count_m+1, thepoolurl, mcq, init_sn_m+0, *args)

    # tags
    # XXX fix getUrn() and getTag() when no arg   is given
    if not is_csdb:
        ts = ps.getAllTags()
        assert len(ts) == q + 1
        ts = ps.getTags(ref2[0].urn)
        assert len(ts) == 1
        assert ts[0] == 't0'
        u = ps.getUrnFromTag('all-tm')
        assert len(u) == m
        assert u[0] == ref2[q].urn

    # access resource
    checkdbcount(init_count+n, thepoolurl, pcq, init_sn+n-1, *args)
    checkdbcount(init_count_m+1, thepoolurl, mcq, init_sn_m+0, *args)
    # get ref from urn
    pref = ps.load(ref2[n - 2].urn)
    assert pref == ref2[n - 2]
    # actual product
    # print(pref._product)
    assert pref.product == x2[n - 2]
    # from tags

    # removal by reference urn
    # print(ref2[n - 2].urn)
    ps.remove(ref2[n - 2].urn)
    # files are less
    # DB shows less in record
    # current serial number not changed
    # number of items decreased by 1
    checkdbcount(init_count + n - 1, thepoolurl,
                 pcq, init_sn+n-1, *args)
    checkdbcount(init_count_m+1, thepoolurl, mcq, init_sn_m+0, *args)

    # check isEmpty

    # report lru_cache info
    print('***HTTPClient Pool cache*** %s ' % str(pspool.getCacheInfo()))

    # clean up a pool
    ps.wipePool()
    checkdbcount(0, thepoolurl, pcq, None, *args)
    assert ps.getPool(thepoolname).isEmpty()


def test_ProdStorage_func_local_mem():
    # local pool
    thepoolname = Test_Pool_Name
    thepoolpath = '/tmp/fditest'
    thepoolurl = 'file://' + thepoolpath + '/' + thepoolname
    cleanup(thepoolurl, thepoolname)
    check_prodStorage_func_for_pool(thepoolname, thepoolurl, None)

    # mempool
    thepoolname = DEFAULT_MEM_POOL
    thepoolpath = '/'
    thepoolurl = 'mem://' + thepoolpath + thepoolname

    cleanup(thepoolurl, thepoolname)
    check_prodStorage_func_for_pool(thepoolname, thepoolurl, None)


def test_ProdStorage_func_http(server, userpass):

    aburl, hdr = server
    # httpclientpool
    thepoolname = Test_Pool_Name
    thepoolurl = aburl + '/' + thepoolname

    cleanup(thepoolurl, thepoolname)
    # First test registering with local pstor will also register on server
    pool = HttpClientPool(poolurl=thepoolurl)

    # register
    pstore = ProductStorage(pool=pool)

    assert pool.isEmpty()
    pstore.unregister(thepoolname)
    # not exist
    with pytest.raises(RuntimeError):
        assert pool.isEmpty()
    check_prodStorage_func_for_pool(thepoolname, thepoolurl, userpass)


def test_ProdStorage_func_server():
    # httppool , the http server-side pool
    thepoolname = 'server'+Test_Pool_Name
    thepoolurl = 'server://' + '/tmp/fditest' + '/' + thepoolname

    cleanup(thepoolurl, thepoolname)
    check_prodStorage_func_for_pool(thepoolname, thepoolurl, None)


def test_ProdStorage_func_csdb(csdb):
    thepool, thepoolurl, pstore = csdb  # csdb:///csdb_test_pool
    thepoolname = thepool.poolname

    cleanup(thepoolurl, thepoolname)
    check_prodStorage_func_for_pool(thepoolname, thepoolurl, None)


def test_LocalPool():
    thepoolname = 'localpool_' + Test_Pool_Name
    thepoolpath = '/tmp/fditest'
    thepoolurl = 'file://' + thepoolpath + '/' + thepoolname

    cleanup(thepoolurl, thepoolname)
    ps = ProductStorage(thepoolname, thepoolurl)
    pname = ps.getPools()[0]
    # get the pool object
    pspool = ps.getPool(pname)

    x = Product(description="This is my product example",
                instrument="MyFavourite", modelName="Flight")
    pcq = fullname(x)
    # save
    ref = ps.save(x, tag='ttag')

    # read HK
    # copy default pool data in memory
    p1 = pspool
    # rename the pool
    cpn = thepoolname + '_copy'
    cpu = thepoolurl + '_copy'
    pcp = transpath(cpn, thepoolpath)
    if op.exists(pcp):
        shutil.rmtree(pcp)
    # make a copy of the old pool on disk
    shutil.copytree(transpath(thepoolname, thepoolpath), pcp)
    ps2 = ProductStorage(pool=cpn, poolurl=cpu)
    # two ProdStorage instances have the same DB
    p2 = ps2.getPool(ps2.getPools()[0])
    # assert deepcmp(p1._urns, p2._urns) is None
    # assert deepcmp(p1._tags, p2._tags) is None
    # assert deepcmp(p1._classes, p2._classes) is None
    assert deepcmp(p1._dTypes, p2._dTypes) is None
    assert deepcmp(p1._dTags, p2._dTags) is None

    backup_restore(ps)


def backup_restore(ps):
    p1 = ps.getPool(ps.getPools()[0])
    hk1 = p1.readHK()
    cpn = p1._poolname + '_2'
    cpu = p1._poolurl + '_2'
    pstore = ProductStorage(pool=cpn, poolurl=cpu)
    # backup
    # the new pool is made empty
    pstore.wipePool()
    # register
    pstore = ProductStorage(pool=cpn, poolurl=cpu)
    # save something to the new pool
    x = Product(description="This is my product 2")
    ref = pstore.save(x, tag='i think')
    ref2 = pstore.save(x, tag='i think')
    assert ref != ref2
    # two pools are different
    p2 = pstore.getPool(pstore.getPools()[0])
    assert deepcmp(hk1, p2.readHK()) is not None

    # make a backup tarfile
    tar = p1.backup()
    os.makedirs('/tmp/fditest', exist_ok=True)
    with open('/tmp/fditest/bk.tar', 'wb') as f:
        f.write(tar)
    with open('/tmp/fditest/bk.tar', 'rb') as f:
        tar2 = f.read()
    assert tar == tar2
    # restore
    lst = p2.restore(tar2)

    # two pools are the same
    assert deepcmp(hk1, p2.readHK()) is None


def mkStorage(thepoolname, thepoolurl, pstore=None):
    """ returns pool object and productStorage """

    cleanup(thepoolurl, thepoolname)
    if not pstore:
        pstore = ProductStorage(thepoolname, thepoolurl)
    thepoolpath, tsc, tpl, pn, un, pw = parse_poolurl(thepoolurl, thepoolname)
    if tsc in ['file', 'server']:
        assert op.exists(transpath(thepoolname, thepoolpath))
    assert len(pstore.getPools()) == 1
    assert pstore.getPools()[0] == thepoolname
    thepool = PoolManager.getMap()[thepoolname]
    assert thepool.getScheme() == tsc
    assert thepool.isEmpty()
    return thepool, pstore


def doquery(poolpath, newpoolpath):
    # creation
    a1 = MapContext
    a2 = 'p'
    a3 = 'p.description == "mc"'
    a4 = False
    q = AbstractQuery(product=a1, variable=a2, where=a3, allVersions=a4)
    assert q.getType() == a1
    assert q.getVariable() == a2
    assert q.getWhere() == a3
    assert q.retrieveAllVersions() == a4

    a1 = TP
    a2 = 'm'
    a3 = 'm["description"].value == "pr"'
    a4 = False
    q = MetaQuery(product=a1, where=a3, allVersions=a4)
    assert q.getType() == a1
    assert q.getVariable() == a2
    assert q.getWhere() == a3
    assert q.retrieveAllVersions() == a4

    # make a productStorage
    thepoolname = Test_Pool_Name
    thepoolurl = poolpath + '/' + thepoolname
    thepool, pstore = mkStorage(thepoolname, thepoolurl)

    # make another
    newpoolname = 'new_' + Test_Pool_Name
    newpoolurl = newpoolpath + '/' + newpoolname
    newpool, pstore2 = mkStorage(newpoolname, newpoolurl)

    # add some products to both storages
    n = 7
    rec1 = []
    for i in range(n):
        a0, a1, a2 = 'desc %d' % i, 'fatman %d' % (i*4), 5000+i
        if i < 3:
            x = TP(description=a0, creator=a1)
            x.meta['extra'] = Parameter(value=a2)
        elif i < 5:
            x = Context(description=a0, creator=a1)
            x.meta['extra'] = Parameter(value=a2)
        else:
            x = MapContext(description=a0, creator=a1)
            x.meta['extra'] = Parameter(value=a2)
            x.meta['time'] = Parameter(value=FineTime1(a2))
        if i < 4:
            r = pstore.save(x)
        else:
            r = pstore2.save(x)
        rec1.append(dict(p=x, r=r, a0=a0, a1=a1, a2=a2))

    # [T T T C] [C M M]
    #  0 1 2 3   4 5 6

    assert thepool.count == 4
    assert newpool.count == 3

    # query with a specific parameter in all products' metadata, which is the variable 'm' in the query expression, i.e. ``m = product.meta; ...``
    m = 2

    q = MetaQuery(TP, 'm["description"].value == "%s"' % rec1[m]['a0'])
    res = pstore.select(q)

    def chk(r, c):
        p = r.product
        assert type(p) == type(c['p'])
        assert p.description == c['a0']
        assert p.creator == c['a1']
        assert p.meta['extra'].value == c['a2']

    chk(res[0], rec1[m])

    # gracefully handle none-exisiting key
    # q = MetaQuery(TP, 'm["not_exists"].value == "%s"' % rec1[m]['a0'])
    # res = pstore.select(q)

    # query with a parent class and a specific parameter
    m = 3
    q = MetaQuery(BaseProduct, 'm["creator"].value == "%s"' % rec1[m]['a1'])
    res = pstore.select(q)
    assert len(res) == 1, str(res)
    chk(res[0], rec1[m])
    # query with a parent class and a specific parameter
    q = MetaQuery(BaseProduct, 'm["extra"].value < 5002')
    res = pstore.select(q)
    # [0,1]
    assert len(res) == 2, str(res)
    chk(res[0], rec1[0])
    chk(res[1], rec1[1])

    # simpler syntax for comparing value only but a bit slower.
    # the parameter with simpler syntax must be on the left hand side of a comparison operator.
    # '5000 < m["extra"]' does not work. But '5000 < m["extra"].value' works.
    q = MetaQuery(BaseProduct, 'm["extra"] > 5000 and m["extra"] <= 5002')
    res = pstore.select(q)
    # [1,2]
    assert len(res) == 2, str(res)
    chk(res[0], rec1[1])
    chk(res[1], rec1[2])

    qstr = 'm["extra"] > 5000 and m["extra"] <= 5002'
    pqv = pstore.select(qstr, variable='m', ptype=BaseProduct)
    pqs = pstore.select(qstr, variable='m', ptype='BaseProduct')
    assert res == pqv == pqs

    # two classes
    q = MetaQuery(BaseProduct, 'm["extra"] > 5000 and m["extra"] < 5004')
    res = pstore.select(q)
    # [1,2,3]
    assert len(res) == 3, str(res)
    chk(res[0], rec1[1])
    chk(res[1], rec1[2])
    chk(res[2], rec1[3])

    # this is not in this store
    q = MetaQuery(BaseProduct, 'm["extra"] == 5004')
    res = pstore.select(q)
    # []
    assert len(res) == 0, str(res)

    # it is in the other store
    q = MetaQuery(BaseProduct, 'm["extra"] == 5004')
    res = pstore2.select(q)
    # [4]
    assert len(res) == 1, str(res)
    chk(res[0], rec1[4])

    # all in  the other store
    q = MetaQuery(BaseProduct, '1')
    res = pstore2.select(q)
    # [4,5,6]
    assert len(res) == 3, str(res)
    chk(res[0], rec1[4])
    chk(res[1], rec1[5])
    chk(res[2], rec1[6])

    # register the new pool above to the  1st productStorage
    pstore.register(newpoolname)
    assert len(pstore.getPools()) == 2
    assert pstore.getPools()[1] == newpoolname

    # all Context, spans over two pools
    q = MetaQuery(Context, 'True')
    res = pstore.select(q)
    # [3,4,5,6]
    assert len(res) == 4, str(res)
    chk(res[0], rec1[3])
    chk(res[1], rec1[4])
    chk(res[2], rec1[5])
    chk(res[3], rec1[6])

    qstr = 'True'
    pqv = pstore.select(qstr, variable='m', ptype=Context)
    pqs = pstore.select(qstr, variable='m', ptype='Context')
    assert res == pqv == pqs

    # all 'time' < 5006. will cause KeyError because some Contex data do not have 'time'
    q = MetaQuery(Context, 'm["time"] < 5006')
    with pytest.raises(KeyError):
        res = pstore.select(q)

    q = MetaQuery(Context, 'm["this_and_the_last_errors_are_expected"] < 5006')
    with pytest.raises(KeyError):
        res = pstore.select(q)

    # all 'time' < 5006 mapcontext. all in newpool
    q = MetaQuery(MapContext, 'm["time"] < 5006')
    res = pstore.select(q)
    # [5]
    assert len(res) == 1, str(res)
    chk(res[0], rec1[5])

    # all 'extra' < 5002, all in 1st pool
    q = MetaQuery(BaseProduct, 'm["extra"] < 5002')
    res = pstore.select(q)
    # [0,1   ]
    assert len(res) == 2, str(res)
    chk(res[0], rec1[0])
    chk(res[1], rec1[1])

    # creator = 'fatman 12|16', two pools
    q = MetaQuery(BaseProduct, '"n 1" in m["creator"].value')
    res = pstore.select(q)
    # [3,4]
    assert len(res) == 2, str(res)
    chk(res[0], rec1[3])
    chk(res[1], rec1[4])

    qstr = '"n 1" in m["creator"].value'
    pq1 = thepool.select(qstr, ptype='BaseProduct')
    pq2 = newpool.qm(qstr, 'BaseProduct')
    assert res == pq1 + pq2

    if not newpoolpath.startswith('http'):
        # same as above but query is a function
        def t(m):
            import re
            return re.match('.*n.1.*', m['creator'].value)

        q = MetaQuery(BaseProduct, t)
        res = pstore.select(q)
        # [3,4]
        assert len(res) == 2, str(res)
        chk(res[0], rec1[3])
        chk(res[1], rec1[4])

    # same as above but query is on the product. this is slow.
    q = AbstractQuery(BaseProduct, 'p', '"n 1" in p.creator')
    res = pstore.select(q)
    # [3,4]
    assert len(res) == 2, str(res)
    chk(res[0], rec1[3])
    chk(res[1], rec1[4])

    qstr = '"n 1" in p.creator'
    pqv = pstore.select(qstr, variable='p', ptype=BaseProduct)
    pqs = pstore.select(qstr, variable='p', ptype='BaseProduct')
    assert res == pqv == pqs
    # pool
    pq1 = thepool.select(qstr, 'p', 'BaseProduct')
    pq2 = newpool.select(qstr, 'p', 'BaseProduct')
    assert res == pq1 + pq2

    q = '"n 1" in p.creator'
    resu = thepool.where(q)
    res = [ProductRef(u) for u in resu]
    # [3]
    assert len(res) == 1, str(res)
    chk(res[0], rec1[3])

    resu = thepool.where('p.meta["extra"] > 5000 and p.meta["extra"] < 5004')
    res = [ProductRef(u) for u in resu]
    # [1,2,3]
    assert len(res) == 3, str(res)
    chk(res[0], rec1[1])
    chk(res[1], rec1[2])
    chk(res[2], rec1[3])

    # report lru_cache info
    print('***cache*** %s ' % str(thepool.getCacheInfo()))


def test_query_local_mem():
    cleanup()
    thepoolpath = '/tmp/fditest'
    doquery('file://'+thepoolpath, 'file://'+thepoolpath)
    doquery('mem://'+thepoolpath, 'mem://'+thepoolpath)
    doquery('file://'+thepoolpath, 'mem://'+thepoolpath)
    doquery('mem://'+thepoolpath, 'file://'+thepoolpath)


def test_query_http(server):

    aburl, hdrs = server
    aburl = aburl.rstrip('/')
    cleanup()
    lpath = '/tmp'
    ### TODO: http
    doquery(aburl, aburl)
    doquery('file://'+lpath, aburl)
    doquery('mem://'+lpath, aburl)


def test_RefContainer():
    # construction
    owner = Context(description='owner')
    v = RefContainer()
    v.setOwner(owner)
    assert v._owner == owner
    # add
    image = ProductRef(Product(description="hi"))
    assert len(image.parents) == 0
    v['i'] = image
    assert v.get('i') == image
    spectrum = ProductRef(Product(description="there"))
    v.put('s', spectrum)
    assert v['s'] == spectrum
    simple = ProductRef(Product(description="everyone"))
    v.set('m', simple)
    assert v.size() == 3
    # number of parents becomes 1
    assert len(image.parents) == 1
    # te parent is..
    assert spectrum.parents[0] == owner

    # del
    del v['s']
    assert 'i' in v
    assert 'm' in v
    assert 's' not in v
    assert len(v) == 2
    # no parent any more
    assert len(spectrum.parents) == 0

    checkjson(v)


@pytest.fixture(scope='function')
def a_storage():

    thepoolname = Test_Pool_Name
    thepoolpath = '/tmp/fditest'
    thepoolurl = 'file://' + thepoolpath + '/'+thepoolname
    # remove existing pools in memory
    PoolManager().removeAll()
    # create a product store
    pstore = ProductStorage(thepoolname, thepoolurl)
    assert len(pstore.getPools()) == 1
    assert pstore.getWritablePool() == thepoolname
    assert op.isdir(transpath(thepoolname, thepoolpath))
    # clean up possible garbage of previous runs
    pstore.wipePool()
    assert op.isdir(transpath(thepoolname, thepoolpath))
    assert sum([1 for x in glob.glob(
        op.join(transpath(thepoolname, thepoolpath), '*'))]) == 0
    return pstore, thepoolname, thepoolurl


def test_Context(a_storage):
    c1 = Context(description='1')
    c2 = Context(description='2')
    assert Context.isContext(c2.__class__)
    with pytest.raises(NotImplementedError):
        assert c1.isValid()

    # dirtiness
    # assert not c1.hasDirtyReferences('ok')
    #


def test_MapContext(a_storage):
    # doc
    image = Product(description="hi")
    spectrum = Product(description="there")
    simple = Product(description="everyone")

    context = MapContext()
    context.refs.put("x", ProductRef(image))
    context.refs.put("y", ProductRef(spectrum))
    context.refs.put("z", ProductRef(simple))
    assert context.refs.size() == 3
    assert context.refs.get('x').product.description == 'hi'
    assert context.refs.get('y').product.description == 'there'
    assert context.refs.get('z').product.description == 'everyone'

    product4 = Product(description="everybody")
    context.refs.put("y", ProductRef(product4))
    product5 = Product(description="here")
    context.refs.put("a", ProductRef(product5))

    assert context.refs.get('x').product.description == 'hi'
    assert context.refs.get('y').product.description == 'everybody'
    assert context.refs.get('z').product.description == 'everyone'
    assert context.refs.get('a').product.description == 'here'

    # access
    c1 = MapContext()
    # syntax 1. refs is a property to MapContext
    c1.refs.put("x", ProductRef(image))
    c2 = MapContext()
    # syntax 2  # put == set
    c2.refs.set("x", ProductRef(image))
    # assert c1 == c2, deepcmp(c1, c2)
    c3 = MapContext()
    # syntax 3 # refs is a composite so set/get = []
    c3.refs["x"] = ProductRef(image)
    # assert c3 == c2
    assert c3.refs['x'].product.description == 'hi'
    c4 = MapContext()
    # syntax 4. refs is a member in a composite (Context) so set/get = []
    c4['refs']["x"] = ProductRef(image)
    # assert c3 == c4
    assert c4['refs']['x'].product.description == 'hi'

    # stored prod
    pstore, thepoolname, purl = a_storage
    # create a prooduct
    x = Product(description='save me in store')
    # save the product and get a reference
    prodref = pstore.save(x)
    # has the ProductStorage
    assert prodref.getPoolname() == thepoolname
    # has the pool
    assert prodref._poolname == thepoolname
    # returns the product
    assert prodref.product == x
    # create an empty mapcontext
    mc = MapContext()
    # put the ref in the context.
    # The manual has this syntax mc.refs.put('xprod', prodref)
    # but I like this for doing the same thing:
    mc['refs']['xprod'] = prodref
    # get the urn
    urn = prodref.urn
    assert issubclass(urn.__class__, str)
    # re-create a product only using the urn
    newp = ProductRef(urn).product
    # the new and the old one are equal
    assert newp == x
    # parent is set
    assert prodref.parents[0] == mc
    # re-create a product only using the urn 2
    newref = pstore.load(urn)
    newp2 = newref.product
    # the new and the old one are equal
    assert newp2 == x

    des = checkjson(mc, dbg=0)
    # print(type(des['refs']))
    # print('&&&&&& ' + des.refs.serialized(indent=4) + ' %%%%%%')
    # print(yaml.dump(des))

    newx = des['refs']['xprod'].product
    assert newx == x

    # remove refs
    del mc.refs['xprod']
    assert mc.refs.size() == 0
    assert len(prodref.parents) == 0
    # another way to remove
    des.refs.pop('xprod')
    assert des.refs.size() == 0
    assert len(prodref.parents) == 0
    # clear all
    prodref2 = pstore.save(Product())
    mc.refs['a'] = prodref
    mc.refs['b'] = prodref2
    assert mc.refs.size() == 2
    mc.refs.clear()
    assert mc.refs.size() == 0

    # URN of an object in memory
    urn = ProductRef(x).urn
    newp = PoolManager.getPool(DEFAULT_MEM_POOL).loadProduct(urn)
    # the new and the old one are equal
    assert newp == x

    c1 = MapContext(description='1')
    c2 = MapContext(description='2')
    # getAllRefs
    pstore, thepoolname, purl = a_storage
    p1 = Product('p1')
    p2 = Product('p2')
    # _urn for product is set.
    assert not hasattr(p1, '_urn')
    refp1 = pstore.save(p1)
    assert p1._urn == refp1.urnobj
    refp2 = pstore.save(p2)
    c1.refs['p1'] = refp1
    refc1 = pstore.save(c1)
    c2.refs['p2'] = refp2
    c2.refs['c1'] = refc1
    assert c2.getAllRefs() == [refp2, refc1]
    assert c2.getAllRefs(includeContexts=False) == [refp2]
    assert c2.getAllRefs(recursive=True) == [refp2, refc1, refp1]

    # realistic scenario


def test_realistic_http(server, demo_product):

    aburl, hdrs = server
    aburl = aburl.rstrip('/')
    poolname = 'demo'
    poolurl = aburl + '/' + poolname
    cleanup(poolurl, poolname)
    # remove existing pools in memory
    # clean up possible garbage of previous runs. use class method to avoid reading pool hk info during ProdStorage initialization.
    thepool, pstore = mkStorage(poolname, poolurl)
    pass


def test_realistic_csdb(csdb, urlcsdb, csdb_client, demo_product):
    urlupload, urldelete, urllist, client = csdb_client
    test_pool, poolurl, pstore = csdb  # csdb:///csdb_test_pool
    poolname = test_pool

    cleanup(poolurl, poolname)
    # remove existing pools in memory
    # clean up possible garbage of previous runs. use class method to avoid reading pool hk info during ProdStorage initialization.
    thepool, pstore = mkStorage(poolname, poolurl, pstore)

    p1 = Product(description='p1')
    p2 = Product(description='p2')
    map1 = MapContext(description='product with refs 1')
    # A ProductRef created from a lone product will use a mempool
    pref1 = ProductRef(p1)
    # use a productStorage with a pool on disk
    pref2 = pstore.save(p2)
    # how many prodrefs do we have? (do not use len() due to _STID, version)
    assert map1['refs'].size() == 0
    assert len(pref1.parents) == 0
    assert len(pref2.parents) == 0
    # add a ref to the contex. every ref has a name in mapcontext
    map1['refs']['spam'] = pref1
    assert map1['refs'].size() == 1
    assert len(pref1.parents) == 1
    assert pref1.parents[0] == map1
    # add the second one
    map1['refs']['egg'] = pref2
    # how many prodrefs do we have? (do not use len() due to _STID, version)
    assert map1['refs'].size() == 2
    assert len(pref2.parents) == 1
    assert pref2.parents[0] == map1
    assert pref1.parents[0] == map1
    # remove a ref
    del map1['refs']['spam']
    # how many prodrefs do we have? (do not use len() due to _STID, version)
    assert map1.refs.size() == 1
    assert len(pref1.parents) == 0
    # add ref2 to another map
    map2 = MapContext(description='product with refs 2')
    map2.refs['also2'] = pref2
    assert map2['refs'].size() == 1
    # two parents
    assert len(pref2.parents) == 2
    assert pref2.parents[1] == map2
    map1ref = pstore.save(map1, tag=__name__+'::realistic.map1')
    map1ref = pstore.save(map2, tag=__name__+'::realistic.map2')

    # demo prod
    dp, related = demo_product
    relatedref = pstore.save(related, tag='referenced by DemoProduct')
    dp['refs']['a related product'] = relatedref
    demoprodref = pstore.save(dp, tag='DemoProduct')


def f(n):
    return list(itertools.repeat(random.random(), n))


def rands(n):
    return [random.random() for i in range(n)]


def h(n):
    return [random.random()] * n


def speed():
    m = 10000
    print(timeit.timeit('[func(%d) for func in (rands,)]' % m,
                        globals=globals(), number=1))
    a = ArrayDataset(rands(m))
    p = Product(description="product example",
                instrument="Favourite", modelName="Flight")
    p['array'] = a
    PoolManager().removeAll()
    # create a product store
    pool = 'file:///tmp/perf_' + Test_Pool_Name
    pstore = ProductStorage(pool)
    # clean up possible garbage of previous runs
    pstore.wipePool()
    # in memory
    print(timeit.timeit('ref1 = ProductRef(p)',
                        globals=globals().update(locals()), number=1))
    pref2 = pstore.save(p)  # on disk


def running(t):
    print('running ' + str(t))
    t()


if __name__ == '__main__' and __package__ is None:
    speed()
    exit()
    running(test_ProductRef)
    running(test_ProductRef)
    running(test_MapContext)
    running(test_Urn)
    # running(test_MapRefsDataset)
    running(test_PoolManager)
    running(test_ProductStorage)
    running(test_Context)
