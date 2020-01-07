import traceback
from pprint import pprint
import json
from pathlib import Path
from collections import ChainMap
import builtins
import os

import sys
#print([(k, v) for k, v in globals().items() if '__' in k])

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
else:
    PY3 = False

if __name__ == '__main__' and __package__ is None:
    pass
else:
    # This is to be able to test w/ or w/o installing the package
    # https://docs.python-guide.org/writing/structure/
    from .pycontext import spdc

    from .logdict import doLogging, logdict
    if doLogging:
        import logging
        import logging.config
        # create logger
        logging.config.dictConfig(logdict)
        logger = logging.getLogger()
        logger.debug('%s logging level %d' %
                     (__name__, logger.getEffectiveLevel()))
        logging.getLogger("filelock").setLevel(logging.WARNING)

from spdc.dataset.eq import deepcmp
from spdc.dataset.product import Product
from spdc.dataset.deserialize import deserializeClassID

from spdc.pal.urn import Urn, parseUrn, makeUrn
from spdc.pal.productstorage import ProductStorage
from spdc.pal.productref import ProductRef
from spdc.pal.context import Context, MapContext, MapRefsDataset
from spdc.pal.common import getProductObject
from spdc.pal.poolmanager import PoolManager
#from products.QSRCLIST_VT import QSRCLIST_VT


def checkjson(obj):
    """ seriaizes the given object and deserialize. check equality.
    """

    # dbg = True if issubclass(obj.__class__, Product) else False
    dbg = False

    if hasattr(obj, 'serialized'):
        js = obj.serialized()
    else:
        js = json.dumps(obj)

    if dbg:
        print('*************** checkjsom ' + obj.__class__.__name__ +
              ' serialized: ************\n')
        print(js)
        print('*************************')
    des = deserializeClassID(js, debug=dbg)
    if dbg:
        if hasattr(des, 'meta'):
            print('moo ' + str((des.meta.listeners)))
        print('*********** checkjson deserialized ' + str(des.__class__) +
              '***********\n')
        pprint(des)

        # js2 = json.dumps(des, cls=SerializableEncoder)
        # pprint('******** des     serialized: **********')
        # pprint(js)

        r = deepcmp(obj, des)
        print('*************** deepcmp ***************')
        print('identical' if r is None else r)
        print(' DIR \n' + str(dir(obj)) + '\n' + str(dir(des)))
    if 0 and issubclass(obj.__class__, Product):
        obj.meta.listeners = []
        des.meta.listeners = []
    assert obj == des, deepcmp(obj, des) + '\nOBJ ' + \
        obj.toString() + '\nDES ' + des.toString()
    return des


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


def test_Urn():
    prd = Product(description='pal test')
    a1 = 'file'      # scheme
    c1, c2 = 's:', '/d'
    a2 = c1            # place
    b1, b2, b3 = '/b', '/tmp/foo', '/c'
    a3 = b1 + b2 + b3
    a4 = prd.__class__.__qualname__
    a5 = 43
    s = a1 + '://' + a2   # file://s:
    p = s + a3
    r = a4 + ':' + str(a5)
    rp = a4 + '_' + str(a5)
    u = 'urn:' + p + ':' + r

    # utils
    assert parseUrn(u) == (p, a4, str(a5), a1, a2, a2 + a3)
    poolname, resourceclass, serialnumstr, scheme, place, poolpath = parseUrn(
        'urn:file://c:/tmp/mypool:proj1.product:322')
    assert poolname == 'file://c:/tmp/mypool'
    assert resourceclass == 'proj1.product'
    assert place == 'c:'
    assert poolpath == 'c:/tmp/mypool'
    poolname, resourceclass, serialnumstr, scheme, place, poolpath = parseUrn(
        'urn:https://127.0.0.1:5000/tmp/mypool:proj1.product:322')
    assert poolname == 'https://127.0.0.1:5000/tmp/mypool'
    assert resourceclass == 'proj1.product'
    assert place == '127.0.0.1:5000'
    assert poolpath == '/tmp/mypool'

    # constructor
    # urn only
    v = Urn(urn=u)
    assert v.getScheme() == a1
    assert v.getPlace() == a2
    assert v.getPoolId() == p  #
    assert v.getUrnWithoutPoolId() == r
    assert v.getFullPath(u) == a2 + a3 + '/' + rp  # s:/b/tmp/foo/c
    assert v.getIndex() == a5
    assert v.getUrn() == u
    # urn in memory
    v = Urn.getInMemUrnObj(prd)
    assert v.urn == 'urn:mem:///' + \
        str(os.getpid()) + ':' + a4 + ':' + str(id(prd))
    # urn with pool
    v = Urn(cls=prd.__class__, pool=p, index=a5)
    assert v.getScheme() == a1
    assert v.getFullPath(u) == a2 + a3 + '/' + rp  # s:/b/tmp/foo/c
    # urn with storage that does not match urn
    try:
        v = Urn(urn=u, cls=prd.__class__, pool=p, index=a5)
    except Exception as e:
        assert issubclass(e.__class__, ValueError)
    # no-arg constructor
    v = Urn()
    v.urn = u
    assert v.getScheme() == a1
    assert v.getFullPath(u) == a2 + a3 + '/' + rp  # s:/b/tmp/foo/c

    # access
    assert v.getUrn() == v.urn
    assert v.getPool() == v.pool
    assert v.getTypeName() == a4
    assert v.getPlace() == v.place

    checkjson(v)


def test_MapRefsDataset():
    a1 = 'foo'
    a2 = 'bar'
    d = MapRefsDataset()
    d.put(a1, a2)
    assert d[a1] == a2


def test_PoolManager():
    defaultpoolpath = '/tmp/pool'
    defaultpool = 'file://' + defaultpoolpath
    pm = PoolManager()
    assert pm.size() == 0
    pool = pm.getPool(defaultpool)
    assert pm.size() == 1
    print('GlobalPoolList: ' + str(id(pm.getMap())) + str(pm))
    pm.removeAll()
    assert pm.size() == 0


def test_ProductRef():
    defaultpoolpath = '/tmp/pool'
    defaultpool = 'file://' + defaultpoolpath
    prd = Product()
    a1 = 'file'
    a2 = ''
    a3 = defaultpoolpath
    a4 = prd.__class__.__qualname__
    a5 = 0
    s = a1 + '://' + a2   # file://s:
    p = s + a3  # a pool URN
    r = a4 + ':' + str(a5)  # a resource
    u = 'urn:' + p + ':' + r    # a URN
    pdp = Path(defaultpoolpath)
    os.system('rm -rf ' + defaultpoolpath)
    assert not pdp.exists()

    # in memory
    mr = ProductRef(prd)
    assert mr.urnobj == Urn.getInMemUrnObj(prd)
    assert mr.meta == prd.meta
    uobj = Urn(urn=u)
    # remove existing pools in memory
    PoolManager().removeAll()
    # construction
    ps = ProductStorage(p)
    rfps = ps.save(prd)
    pr = ProductRef(urn=rfps.urnobj, pool=ps.getPool(p))
    assert rfps == pr
    assert rfps.getMeta() == pr.getMeta()
    assert pr.urnobj == uobj
    # This does not obtain metadata
    pr = ProductRef(urn=rfps.urnobj)
    assert rfps == pr
    assert rfps.getMeta() != pr.getMeta()
    assert pr.urnobj == uobj
    assert pr.getStorage() is None
    assert rfps.getStorage() is not None
    # load from a storage.
    pr = ps.load(u)
    assert rfps == pr
    assert rfps.getMeta() == pr.getMeta()
    assert pr.getStorage() == rfps.getStorage()

    # parent
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


def test_ProductStorage():
    defaultpoolpath = '/tmp/pool'
    defaultpool = 'file://' + defaultpoolpath
    pdp = Path(defaultpoolpath)
    os.system('rm -rf ' + defaultpoolpath)
    assert not pdp.exists()
    # remove existing pools in memory
    PoolManager().removeAll()

    x = Product(description="This is my product example",
                instrument="MyFavourite", modelName="Flight")
    pcq = x.__class__.__qualname__
    # constructor
    # default pool
    ps = ProductStorage()
    p1 = ps.getPools()[0]
    assert p1 == defaultpool
    pspool = ps.getPool(p1)
    assert len(pspool.getProductClasses()) == 0
    # constrct with a pool
    ps2 = ProductStorage(defaultpool)
    assert ps.getPools() == ps2.getPools()

    # register pool
    # with a storage that already has a pool
    newpoolpath = '/tmp/newpool'
    newpoolname = 'file://' + newpoolpath
    npp = Path(newpoolpath)
    os.system('rm -rf ' + newpoolpath)
    assert not npp.exists()

    ps2.register(newpoolname)
    assert npp.exists()
    assert len(ps2.getPools()) == 2
    assert ps2.getPools()[1] == newpoolname

    # save
    ref = ps.save(x)
    assert ref.urn == 'urn:' + defaultpool + ':' + pcq + ':0'
    # count files in pool and entries in class db
    assert sum(1 for x in pdp.glob(pcq + '*[0-9]')) == 1
    cread = json.load(pdp.joinpath('classes.jsn').open())
    assert cread[pcq]['currentSN'] + 1 == 1

    # save more
    # one by one
    q = 3
    x2, ref2 = [], []
    for d in range(q):
        tmp = Product(description='x' + str(d))
        x2.append(tmp)
        ref2.append(ps.save(tmp, tag='t' + str(d)))
        # count files in pool
    assert sum(1 for x in pdp.glob(pcq + '*[0-9]')) == 1 + q
    # number of prod in the DB
    cread = json.load(pdp.joinpath('classes.jsn').open())
    assert cread[pcq]['currentSN'] + 1 == 1 + q
    # save many in one go
    m, x3 = 2, []
    n = q + m
    for d in range(q, n):
        tmp = Product(description='x' + str(d))
        x3.append(tmp)
    ref2 += ps.save(x3, tag='all-tm')
    x2 += x3
    # check refs
    assert len(ref2) == n
    # count files in pool
    assert sum(1 for x in pdp.glob(pcq + '*[0-9]')) == 1 + n
    # number of prod in the DB
    cread = json.load(pdp.joinpath('classes.jsn').open())
    assert cread[pcq]['currentSN'] + 1 == 1 + n

    # tags
    ts = ps.getAllTags()
    assert len(ts) == q + 1
    ts = ps.getTags(ref2[0].urn)
    assert len(ts) == 1
    assert ts[0] == 't0'
    u = ps.getUrnFromTag('all-tm')
    assert len(u) == m
    assert u[0] == ref2[q].urn

    # multiple storages pointing to the same pool will get exception
    try:
        ps2 = ProductStorage()
    except Exception as e:
        pass
    else:
        assert 1  # False

    # read HK
    # make a copy of the pool files
    cp = defaultpoolpath + '_copy'
    os.system('rm -rf ' + cp + '; cp -rf ' + defaultpoolpath + ' ' + cp)
    ps2 = ProductStorage(pool='file://' + cp)
    # two ProdStorage instances have the same DB
    p2 = ps2.getPool(ps2.getPools()[0])
    assert deepcmp(pspool._urns, p2._urns) is None
    assert deepcmp(pspool._tags, p2._tags) is None
    assert deepcmp(pspool._classes, p2._classes) is None

    # access resource
    # get ref from urn
    pref = ps.load(ref2[n - 2].urn)
    assert pref == ref2[n - 2]
    # actual product
    assert pref.product == x2[n - 2]
    # from tags

    # removal by reference urn
    print(ref2[n - 2].urn)
    ps.remove(ref2[n - 2].urn)
    # files are less
    assert sum(1 for x in pdp.glob(pcq + '*[0-9]')) == n
    # DB shows less in record
    cread = json.load(pdp.joinpath('classes.jsn').open())
    # current serial number not changed
    assert cread[pcq]['currentSN'] + 1 == n + 1
    # number of items decreased by 1
    assert len(cread[pcq]['sn']) == n

    # clean up a pool
    ps.wipePool(defaultpool)
    assert sum(1 for x in pdp.glob(pcq + '*[0-9]')) == 0
    assert len(ps.getPool(defaultpool)._urns) == 0


def test_Context():
    c1 = Context(description='1')
    c2 = Context(description='2')
    assert Context.isContext(c2.__class__)
    try:
        assert c1.isValid()
    except NotImplementedError as e:
        pass
    else:
        assert False

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
    assert c1 == c2
    c3 = MapContext()
    # syntax 3 # refs is a composite so set/get = []
    c3.refs["x"] = ProductRef(image)
    assert c3 == c2
    assert c3.refs['x'].product.description == 'hi'
    c4 = MapContext()
    # syntax 4. refs is a member in a composite (Context) so set/get = []
    c4['refs']["x"] = ProductRef(image)
    assert c3 == c4
    assert c4['refs']['x'].product.description == 'hi'

    # stored prod
    defaultpoolpath = '/tmp/pool'
    defaultpool = 'file://' + defaultpoolpath
    # create a prooduct
    x = Product(description='in store')
    # remove existing pools in memory
    PoolManager().removeAll()
    # create a product store
    pstore = ProductStorage()
    assert len(pstore.getPools()) == 1
    assert pstore.getWritablePool() == defaultpool
    assert Path(defaultpoolpath).is_dir()
    # clean up possible garbage of previous runs
    pstore.wipePool(defaultpool)
    assert Path(defaultpoolpath).is_dir()
    assert sum([1 for x in Path(defaultpoolpath).glob('*')]) == 0
    # save the product and get a reference
    prodref = pstore.save(x)
    # create an empty mapcontext
    mc = MapContext()
    # put the ref in the context.
    # The manual has this syntax mc.refs.put('xprod', prodref)
    # but I like this for doing the same thing:
    mc['refs']['xprod'] = prodref
    # get the urn
    urn = prodref.urn
    # re-create a product only using the urn
    newp = getProductObject(urn)
    # the new and the old one are equal
    assert newp == x

    # URN of an object in memory
    urn = Urn(cls=x.__class__, pool='mem:///' + str(os.getpid()),
              index=id(x)).urn
    newp = getProductObject(urn)
    # the new and the old one are equal
    assert newp == x

    des = checkjson(mc)

    newx = des['refs']['xprod'].product
    assert newx == x


if __name__ == '__main__':
    print("TableDataset demo")
    demo_TableDataset()

    print("CompositeDataset demo")
    demo_CompositeDataset()

# serializing using package jsonconversion

# from collections import OrderedDict
# import datetime

# from jsonconversion.encoder import JSONObjectEncoder, JSONObject
# from jsonconversion.decoder import JSONObjectDecoder


# class MyClass(JSONObject):

#     def __init__(self, a, b, c):
#         self.a = a
#         self.b = b
#         self.c = c

#     @classmethod
#     def from_dict(cls, dict_):
#         return cls(dict_['a'], dict_['b'], dict_['c'])

#     def to_dict(self):
#         return {'a': self.a, 'b': self.b, 'c': self.c}

#     def __eq__(self, other):
#         return self.a == other.a and self.b == other.b and self.c == other.c


# def test_jsonconversion():
#     l = OrderedDict(d=0)
#     d = datetime.datetime.now()
#     a1 = MyClass(1, 2, 'pp')
#     s = dict(name='SVOM', year=2019, result=[1.3, 4.7, 6, 45, a1])
#     data = dict(k=4, h=MyClass(1, l, s))
#     print(data)
#     print('---------')
#     js = json.dumps(data, cls=JSONObjectEncoder)
#     #js = serializeClassID(data)
#     # print(js)
#     #js = json.dumps(data)
#     print(js)
#     p = json.loads(js, cls=JSONObjectDecoder)
#     print(p['h'].b)
