import fdi.dataset.namespace
from fdi.dataset.namespace import NameSpace_meta, Lazy_Loading_ChainMap, Load_Failed

from collections import ChainMap
import pytest
import importlib
import copy
import sys
import logging

# from test_dataset import check_Product

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
else:
    PY3 = False

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


@pytest.fixture(scope='function')
def NSmeta():
    yield fdi.dataset.namespace.NameSpace_meta
    importlib.reload(fdi.dataset.namespace)


@pytest.fixture(scope='function')
def claz():
    import fdi.dataset.classes
    importlib.reload(fdi.dataset.classes)
    from fdi.dataset.classes import Classes
    return Classes


def test_Lazy(NSmeta):
    d = object()
    a = {"a": d, "f": 8}
    b = {"c": 55}
    e = {"ee": 0, "c": 22}
    v = Lazy_Loading_ChainMap(a, b, extensions=[e])
    assert v
    lab = len(a)+len(b)
    assert len(v.initial) == lab
    assert len(v.cache) == 0
    # first access removes 'a' from initial
    assert v["a"] is d
    assert len(a) == 2
    assert len(b) == 1
    assert len(v.initial) == lab-1
    # e has only 1 unique key. len =  + (len(e)-1)
    assert len(v) == len(v.initial) + len(v.cache) + (len(e)-1)
    assert len(v.cache) == 1
    assert v.cache['a'] is d
    # accessing again won't move anything
    assert v["a"] is d
    assert len(a) == 2
    assert len(b) == 1
    assert len(v.initial) == lab-1
    # same with the other map
    v["c"] = 99
    assert len(a) == 2
    # 'c' is still in b
    assert len(b) == 1
    assert 'c' in b
    assert len(v.cache) == 2
    assert 'c' in v.cache
    # 'c' is not in initial
    assert 'c' not in v.initial
    assert len(v.initial) == lab-2
    assert v["c"] == 99
    # access extensions
    assert v["ee"] == 0
    # cache has priority
    assert v["c"] == 99
    # len(v) is correct, the sum of lens of initial and cache
    assert len(v) == lab + (len(e)-1)
    assert len(v) == len(v.initial) + len(v.cache) + (len(e)-1)
    assert v.cache['c'] == 99
    # intentionally feed cache a failure mark
    v.initial['f'] = Load_Failed
    # make sure the above did store 'f' in cache
    assert len(v.cache) == 2
    assert v.initial['f'] is Load_Failed
    assert len(v.cache) == 2
    v.ignore_error = True
    # reading result is None
    assert v['f'] is None
    v.ignore_error = False
    assert len(v.initial) == 1
    assert 'f' in v.initial
    assert 'f' not in v.cache
    assert len(v) == lab + (len(e)-1)
    assert len(v) == len(v.initial) + len(v.cache) + (len(e)-1)
    # exclude
    v.exclude.append('a')

    assert v['a'] is None
    with pytest.raises(KeyError):
        assert v['nonexist'] is None
    v.ignore_error = True
    assert v['nonexist'] is None


def test_NameSpace_func(NSmeta):
    d = object()
    a = {"a": d, "f": 8}
    b = {"c": 55}
    e = {"ee": 0, "c": 22}
    cnt = 0
    from functools import wraps

    def counter(f):
        @wraps
        def w(*a, **k):
            nonlocal cnt
            f(*a, **k)
            cnt += 1
        return w

    def loada(key, mapping, remove=True, exclude=None, ignore_error=False):
        logger.debug(key)
        nonlocal cnt
        cnt += 1
        logger.debug('cnt = %d' % cnt)
        return fdi.dataset.namespace.refloader(key, mapping, remove, exclude=exclude, ignore_error=ignore_error)

    class ns(metaclass=NSmeta,
             sources=[a, b],
             extensions=[e],
             load=loada,
             loadcount=0
             ):
        def __init__(cls, *args, **kwds):
            super().__init__(*args, **kwds)

#
#    class ns(metaclass=nsm):
#        pass
#
    tmap = ns.mapping
    assert cnt == 0

    assert tmap['a'] is d
    assert cnt == 1
    assert tmap.cache['a'] is d
    # e has only 1 unique key. len =  + (len(e)-1)
    assert len(tmap) == len(a)+len(b) + (len(e)-1)
    ns.update({'c': 77})
    # update does not load anything
    assert cnt == 1
    assert list(tmap) == ['ee', 'c', 'f', 'a']
    # getting index does not load anything
    assert cnt == 1
    assert tmap['c'] == 77
    assert len(tmap.initial) == 1
    assert len(tmap) == 3 + (len(e)-1)
    assert cnt == 1
    t = copy.copy(tmap)
    t = copy.deepcopy(tmap)
    assert cnt == 1
    d = dict(tmap)
    assert cnt == 3
    # repr calls each of the maps directly. no loading.
    print(tmap)
    assert cnt == 3
    ns.clear()
    assert len(tmap) == 0
    ns.reload()
    assert len(tmap.initial) == 3
    assert len(tmap.cache) == 0
    assert len(e) == 0
    assert len(tmap) == 3 + len(e)
    assert cnt == 3


def test_SubProduct(claz):
    from fdi.dataset.testproducts import SP
    from fdi.dataset.baseproduct import BaseProduct

    Classes = claz

    # equivalence
    v = Classes.mapping['BaseProduct']
    assert v is BaseProduct

    y = SP()

    # register it in Classes so deserializer knows how to instanciate.
    Classes.update({'SP': SP})

    assert issubclass(SP, BaseProduct)

    from fdi.pal.context import MapContext

    class SSP(SP, MapContext):
        def __init__(self, **kwds):
            super().__init__(**kwds)

    x = SSP()
    x.instrument = 'ff'
    assert x.instrument == 'ff'
    x.rr = 'r'
    assert x.rr == 'r'


def test_Classes(claz):
    from fdi.dataset.baseproduct import BaseProduct
    PC = claz
    prjcls = PC.mapping
    nc = len(prjcls)
    assert nc > 44
    assert issubclass(prjcls.__class__, ChainMap)
    assert 'Product' in prjcls
    PC.clear()
    m = prjcls
    assert len(m) == 0
    # clear() replenishes `initial` map
    PC.reload()
    assert len(prjcls) == len(prjcls.sources)
    c = prjcls['Product']
    assert c
    assert issubclass(c, BaseProduct)
    assert c(description='foobar').description == 'foobar'
    # Add a class to current namespace
    PC.update({'foo': int})
    # it shows in mapping
    assert 'foo' in prjcls
    # but not in PC.mapping.initial
    assert 'foo' not in prjcls.initial
    assert 'foo' not in prjcls.sources
    # mockup "permanent" updating PC.sources
    prjcls.sources.update({'path': 'sys'})
    assert 'path' in prjcls.sources
    assert 'path' not in prjcls
    # to make the change into effect, one has to re-run loading module_class
    PC.reload()
    assert 'path' in prjcls
    assert issubclass(prjcls['path'].__class__, list)
    # if there arre a lot of new classes e.g. there is a new package, to add
    # mockup permanent updating PC.sources with a dict of classname:class_obj/module_name

    class foo():
        pass

    PC.update({'maxsize': 'sys', 'f_': foo}, extension=True)
    assert 'maxsize' in prjcls.sources
    assert 'f_' in prjcls.sources
    assert 'maxsize' not in prjcls
    assert 'f_' not in prjcls
    # to make the change into effect, one has to re-run loading module_class
    PC.reload()
    assert 'maxsize' in prjcls
    assert prjcls['maxsize'] == sys.maxsize
    assert 'f_' in prjcls
    assert issubclass(prjcls['f_'], foo)

# add name spacw


def test_gb(claz):
    from fdi.dataset.baseproduct import BaseProduct

    Classes = claz
    Class_Look_Up = Classes.mapping
    nm = len(Classes.mapping.maps)
    assert 'wakaka' not in Class_Look_Up
    _bltn = dict((k, v) for k, v in {'wakaka': tuple}.items() if k[0] != '_')
    Classes.mapping.add_ns(_bltn, order=-1)
    assert nm+1 == len(Classes.mapping.maps)
    p = Class_Look_Up['Product']

    assert isinstance(p, type)
    assert issubclass(p, BaseProduct)
    assert 'Product' in Class_Look_Up.maps[0]
    assert Class_Look_Up.cache['Product'] is p

    assert 'wakaka' in Class_Look_Up.maps[-1]
    assert 'wakaka' in Class_Look_Up
    Classes.mapping.add_ns({'foo': bytes}, order=0)
    assert nm+2 == len(Classes.mapping.maps)
    assert 'foo' in Class_Look_Up.maps[0]
    assert 'foo' in Class_Look_Up
