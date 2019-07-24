import datetime
import traceback
from pprint import pprint
import json
from pathlib import Path
import os

from .logdict import doLogging, logdict
if doLogging:
    import logging
    import logging.config
    # create logger
    logging.config.dictConfig(logdict)
    logger = logging.getLogger()
    logger.debug('%s logging level %d' %
                 (__name__, logger.getEffectiveLevel()))

from dataset.annotatable import Annotatable
from dataset.copyable import Copyable
from dataset.odict import ODict
from dataset.serializable import serializeClassID, SerializableEncoder
from dataset.eq import deepcmp
from dataset.quantifiable import Quantifiable
from dataset.listener import EventSender, DatasetBaseListener
from dataset.composite import Composite
from dataset.metadata import Parameter, NumericParameter, MetaDataHolder, MetaData, Attributable, AbstractComposite
from dataset.datawrapper import DataWrapper, DataWrapperMapper
from dataset.dataset import ArrayDataset, TableDataset, CompositeDataset, Column
from dataset.product import FineTime1, History, Product
from dataset.deserialize import deserializeClassID


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
    des = deserializeClassID(js, dglobals=globals(), debug=dbg)
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
        # print(' DIR \n' + str(dir(obj)) + '\n' + str(dir(des)))
    if issubclass(obj.__class__, Product):
        obj.meta.listeners = []
        des.meta.listeners = []
    assert obj == des
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


from pal.urn import Urn
from pal.productstorage import ProductStorage
from pal.productref import ProductRef
from pal.comparable import Comparable
from pal.context import Context, MapContext, MapRefsDataset
from pal.common import getProductObject


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
    # urn with pool
    v = Urn(cls=prd.__class__, pool=p, index=a5)
    assert v.getScheme() == a1
    assert v.getFullPath(u) == a2 + a3 + '/' + rp  # s:/b/tmp/foo/c
    # urn with storage that does not match urn
    try:
        v = Urn(urn=u, cls=prd.__class__, pool=p, index=a5)
    except Exception as e:
        assert issubclass(e.__class__, ValueError)
    print(v.toString())
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

    # utils
    assert Urn.parseUrn(u) == (p, a4, str(a5), a1, a2, a2 + a3)

    checkjson(v)


def test_MapRefsDataset():
    a1 = 'foo'
    a2 = 'bar'
    d = MapRefsDataset()
    d.put(a1, a2)
    assert d[a1] == a2


def test_ProductRef():
    defaultpool = 'file:///tmp/pool'
    prd = Product()
    a1 = 'file'
    a2 = ''
    a3 = defaultpool
    a4 = prd.__class__.__qualname__
    a5 = 43
    s = a1 + '://' + a2   # file://s:
    p = s + a3
    r = a4 + ':' + str(a5)
    u = 'urn:' + p + ':' + r

    mr = ProductRef(prd)
    assert mr.urnobj == prd
    uobj = Urn(urn=u)
    # construction
    pr = ProductRef(urnobj=uobj)
    assert pr.urn == u
    assert pr.urnobj == uobj
    # parent
    b1, b2 = 'abc', '3c273'
    pr.addParent(b1)
    pr.addParent(b2)
    assert b1 in set(pr.parents)
    assert b2 in set(pr.parents)
    pr.removeParent(b1)
    assert b1 not in set(pr.parents)
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

    x = Product(description="This is my product example",
                instrument="MyFavourite", modelName="Flight")
    pcq = x.__class__.__qualname__
    # constructor
    ps = ProductStorage()
    p1 = ps.getPools()[0]
    assert p1 == defaultpool
    pspool = ps.getPool(p1)
    assert len(pspool['classes']) == 0
    # save
    ref = ps.save(x)
    assert ref.urn == 'urn:' + defaultpool + ':' + pcq + ':0'
    # count files in pool and entries in class db
    assert sum(1 for x in pdp.glob(pcq + '*[0-9]')) == 1
    cread = json.load(pdp.joinpath('classes.jsn').open())
    assert cread[pcq]['currentSN'] + 1 == 1

    # save more
    n = 5
    x2, ref2 = [], []
    for d in range(n):
        tmp = Product(description='x' + str(d))
        x2.append(tmp)
        ref2.append(ps.save(tmp, tag='t' + str(d)))
    # count files in pool
    assert sum(1 for x in pdp.glob(pcq + '*[0-9]')) == 1 + n
    # number of prod in the DB
    cread = json.load(pdp.joinpath('classes.jsn').open())
    assert cread[pcq]['currentSN'] + 1 == 1 + n

    # multiple storages pointing to the same pool will get exception
    try:
        ps2 = ProductStorage()
    except Exception as e:
        pass
    else:
        assert 1  # False

    # read HK
    # make a copy of the pool
    cp = defaultpoolpath + '_copy'
    os.system('rm -rf ' + cp + '; cp -rf ' + defaultpoolpath + ' ' + cp)
    ps2 = ProductStorage(pool='file://' + cp)
    # two ProdStorage instances have the same DB
    p2 = ps2.getPool(ps2.getPools()[0])
    assert len(pspool) == len(p2)
    assert deepcmp(pspool['classes'], p2['classes']) is None
    assert deepcmp(pspool['tags'], p2['tags']) is None

    # tags
    ts = ps.getAllTags()
    assert len(ts) == n
    print(ps)
    ts = ps.getTags(ref2[3].urn)
    assert len(ts) == 1
    assert ts[0] == 't3'
    u = ps.getUrnFromTag('t3')
    assert len(u) == 1
    assert u[0] == ref2[3].urn

    # access resource
    # get ref from urn
    pref = ps.load(ref2[n - 2].urn)
    assert pref == ref2[n - 2]
    # actual product
    assert pref.product == x2[n - 2]
    # from tags

    # removal by reference urn
    ps.remove(ref2[n - 2].urn)
    # files are less
    assert sum(1 for x in pdp.glob(pcq + '*[0-9]')) == n
    # DB shows less in record
    cread = json.load(pdp.joinpath('classes.jsn').open())
    # current serial number not changed
    assert cread[pcq]['currentSN'] + 1 == n + 1
    # number of items decreased by 1
    assert len(cread[pcq]['sn2tag']) == n

    # clean up a pool
    ps.wipePool(defaultpool)
    assert sum(1 for x in pdp.glob(pcq + '*[0-9]')) == 0
    assert sum(1 for x in ps.getPool(defaultpool)['classes']) == 0


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
    #assert not c1.hasDirtyReferences('ok')
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
    t = c4['refs']["x"] = ProductRef(image)
    assert c3 == c4
    assert c4['refs']['x'].product.description == 'hi'

    # stored prod
    defaultpoolpath = '/tmp/pool'
    defaultpool = 'file://' + defaultpoolpath
    # create a prooduct
    x = Product(description='in store')
    # create a product store
    pstore = ProductStorage()
    # clean up possible garbage of previous runs
    pstore.wipePool(defaultpool)
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
