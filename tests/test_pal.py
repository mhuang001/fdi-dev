
from fdi.dataset.arraydataset import ArrayDataset
import itertools
import random
import timeit
import pytest

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

from requests.auth import HTTPBasicAuth
import copy
import traceback
from pprint import pprint
import json
import shutil
import getpass
import os
import requests
import weakref
import gc
from os import path as op
import glob


import sys

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
else:
    PY3 = False

Classes.updateMapping()

if __name__ == '__main__' and __package__ == 'tests':
    # run by python -m tests.test_dataset
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
    poolpath, scheme, place, poolname = parse_poolurl(poolurl, poolhint=b2)
    assert poolpath == a2 + b1
    assert scheme == a1
    assert place == ''
    assert poolname == b2
    # implicit pool is the last segment
    poolpath, scheme, place, poolname = parse_poolurl(
        'file:///c:/tmp/mypool/v3/')
    assert poolpath == '/c:/tmp/mypool'
    assert scheme == 'file'
    assert place == ''
    assert poolname == 'v3'
    # explicit poolname. the first distinctive substring
    poolpath, scheme, place, poolname = parse_poolurl(
        'file:///c:/tmp/mypool/v3/', 'my')
    assert poolpath == '/c:/tmp'
    assert scheme == 'file'
    assert place == ''
    assert poolname == 'mypool/v3'

    # https scheme. pool parameter is given in a urn
    poolpath, scheme, place, poolname = parse_poolurl(
        'https://127.0.0.1:5000/v3/mypool/v2', 'urn:mypool/v2:foo.KProduct:43')
    assert poolpath == '/v3'
    assert scheme == 'https'
    assert place == '127.0.0.1:5000'
    assert poolname == 'mypool/v2'


def test_Urn():
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

    h = v.hash()
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
    """ direc must have a leading / if base_poolpath is defined in config """

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
        nu = [(poolname, poolurl)]
    else:
        nu = []
        for pn, pool in PoolManager.getMap().items():
            nu.append((pn, pool._poolurl))
    for pname, purl in nu:
        direc, schm, place, pn = parse_poolurl(purl, pname)
        if schm in ['file', 'server']:
            d = direc + '/' + pn
            rmlocal(d)
        elif schm == 'mem':
            pass
        elif schm in ['http', 'https']:
            pass
        else:
            assert False
        # correct way
        try:
            p = PoolManager.getPool(pname, poolurl)
            p.removeAll()
        except RuntimeError:
            pass

        PoolManager.remove(pname)
        try:
            del p
        except NameError:
            pass
        gc.collect()


def test_PoolManager():
    defaultpoolName = 'fdi_pool_' + __name__ + getpass.getuser()
    defaultpoolPath = '/tmp'
    defaultpoolUrl = 'file://' + defaultpoolPath + '/' + defaultpoolName
    cleanup(defaultpoolUrl, defaultpoolName)
    # class methods

    assert PoolManager.size() == 0
    # This creates a pool and returns it if the pool of given name does not exist
    pool = PoolManager.getPool(defaultpoolName, defaultpoolUrl)
    assert PoolManager.size() == 1
    assert defaultpoolName in PoolManager.getMap()
    # print('GlobalPoolList#: ' + str(id(pm.getMap())) + str(pm))
    PoolManager.removeAll()
    assert PoolManager.size() == 0
    assert weakref.getweakrefcount(pool) == 0
    #print(weakref.getweakrefs(pool), id(pool), 'mmmm pool')
    del pool

    # initiate
    pm = PoolManager()
    assert len(pm) == 0
    p1 = pm.getPool(defaultpoolName, defaultpoolUrl)
    #print(weakref.getweakrefs(p1), id(p1), 'mmmm p1')
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
    with pytest.raises(RuntimeError):
        ph = pm.getPool(poolurl='http://h.edu/foo')
    assert not PoolManager.isLoaded('foo')
    assert PoolManager.remove('foo') == 1


def checkdbcount(expected_cnt, poolurl, prodname, currentSN, usrpsw, *args):
    """ count files in pool and entries in class db.

    expected_cnt, currentSN: expected number of prods and currentSN in pool for products named prodname
    """
    poolpath, schm, place, poolname = parse_poolurl(poolurl)
    scheme = schm.lower()
    if scheme in ['file', 'server']:
        path = op.join(poolpath, poolname)
        assert sum(1 for x in glob.glob(
            op.join(path, prodname + '*[0-9]'))) == expected_cnt
        cp = op.join(path, 'classes.jsn')
        if op.exists(cp) or expected_cnt != 0:
            with open(cp, 'r') as fp:
                js = fp.read()
            cread = deserialize(js)
            if currentSN == -1:
                assert cread[prodname]['currentSN'] == currentSN
                # number of items is expected_cnt
            assert len(cread[prodname]['sn']) == expected_cnt
    elif scheme == 'mem':
        mpool = PoolManager.getPool(poolurl=poolurl).getPoolSpace()
        if mpool is None or len(mpool) == 0:
            # wiped
            assert expected_cnt == 0
            assert currentSN == -1
            return
        ns = [n for n in mpool if prodname in n]
        assert len(ns) == expected_cnt, len(ns)
        if currentSN == -1:
            assert mpool['classes'][prodname]['currentSN'] == currentSN
        # for this class there are  how many prods
        assert len(mpool['classes'][prodname]['sn']) == expected_cnt
    elif scheme in ['http', 'https']:
        auth = HTTPBasicAuth(*usrpsw)
        cpath = poolname + '/' + 'count/' + prodname
        api_baseurl = scheme + '://' + place + poolpath + '/'
        url = api_baseurl + cpath
        x = requests.get(url, auth=auth)
        count = int(x.json()['result'])
        assert count == expected_cnt
    else:
        assert False, 'bad pool scheme'


def test_ProductRef():
    defaultpoolName = 'fdi_pool_' + __name__ + getpass.getuser()
    defaultpoolPath = '/tmp'
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
    cleanup(p, u)

    # in memory
    # A productref created from a single product will result in a memory pool urn, and the metadata won't be loaded.
    v = ProductRef(prd)
    # only one prod in memory pool
    checkdbcount(1, 'mem:///'+DEFAULT_MEM_POOL, a4, 0, '')
    assert v.urn == 'urn:'+DEFAULT_MEM_POOL+':' + a4 + ':' + str(0)
    assert v.meta is None
    assert v.product == prd

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
    defaultpoolname = 'fdi_pool_' + __name__ + getpass.getuser()
    poolpath = '/tmp'
    defaultpoolurl = 'file://' + poolpath + '/' + defaultpoolname
    cleanup(defaultpoolurl, defaultpoolname)
    newpoolname = 'fdi_newpool_' + __name__ + getpass.getuser()
    newpoolurl = 'file://' + poolpath + '/' + newpoolname
    cleanup(newpoolurl, newpoolname)

    # Constructor
    # no default pool
    ps = ProductStorage()
    with pytest.raises(IndexError):
        p1 = ps.getPools()[0]
    # with poolurl the pool is constructed
    ps = ProductStorage(poolurl=defaultpoolurl)
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
    try:
        ps2 = ProductStorage()
    except Exception as e:
        pass
    else:
        pass  # assert False, 'exception expected'


def check_ps_func_for_pool(thepoolname, thepoolurl, *args):
    ps = ProductStorage(poolurl=thepoolurl)
    p1 = ps.getPools()[0]
    # get the pool object
    pspool = ps.getPool(p1)

    x = Product(description="This is my product example",
                instrument="MyFavourite", modelName="Flight")
    pcq = fullname(x)
    # save
    ref = ps.save(x)
    # ps has 1 prod
    assert ref.urn == 'urn:' + thepoolname + ':' + pcq + ':0'
    checkdbcount(1, thepoolurl, pcq, 0, *args)

    # save more
    # one by one
    q = 3
    x2, ref2 = [], []
    for d in range(q):  # The 1st one is a mapcontext, rest prodct
        tmp = Product(description='x' + str(d)
                      ) if d > 0 else MapContext(description='x0')
        x2.append(tmp)
        ref2.append(ps.save(tmp, tag='t' + str(d)))

    checkdbcount(q, thepoolurl, pcq, q - 1, *args)
    checkdbcount(1, thepoolurl, fullname(MapContext), 0, *args)
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
    checkdbcount(n, thepoolurl, pcq, n, *args)
    checkdbcount(1, thepoolurl, fullname(MapContext), 0, *args)

    # tags
    ts = ps.getAllTags()
    assert len(ts) == q + 1
    ts = ps.getTags(ref2[0].urn)
    assert len(ts) == 1
    assert ts[0] == 't0'
    u = ps.getUrnFromTag('all-tm')
    assert len(u) == m
    assert u[0] == ref2[q].urn

    # access resource
    checkdbcount(n, thepoolurl, pcq, n, *args)
    checkdbcount(1, thepoolurl, fullname(MapContext), 0, *args)
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
    checkdbcount(n - 1, thepoolurl, pcq, n, *args)
    checkdbcount(1, thepoolurl, fullname(MapContext), 0, *args)

    # clean up a pool
    ps.wipePool()
    checkdbcount(0, thepoolurl, pcq, -1, *args)
    assert ps.getPool(thepoolname).isEmpty()


def test_ProdStorage_func_local_mem():
    # local pool
    thepoolname = 'fdi_pool_' + __name__ + getpass.getuser()
    thepoolpath = '/tmp'
    thepoolurl = 'file://' + thepoolpath + '/' + thepoolname
    cleanup(thepoolurl, thepoolname)
    check_ps_func_for_pool(thepoolname, thepoolurl, None)

    # mempool
    thepoolname = DEFAULT_MEM_POOL
    thepoolpath = '/'
    thepoolurl = 'mem://' + thepoolpath + thepoolname

    cleanup(thepoolurl, thepoolname)
    check_ps_func_for_pool(thepoolname, thepoolurl, None)


def test_ProdStorage_func_http(setup, userpass):

    aburl, hdr = setup
    # httpclientpool
    thepoolname = 'fdi_'+__name__
    thepoolurl = aburl + '/' + thepoolname

    cleanup(thepoolurl, thepoolname)
    # First test registering with local pstor will also register on server
    pool = HttpClientPool(poolurl=thepoolurl)
    # not exist
    with pytest.raises(RuntimeError):
        assert pool.isEmpty()
    # register
    pstore = ProductStorage(pool=pool)
    assert pool.isEmpty()
    pstore.unregister(thepoolname)
    # not exist
    with pytest.raises(RuntimeError):
        assert pool.isEmpty()
    check_ps_func_for_pool(thepoolname, thepoolurl, userpass)


def test_ProdStorage_func_server(local_pools_dir):
    # httppool , the http server-side pool
    thepoolname = 'fdi_server'+__name__
    thepoolurl = 'server://' + local_pools_dir + '/' + thepoolname

    cleanup(thepoolurl, thepoolname)
    check_ps_func_for_pool(thepoolname, thepoolurl, None)


def test_LocalPool():
    thepoolname = 'fdi_localpool_' + __name__ + getpass.getuser()
    thepoolpath = '/tmp'
    thepoolurl = 'file://' + thepoolpath + '/' + thepoolname

    ps = ProductStorage(thepoolname, thepoolurl)
    p1 = ps.getPools()[0]
    # get the pool object
    pspool = ps.getPool(p1)

    x = Product(description="This is my product example",
                instrument="MyFavourite", modelName="Flight")
    pcq = fullname(x)
    # save
    ref = ps.save(x, tag='ttag')

    # read HK
    # copy default pool data in memory
    ps1 = copy.deepcopy(pspool)
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
    assert deepcmp(ps1._urns, p2._urns) is None
    assert deepcmp(ps1._tags, p2._tags) is None
    assert deepcmp(ps1._classes, p2._classes) is None


def mkStorage(thepoolname, thepoolurl):
    """ returns pool object and productStorage """

    cleanup(thepoolurl, thepoolname)
    pstore = ProductStorage(thepoolname, thepoolurl)
    thepoolpath, tsc, tpl, pn = parse_poolurl(thepoolurl, thepoolname)
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
    thepoolname = 'fdi_pool_' + __name__ + getpass.getuser()
    thepoolurl = poolpath + '/' + thepoolname
    thepool, pstore = mkStorage(thepoolname, thepoolurl)

    # make another
    newpoolname = 'fdi_newpool_' + __name__ + getpass.getuser()
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

    # query with a specific parameter in all products' metadata, which is the variable 'm' in the query expression, i.e. ``m = product.meta; ...``
    m = 2
    q = MetaQuery(TP, 'm["description"].value == "%s"' % rec1[m]['a0'])
    res = pstore.select(q)
    assert len(res) == 1, str(res)

    def chk(r, c):
        p = r.product
        assert type(p) == type(c['p'])
        assert p.description == c['a0']
        assert p.creator == c['a1']
        assert p.meta['extra'].value == c['a2']

    chk(res[0], rec1[m])

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

    # all 'time' < 5006. will cause TypeError because some Contex data do not have 'time'
    q = MetaQuery(Context, 'm["time"] < 5006')
    with pytest.raises(TypeError):
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


def test_query_local_mem():
    cleanup()
    thepoolpath = '/tmp'
    doquery('file://'+thepoolpath, 'file://'+thepoolpath)
    doquery('mem://'+thepoolpath, 'mem://'+thepoolpath)
    doquery('file://'+thepoolpath, 'mem://'+thepoolpath)
    doquery('mem://'+thepoolpath, 'file://'+thepoolpath)


def test_query_http(setup):

    aburl, hdrs = setup
    aburl = aburl.rstrip('/')
    cleanup()
    lpath = '/tmp'
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


def test_Context():
    c1 = Context(description='1')
    c2 = Context(description='2')
    assert Context.isContext(c2.__class__)
    with pytest.raises(NotImplementedError):
        assert c1.isValid()

    # dirtiness
    # assert not c1.hasDirtyReferences('ok')
    #


def test_MapContext():
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
    thepoolname = 'fdi_pool_' + __name__ + getpass.getuser()
    thepoolpath = '/tmp'
    thepoolurl = 'file://' + thepoolpath + '/'+thepoolname
    # create a prooduct
    x = Product(description='save me in store')
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

    des = checkjson(mc)
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

    # realistic scenario


def test_realistic():
    poolname = 'fdi_pool_' + __name__ + getpass.getuser()
    poolpath = '/tmp'
    poolurl = 'file://' + poolpath + '/' + poolname
    # remove existing pools in memory
    PoolManager.removeAll()
    # clean up possible garbage of previous runs. use class method to avoid reading pool hk info during ProdStorage initialization.
    pstore = ProductStorage(poolurl=poolurl)  # on disk
    pstore.wipePool()

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
    pool = 'file:///tmp/fdi_perf_' + __name__ + getpass.getuser()
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
