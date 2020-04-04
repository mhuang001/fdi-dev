#
#
# -*- coding: utf-8 -*-
import datetime
import traceback
from pprint import pprint
import copy
import json
import sys
# import __builtins__
#print([(k, v) for k, v in globals().items() if '__' in k])

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
else:
    PY3 = False

if __name__ == '__main__' and __package__ is None:
    from outputs import nds2, nds3, out_TableDataset, out_CompositeDataset
else:
    # This is to be able to test w/ or w/o installing the package
    # https://docs.python-guide.org/writing/structure/
    from .pycontext import spdc

    from .outputs import nds2, nds3, out_TableDataset, out_CompositeDataset

    from .logdict import doLogging, logdict
    if doLogging:
        import logging
        import logging.config
        # create logger
        logging.config.dictConfig(logdict)
        logger = logging.getLogger()
        logger.debug('%s logging level %d' %
                     (__name__, logger.getEffectiveLevel()))

from spdc.dataset.annotatable import Annotatable
from spdc.dataset.copyable import Copyable
from spdc.dataset.odict import ODict
from spdc.dataset.serializable import serializeClassID, SerializableEncoder
from spdc.dataset.eq import deepcmp
from spdc.dataset.quantifiable import Quantifiable
from spdc.dataset.listener import EventSender, DatasetBaseListener
from spdc.dataset.composite import Composite
from spdc.dataset.metadata import Parameter, NumericParameter, MetaData
from spdc.dataset.datawrapper import DataWrapperMapper
from spdc.dataset.metadataholder import MetaDataHolder
from spdc.dataset.attributable import Attributable
from spdc.dataset.abstractcomposite import AbstractComposite
from spdc.dataset.datawrapper import DataWrapper, DataWrapperMapper
from spdc.dataset.dataset import ArrayDataset, TableDataset, CompositeDataset, Column, ndprint
from spdc.dataset.product import FineTime, FineTime1, History, Product, utcobj
from spdc.dataset.deserialize import deserializeClassID


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
    des = deserializeClassID(js, lgb=copy.copy(
        globals()).update(locals()), debug=dbg)
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
    if 0 and issubclass(obj.__class__, Product):
        print(str(id(obj)) + ' ' + obj.toString())
        print(str(id(des)) + ' ' + des.toString())
        # obj.meta.listeners = []
        # des.meta.listeners = []
    assert obj == des, deepcmp(obj, des)
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


def test_deepcmp():
    i1 = 3982
    i2 = 3982
    i3 = 6666.2
    t1 = (765, i1, 'd')
    t2 = (765, 3982, 'd')
    t3 = (765, 3982, 'd', 'p')
    s1 = {9865, i2, 0.311}
    s2 = {9865, 3982, 0.311}
    s3 = {9865, 0.311}
    s4 = {9800, 3983, 0.311}
    l1 = [6982, i1, t1, 3982]
    l2 = [6982, i1, (765, 3982, 'd'), 3982]
    l3 = [6982, i1, t3, 3982]
    d1 = {3982: i1, t1: i2, i3: t1, t3: l1}
    d2 = {i2: 3982, t2: i1, 6666.2: t2, (765, 3982, 'd', 'p'): l2}
    d3 = {i2: 3982, '4': i1, i3: t1, (765, 3982, 'd'): l1}
    d4 = {i2: 3982, t2: i1, 6666.2: t2, (765, 3982, 'd', 'p'): d1}
    r = deepcmp(i1, i2)
    assert r is None
    r = deepcmp(t1, t2)
    assert r is None
    r = deepcmp(s1, s2)
    assert r is None
    r = deepcmp(l1, l2)
    assert r is None
    r = deepcmp(d1, d2)
    assert r is None
    #

    def nc(a1, a2):
        # print('--------------------')
        r = deepcmp(a1, a2)
        assert r is not None
        # print(a1)
        # print(a2)
        # print(r)
    nc(i1, i3)
    nc(t1, t3)
    nc(s1, s3)
    nc(s1, s4)
    nc(l1, l3)
    nc(d1, d3)
    nc(d1, d4)


def test_serialization():
    v = 1
    checkjson(v)
    v = 'a'
    checkjson(v)
    v = 3.4
    checkjson(v)
    v = True
    checkjson(v)
    v = None
    checkjson(v)
    #v = b'\xde\xad\xbe\xef'
    # checkjson(v)
    v = [1.2, 'ww']
    checkjson(v)
    v = {'e': 4, 'y': {'d': 'ff', '%': '$'}}
    checkjson(v)


def ndlist(*args):
    """ Generates an N-dimensional array with list.
    ``ndlist(2, 3, 4, 5)`` will make a list of 2 lists of 3 lists of 4 lists of 5 elements of 0.
    https://stackoverflow.com/a/33460217
    """
    dp = 0
    for x in reversed(args):
        dp = [copy.deepcopy(dp) for i in range(x)]
    return dp


def test_ndprint():
    s = [1, 2, 3]
    v = ndprint(s)
    # print(v)
    # table, 1 column
    assert v == '1 \n2 \n3 \n'
    v = ndprint(s, trans=False)
    # print(v)
    # 1D matrix. 1 row.
    assert v == '1 2 3 '
    s = [[i + j for i in range(2)] for j in range(3)]
    v = ndprint(s)
    # print(v)
    # 2x3 matrix 3 columns 2 rows
    assert v == '0 1 2 \n1 2 3 \n'
    v = ndprint(s, trans=False)
    # print(v)
    # 2x3 table view 2 columns 3 rows
    assert v == '0 1 \n1 2 \n2 3 \n'

    s = ndlist(2, 3, 4, 5)
    s[0][1][0] = [0, 0, 0, 0, 0]
    s[0][1][1] = [0, 0, 0, 1, 0]
    s[0][1][2] = [5, 4, 3, 2, 1]
    s[0][1][3] = [0, 0, 0, 3, 0]
    v = ndprint(s, trans=False)
    # print(v)
    assert v == nds2
    v = ndprint(s)
    # print(v)
    assert v == nds3
    # pprint.pprint(s)


def test_Annotatable():

    v = Annotatable()
    assert v.getDescription() == 'UNKNOWN'
    a = 'this'
    v = Annotatable(a)
    assert v.getDescription() == a
    assert v.description is v.getDescription()
    a1 = 'that'
    v.setDescription(a1)
    assert v.description == a1
    v.description = a
    assert v.description == a
    checkgeneral(v)


def test_Composite():

    # set/get
    a1 = 'this'
    a2 = 'that'
    v = Composite()
    v.set(a1, a2)
    assert v.get(a1) == a2
    # keyword arg, new value substitute old
    a3 = 'more'
    v.set(name=a1, dataset=a3)
    assert v.get(a1) == a3

    # access
    v = Composite()
    v[a1] = a2  # DRM doc case 'v.get(a1)' == 'v[a1]'
    assert v[a1] == a2
    assert v[a1] == v.get(a1)
    sets = v.getSets()
    assert issubclass(sets.__class__, dict)

    # dict view
    a3 = 'k'
    a4 = 'focus'
    v[a3] = a4
    assert [k for k in v] == [a1, a3]
    assert [(k, v) for (k, v) in v.items()] == [(a1, a2), (a3, a4)]

    # remove
    v = Composite()
    v.set(a1, a2)
    assert v[a1] == a2
    assert v.remove(a1) == a2
    assert v.size() == 0
    assert v.remove(a1) is None
    assert v.remove('notexist') is None

    # test for containsKey, isEmpty, keySet, size
    v = Composite()
    assert v.containsKey(a1) == False
    assert v.isEmpty() == True
    ks = v.keySet()
    assert len(ks) == 0
    assert v.size() == 0
    v.set(a1, a2)
    assert v.containsKey(a1) == True
    assert v.isEmpty() == False
    ks = v.keySet()
    assert len(ks) == 1 and ks[0] == a1
    assert v.size() == 1

    checkgeneral(v)


def test_AbstractComposite():

    v = AbstractComposite()
    assert issubclass(v.__class__, Annotatable)
    assert issubclass(v.__class__, Attributable)
    assert issubclass(v.__class__, DataWrapperMapper)
    checkgeneral(v)


def test_Copyable():
    """ tests in a subprocess. """
    class Ctest(Copyable):
        def __init__(self, _p, **kwds):
            self.p = _p
            super(Ctest, self).__init__(**kwds)

        def get(self):
            return self.p

    old = [[1, 1, 1], [2, 2, 2], [3, 3, 3]]
    v = Ctest(old)
    new = v.copy().get()
    old[1][1] = 'AA'
    assert new[1][1] == 2
    assert id(old) != id(new)

    checkgeneral(v)


def test_EventSender():
    global test123

    class MockFileWatcher(EventSender):
        """ Preferred: subclassing EvenSender """

        def watchFiles(self):
            source_path = "foo"
            self.fire(source_path)

    class MockFileWatcher2():
        """ evensender is an attribute """

        def __init__(self):
            self.fileChanged = EventSender()

        def watchFiles(self):
            source_path = "foo"
            self.fileChanged(source_path)

    class MockListener(DatasetBaseListener):
        pass

    def log_file_change(source_path):
        global test123
        r = "%r changed." % (source_path)
        # print(r)
        test123 = r

    def log_file_change2(source_path):
        global test123
        r = "%r changed2." % (source_path)
        # print(r)
        test123 = r

    l1 = MockListener()
    l1.targetChanged = log_file_change
    l2 = MockListener()
    l2.targetChanged = log_file_change2

    watcher = MockFileWatcher()
    watcher.addListener(l2)
    watcher.addListener(l1)
    watcher.removeListener(l2)
    watcher.watchFiles()
    assert test123 == "'foo' changed."

    test123 = 0
    watcher = MockFileWatcher2()
    watcher.fileChanged.addListener(l2)
    watcher.fileChanged.addListener(l1)
    watcher.fileChanged.removeListener(l2)
    watcher.watchFiles()
    assert test123 == "'foo' changed."


def test_Parameter():
    # python  keeps an array of integer objects for all integers
    # between -5 and 256 so do not use small int for testing
    # because one cannot make a copy

    # test equivalence of v.setValue(a) and v.value=a
    a2 = 300
    a1 = 'a test parameter'
    v = Parameter()
    v.description = a1
    v.setValue(a2)
    assert v.value == a2

    # test constructor
    v = Parameter()
    assert v.description == 'UNKNOWN'  # inherited from Anotatable
    assert v.value is None  # inherited from Anotatable
    a2 = 300
    v = Parameter(a2)  # description has a default so a2 -> 'value'
    assert v.description == 'UNKNOWN'  # inherited from Anotatable
    assert v.value == a2
    a1 = 'a test parameter'
    v = Parameter(description=a1)
    assert v.description == a1
    assert v.value is None
    v = Parameter(a2, description=a1)  # only one positional argument
    assert v.value == a2
    assert v.description == a1
    v = Parameter(description=a1, value=a2)  # arbitrary argument order here
    assert v.description == a1
    assert v.value == a2

    # getType
    assert v.getValue() == a2
    assert v.getType() == ''

    # test equals
    b1 = ''.join(a1)  # make a new string copy
    b2 = a2 + 0  # make a copy
    v1 = Parameter(description=b1, value=b2)
    assert v.equals(v1)
    assert v == v1
    v1.value = -4
    assert not v.equals(v1),   deepcmp(v, v1, verbose=True)
    assert v != v1
    b2 = a2 + 0  # make a copy
    v1.value = b2  # change it back
    v1.description = 'changed'
    assert not v.equals(v1)
    assert v != v1

    # serializing
    a1 = 'a test parameter'
    a2 = 351
    v = Parameter(description=a1, value=a2)
    checkjson(v)
    b1 = 'a binary par'
    b2 = 'z'  # b'\xaa\x55'
    v = Parameter(description=b1)
    v.value = b2
    checkjson(v)

    assert v.toString() == str(v)

    # event
    global test123
    test = None

    class MockListener(DatasetBaseListener):
        def targetChanged(self, e):
            global test123
            r = "%r changed." % (e)
            # print(r)
            test123 = r
    l = MockListener()
    v.addListener(l)
    v.value = 4
    # print(test123)

    checkgeneral(v)


def test_Quantifiable():
    a = 'volt'
    v = Quantifiable(a)
    assert v.unit == a
    assert v.getUnit() == a
    v = Quantifiable()
    v.setUnit(a)
    assert v.unit == a


def test_NumericParameter():
    a1 = 'a test NumericParameter'
    a2 = 100
    a3 = 'second'
    v = NumericParameter(description=a1, value=a2, unit=a3)
    assert v.description == a1
    assert v.value == a2
    assert v.unit == a3

    checkjson(v)

    # equals
    a4 = ''.join(a3)  # same contents
    v1 = NumericParameter(description=a1, value=a2, unit=a4)
    assert v == v1
    assert v1 == v
    v1.unit = 'meter'
    assert v != v1
    assert v1 != v

    checkgeneral(v)


def test_MetaData():
    a1 = 'foo'
    a2 = Parameter(description='test param', value=900)
    v = MetaData()
    v.set(a1, a2)
    assert v.get(a1) == a2
    # print(v)
    a3 = 'more'
    v.set(name=a1, newParameter=a3)
    assert v[a1] == a3

    v = MetaData()
    v[a1] = a2  # DRM doc case
    assert v[a1] == a2
    a4 = NumericParameter(description='another param',
                          value=2.3, unit='sec')
    v[a3] = a4

    checkjson(v)

    v.remove(a1)  # inherited from composite
    assert v.size() == 1

    # copy
    c = v.copy()
    assert c is not v
    assert v.equals(c)
    assert c.equals(v)

    # equality
    a1 = 'foo'
    a2 = Parameter(description='test param', value=534)
    a3 = 'more'
    a4 = NumericParameter(description='another param',
                          value=2.3, unit='sec')
    v = MetaData()
    v[a1] = a2
    v[a3] = a4
    b1 = ''.join(a1)
    b2 = a2.copy()
    b3 = ''.join(a3)
    b4 = a4.copy()
    v1 = MetaData()
    v1[b1] = b2
    v1[b3] = b4
    assert v == v1
    assert v1 == v
    v1[b3].value += 3
    assert v != v1
    assert v1 != v
    b4 = a4.copy()
    v1[b3] = b4
    v1['foo'] = 'bar'
    assert v != v1

    checkgeneral(v)


def test_Attributable():
    v = Attributable()
    assert v.getMeta().size() == 0  # inhrited no argument instanciation
    a1 = MetaData()
    a2 = 'this'
    a3 = Parameter(0.3)
    a1[a2] = a3  # add an entry to metadata
    v.setMeta(a1)
    assert v.getMeta() == a1
    assert v.getMeta().size() == 1

    # dot notion for easier access: get and set
    assert v.getMeta() == v.meta
    v2 = Attributable()
    v2.meta = a1
    assert v.meta == v2.meta

    # constructor with named parameter
    v = Attributable(meta=a1)
    assert v.getMeta() == a1

    checkgeneral(v)


def test_DataWrapper():
    a1 = [1, 4.4, 5.4E3]
    a2 = 'ev'
    a3 = 'three energy vals'
    v = DataWrapper(description=a3)
    assert v.hasData() == False
    v.setData(a1)
    v.setUnit(a2)
    assert v.hasData() == True
    assert v.data == a1
    assert v.unit == a2
    assert v.description == a3

    v = DataWrapper(data=a1, unit=a2, description=a3)
    assert v.hasData() == True
    assert v.data == a1
    assert v.unit == a2
    assert v.description == a3

    checkgeneral(v)


def test_ArrayDataset():
    # from DRM
    a1 = [1, 4.4, 5.4E3]      # a 1D array of data
    a2 = 'ev'                 # unit
    a3 = 'three energy vals'  # description
    v = ArrayDataset(data=a1, unit=a2, description=a3)
    v1 = ArrayDataset(data=a1)
    assert v1.unit is None
    # omit the parameter names, the orders are data, unit, description
    v2 = ArrayDataset(a1)
    assert v2.data == a1
    v2 = ArrayDataset(a1, a2)
    assert v2.data == a1
    assert v2.unit == a2
    v2 = ArrayDataset(a1, a2, a3)
    assert v2.data == a1
    assert v2.unit == a2
    assert v2.description == a3

    # COPY
    c = v.copy()
    assert v == c
    assert c == v

    # test data and unit
    a3 = [34, 9999]
    a4 = 'm'
    a5 = 'new description'
    v.data = a3
    v.unit = a4
    assert v.data == a3
    assert v.unit == a4
    assert v.data[1] == 9999

    # test equality
    a1 = [1, 4.4, 5.4E3]
    a2 = 'ev'
    a3 = 'three energy vals'
    v = ArrayDataset(data=a1, unit=a2, description=a3)
    a4 = 'm1'
    a5 = NumericParameter(description='a param in metadata',
                          value=2.3, unit='sec')
    v.meta[a4] = a5

    # b[1-5] and v1 have the  same contents as a[1-5] and v
    b1 = [1, 4.4, 5.4E3]
    b2 = ''.join(a2)
    b3 = ''.join(a3)
    v1 = ArrayDataset(data=b1, unit=b2, description=b3)
    b4 = ''.join(a4)
    b5 = NumericParameter(description='a param in metadata',
                          value=2.3, unit='sec')
    v1.meta[b4] = b5

    # equal
    assert v == v1
    assert v1 == v
    # not equal
    # change data
    v1.data += [6]
    assert v != v1
    assert v1 != v
    # restore v1 so that v==v1
    v1.data = copy.deepcopy(a1)
    assert v == v1
    # change description
    v1.description = 'changed'
    assert v != v1
    assert v1 != v
    # restore v1 so that v==v1
    v1.description = ''.join(a3)
    assert v == v1
    assert id(v) != id(v1)
    # change meta
    v1.meta[b4].description = 'c'
    assert v != v1
    assert v1 != v

    # data access
    d = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    x = ArrayDataset(data=d)
    assert x.data[1][2] == 6
    assert x.data[1][2] == x[1][2]
    # slice [0:2] is [[1,2,3][4,5,6]]
    y = x[0:2]
    assert y[1][0] == 4
    # removal
    r0 = x[0]
    x.remove(r0)
    assert x[0][2] == 6  # x=[[4, 5, 6], [7, 8, 9]]
    r0 = x[0]
    assert r0 == x.pop(0)
    assert x[0][1] == 8

    # iteration
    i = []
    for m in v:
        i.append(m)
    assert i == a1

    # toString()
    s = ndlist(2, 3, 4, 5)
    x = ArrayDataset(data=s)
    x[0][1][0] = [0, 0, 0, 0, 0]
    x[0][1][1] = [0, 0, 0, 1, 0]
    x[0][1][2] = [5, 4, 3, 2, 1]
    x[0][1][3] = [0, 0, 0, 3, 0]
    ts = x.toString()
    i = ts.index('0 0 0 0')
    # print(ts)
    assert ts[i:] == nds3 + '\n'

    checkjson(v)
    checkgeneral(v)


def test_TableModel():
    pass


def test_TableDataset():
    # constructor
    # if data is not a sequence an exception is thrown
    try:
        t = 5
        t = ArrayDataset(data=42)
    except Exception as e:
        assert issubclass(e.__class__, TypeError)
    assert t == 5

    # setData format 1: data is a sequence of dict
    a1 = [dict(name='col1', column=Column(data=[1, 4.4, 5.4E3], unit='eV')),
          dict(name='col2', column=Column(data=[0, 43.2, 2E3], unit='cnt'))
          ]
    v = TableDataset(data=a1)  # inherited from DataWrapper
    assert v.getColumnCount() == len(a1)
    assert v.getColumnName(0) == a1[0]['name']  # 'col1'
    t = a1[1]['column'].data[1]  # 43.2
    assert v.getValueAt(rowIndex=1, columnIndex=1) == t

    # 2: another syntax, same effect as last
    a2 = [{'name': 'col1', 'column': Column(data=[1, 4.4, 5.4E3], unit='eV')},
          {'name': 'col2', 'column': Column(data=[0, 43.2, 2E3], unit='cnt')}]
    v2 = TableDataset(data=a2)
    assert v == v2

    # 3: data is a mapping
    a4 = dict(col1=Column(data=[1, 4.4, 5.4E3], unit='eV'),
              col2=Column(data=[0, 43.2, 2E3], unit='cnt'))
    v4 = TableDataset(data=a4)
    assert v == v4

    # 3: *Quickest?* list of tuples that do not need to use Column
    v3 = TableDataset(data=[('col1', [1, 4.4, 5.4E3], 'eV'),
                            ('col2', [0, 43.2, 2E3], 'cnt')
                            ])
    assert v == v3

    # add, set, and replace columns
    # column set / get
    u = TableDataset()
    c1 = Column([1, 4], 'sec')
    u.addColumn('col3', c1)
    # for non-existing names set is addColum.
    c2 = Column([2, 3], 'eu')
    u['col4'] = c2
    assert u['col4'][0] == 2
    # replace column for existing names
    c3 = Column([5, 7], 'j')
    u['col4'] = c3
    assert u['col4'][0] == c3.data[0]
    # addRow
    assert u.rowCount == 2
    cc = copy.deepcopy(c1)
    c33, c44 = 3.3, 4.4
    cc.append(c33)
    u.addRow({'col4': c44, 'col3': c33})
    assert u.rowCount == 3
    assert u['col3'] == cc
    # removeRow
    assert u.removeRow(u.rowCount - 1) == [c33, c44]
    assert u.rowCount == 2

    # access
    # unit access
    assert u['col4'].unit == 'j'
    # access index with indexOf
    assert u.indexOf('col3') == u.indexOf(c1)
    # access cell value
    u.setValueAt(aValue=42, rowIndex=1, columnIndex=1)
    assert u.getValueAt(rowIndex=1, columnIndex=1) == 42

    # replace whole table. see constructor examples for making a1
    u.data = a1
    assert v == u
    # col3,4 are gone
    assert list(u.data.keys()) == ['col1', 'col2']
    # But if providing a list of lists of data only for the existing columns, units sre not changed
    u.data = [[0, 9876, 66]]
    assert u['col1'][1] == 9876
    assert u['col1'].unit == 'eV'
    # list of lists of new data can go past current number of columns
    h = [6, 7, 8]
    u.data = [[0, 9876, 66], [1, 2, 3], h]
    assert u['col1'][1] == 9876
    assert u['col1'].unit == 'eV'
    # genric col[index] names and None unit are given for the added columns
    assert u['col3'][1] == 7  # index counts from 1 !
    assert u['col3'].unit is None

    # syntax ``in``
    assert 'col3' in u

    # toString()
    ts = v3.toString()
    # print(ts)
    # print(out_TableDataset)
    assert ts == out_TableDataset

    checkjson(u)
    checkgeneral(u)

    # doc cases
    # creation:
    ELECTRON_VOLTS = 'eV'
    SECONDS = 'sec'
    t = [x * 1.0 for x in range(10)]
    e = [2 * x + 100 for x in t]

    # creating a table dataset to hold the quantified data
    x = TableDataset(description="Example table")
    x["Time"] = Column(data=t, unit=SECONDS)
    x["Energy"] = Column(data=e, unit=ELECTRON_VOLTS)
    # copy
    # access:
    # See demo_XDataset

    # access
    column1 = x["Time"]
    column2 = x[0]  # same, but now by index
    assert column1 == column2
    text = x.description
    assert text == 'Example table'

    # addColumn
    m = [-tmp for tmp in t]
    c3 = Column(unit='m', data=m)
    assert x.columnCount == 2
    x.addColumn('dist', c3)
    assert x.columnCount == 3
    assert x[2][1] == m[1]

    # addRow
    assert x.rowCount == 10
    # https://stackoverflow.com/q/41866911
    #newR = ODict(Time=101, Energy=102, dist=103)
    newR = ODict()
    newR['Time'] = 101
    newR['Energy'] = 102
    newR['dist'] = 103
    x.addRow(newR)
    assert x.rowCount == 11
    # select
    c10 = x[1]
    r10 = x.select([10])
    assert r10[1][0] == c10[10]
    # iteration:
    # internal data model is based on OrderedDict so index access OK
    for i in range(x.rowCount - 1):
        row = x.getRow(i)
        assert row[0] == t[i]
        assert row[1] == e[i]
        assert row[2] == m[i]
    row = x.getRow(x.rowCount - 1)
    v = list(newR.values()) if PY3 else newR.values()
    for j in range(len(row)):
        assert row[j] == v[j]

    if 0:
        # Please see also this elaborated example.

        # Additionally you can filter the rows in a table, for example:

        xNew = x.select(x[0].data > 20)

    # Please see also this selection example.


def demo_TableDataset():

    # http://herschel.esac.esa.int/hcss-doc-15.0/load/hcss_drm/ia/dataset/demo/TableDataset.py
    ELECTRON_VOLTS = 'eV'
    SECONDS = 'sec'
    # create dummy numeric data:
    # t=Double1d.range(100)
    # e=2*t+100
    t = [x * 1.0 for x in range(10)]
    e = [2 * x + 10 for x in t]

    # creating a table dataset to hold the quantified data
    table = TableDataset(description="Example table")
    table["Time"] = Column(data=t, unit=SECONDS)
    table["Energy"] = Column(data=e, unit=ELECTRON_VOLTS)

    # alternative Column creation:
    c = Column()
    c.data = t
    c.unit = SECONDS
    table["Time1"] = c

    # alternative Column creation using Java syntax:
    c1 = Column()
    c1.setData(t)
    c1.setUnit(SECONDS)
    table.addColumn("Time2", c1)

    t1 = table.copy()
    t2 = table.copy()
    assert table.getColumnCount() == 4
    assert t1.getColumnCount() == 4
    # removing a column by name:
    t1.removeColumn("Time2")
    assert t1.getColumnCount() == 3

    # removing a column by index (removing "Time1")
    # NOTE: indices start at 0!
    t2.removeColumn(3)
    assert t1 == t2

    # adding meta:
    table.meta["Foo"] = Parameter(value="Bar", description="Bla bla")

    # table access:
    print(table)  # summary
    print(table.__class__)  # type
    print(table.rowCount)
    print(table.columnCount)

    # meta data access:
    print(table.meta)
    print(table.meta["Foo"])

    # column access:
    print(table["Time"])
    print(table["Time"].data)
    print(table["Time"].unit)


def test_Column():
    v = TableDataset()
    assert v.getColumnCount() == 0
    v.addColumn("Energy", Column(
        data=[1, 2, 3, 4], description="desc", unit='eV'))
    assert v.getColumnCount() == 1
    # http://herschel.esac.esa.int/hcss-doc-15.0/load/hcss_drm/api/herschel/ia/dataset/TableDataset.html#Z:Z__setitem__-java.lang.String-herschel.ia.dataset.Column-


def test_CompositeDataset():
    # test equality
    a1 = [768, 4.4, 5.4E3]
    a2 = 'ev'
    a3 = 'arraydset 1'
    a4 = ArrayDataset(data=a1, unit=a2, description=a3)
    a5, a6, a7 = [[1.09, 289], [3455, 564]], 'count', 'arraydset 2'
    a8 = ArrayDataset(data=a5, unit=a6, description=a7)
    v = CompositeDataset()
    a9 = 'dataset 1'
    a10 = 'dataset 2'
    v.set(a9, a4)
    v.set(a10, a8)
    assert len(v.getDataWrappers()) == 2
    a11 = 'm1'
    a12 = NumericParameter(description='a different param in metadata',
                           value=2.3, unit='sec')
    v.meta[a11] = a12

    # equality
    b1 = copy.deepcopy(a1)
    b2 = ''.join(a2)
    b3 = ''.join(a3)
    b4 = ArrayDataset(data=b1, unit=b2, description=b3)
    b5, b6, b7 = copy.deepcopy(a5), ''.join(a6), ''.join(a7)
    b8 = ArrayDataset(data=b5, unit=b6, description=b7)
    v1 = CompositeDataset()
    b9 = ''.join(a9)
    b10 = ''.join(a10)
    v1.set(b9, b4)
    v1.set(b10, b8)
    assert len(v1.getDataWrappers()) == 2
    b11 = ''.join(a11)
    b12 = NumericParameter(description='a different param in metadata',
                           value=2.3, unit='sec')
    v1.meta[b11] = b12

    assert v == v1
    assert v1 == v

    # access datasets mapper
    sets = v1.getDataWrappers()
    assert len(sets) == 2
    assert id(sets[b9]) == id(v1[b9])

    # diff dataset access syntax []
    assert v1[b9].data[1] == v1[b9][1]
    v2 = CompositeDataset()
    v2[b9] = b4     # compare with v1.set(b9, b4)
    v2[b10] = b8
    v2.meta[b11] = b12
    assert v == v2

    # change data.
    v1[b9].data[1] += 0
    assert v == v1
    v1[b9].data[1] += 0.1
    assert v != v1
    assert v1 != v
    # change meta
    b4 = copy.deepcopy(a4)
    v1[b9] = b4
    assert v == v1
    v1.meta[b11].description = 'c'
    assert v != v1
    assert v1 != v

    # nested datasets
    v['v1'] = v1
    assert v['v1'][a9] == a4

    # toString()
    v3 = CompositeDataset()
    # creating a table dataset
    ELECTRON_VOLTS = 'eV'
    SECONDS = 'sec'
    t = [x * 1.0 for x in range(5)]
    e = [2 * x + 100 for x in t]
    x = TableDataset(description="Example table")
    x["Time"] = Column(data=t, unit=SECONDS)
    x["Energy"] = Column(data=e, unit=ELECTRON_VOLTS)
    # set a tabledataset ans an arraydset, with a parameter in metadata
    v3.set(a9, a4)
    v3.set(a10, x)
    v3.meta[a11] = a12
    ts = v3.toString()
    # print(ts)
    assert ts == out_CompositeDataset

    checkjson(v)
    checkgeneral(v)


def demo_CompositeDataset():
    """ http://herschel.esac.esa.int/hcss-doc-15.0/load/hcss_drm/ia/dataset/demo/CompositeDataset.py
    """
    # creating a composite dataset.For this demo, we use empty datasets only.
    c = CompositeDataset()
    c["MyArray"] = ArrayDataset()  # adding an array
    c["MyTable"] = TableDataset()  # adding a table
    c["MyComposite"] = CompositeDataset()  # adding a composite as child

    # alternative Java syntax:
    c.set("MyArray", ArrayDataset())
    c.set("MyTable", TableDataset())
    c.set("MyComposite", CompositeDataset())

    # adding two children to a "MyComposite":
    c["MyComposite"]["Child1"] = ArrayDataset()
    assert issubclass(c["MyComposite"]["Child1"].__class__, ArrayDataset)
    c["MyComposite"]["Child2"] = TableDataset()
    c["MyComposite"]["Child3"] = TableDataset()

    # replace array "Child1" by a composite:
    c["MyComposite"]["Child1"] = CompositeDataset()
    assert issubclass(c["MyComposite"]["Child1"].__class__, CompositeDataset)

    # remove3 table "Child3"
    assert c["MyComposite"].containsKey("Child3") == True
    c["MyComposite"].remove("Child3")
    assert c["MyComposite"].containsKey("Child3") == False

    # report the number of datasets in this composite
    print(c.size())
    assert c.size() == 3

    # print(information about this variable ...
    # <class 'spdc.dataset.dataset.CompositeDataset'>
    # {meta = "MetaData[]", _sets = ['MyArray', 'MyTable', 'MyComposite']}
    print(c.__class__)
    print(c)

    # ... print(information about child "MyComposite", and ...
    # <class 'spdc.dataset.dataset.CompositeDataset'>
    # {meta = "MetaData[]", _sets = ['Child1', 'Child2']}
    print(c["MyComposite"].__class__)
    print(c["MyComposite"])

    # ... that of a nested child ...
    # <class 'spdc.dataset.dataset.CompositeDataset'>
    # {meta = "MetaData[]", _sets = []}
    print(c["MyComposite"]["Child1"].__class__)
    print(c["MyComposite"]["Child1"])

    # ... or using java syntax to access Child1:
    # {meta = "MetaData[]", _sets = []}
    print(c.get("MyComposite").get("Child1"))

    # or alternatively:
    # <class 'spdc.dataset.dataset.CompositeDataset'>
    # {meta = "MetaData[]", _sets = ['Child1', 'Child2']}
    child = c["MyComposite"]
    print(child.__class__)
    print(child)


def test_FineTime():
    v = FineTime(datetime.datetime(
        2019, 2, 19, 1, 2, 3, 456789, tzinfo=utcobj))
    dt = v.toDate()
    # So that timezone won't show on the left below
    d = dt.replace(tzinfo=None)
    assert d.isoformat() + ' TAI' == '2019-02-19T01:02:03.456789 TAI'

    v2 = FineTime(datetime.datetime(
        2019, 2, 19, 1, 3, 4, 556789, tzinfo=utcobj))
    assert v != v2
    assert abs(v2.subtract(v) - 61100000) < 0.5
    checkjson(v)
    checkgeneral(v)


def test_FineTime1():
    v = FineTime1(datetime.datetime(
        2019, 2, 19, 1, 2, 3, 456789, tzinfo=utcobj))
    dt = v.toDate()
    # So that timezone won't show on the left below
    d = dt.replace(tzinfo=None)
    assert d.isoformat() + ' TAI' == '2019-02-19T01:02:03.456789 TAI'

    v2 = FineTime1(datetime.datetime(
        2019, 2, 19, 1, 3, 4, 556789, tzinfo=utcobj))
    assert v != v2
    assert abs(v2.subtract(v) - 61100000) < 0.5
    checkjson(v)
    checkgeneral(v)


def test_History():
    v = History()
    checkjson(v)
    checkgeneral(v)


def test_Product():
    """ """
    x = Product(description="This is my product example",
                instrument="MyFavourite", modelName="Flight")
    # print(x.__dict__)
    # print(x.meta.toString())
    assert x.meta['description'] == "This is my product example" \
        and x.instrument == "MyFavourite" and x.modelName == "Flight"
    # ways to add datasets
    i0 = 6
    i1 = [[1, 2, 3], [4, 5, i0], [7, 8, 9]]
    i2 = 'ev'                 # unit
    i3 = 'img1'  # description
    image = ArrayDataset(data=i1, unit=i2, description=i3)

    x["RawImage"] = image
    assert x["RawImage"].data[1][2] == i0
    # no unit or description. diff syntax same function as above
    x.set('QualityImage', ArrayDataset(
        [[0.1, 0.5, 0.7], [4e3, 6e7, 8], [-2, 0, 3.1]]))
    assert x["QualityImage"].unit is None
    # add a tabledataset
    s1 = [('col1', [1, 4.4, 5.4E3], 'eV'),
          ('col2', [0, 43.2, 2E3], 'cnt')
          ]
    spec = TableDataset(data=s1)
    x["Spectrum"] = spec
    assert x["Spectrum"].getValueAt(columnIndex=1, rowIndex=0) == 0

    # default
    assert Product('empty').getDefault() is None
    d = x.getDefault()
    sets = x.getDataWrappers()
    assert id(d) == id(sets['RawImage'])

    # Test metadata
    # mandatory properties are also in metadata
    x.creator = ""
    a0 = "Me, myself and I"
    x.creator = a0
    assert x.creator == a0
    assert x.meta["creator"] == a0

    x.meta["Version"] = 0
    p = Parameter(value="2.1a",
                  description="patched")
    x.meta["Version"] = p
    assert x.meta["Version"] == p
    a1 = 'a test NumericParameter, just b4 json'
    a2 = 1
    a3 = 'second'
    v = NumericParameter(description=a1, value=a2, unit=a3)
    x.meta['numPar'] = v

    # test comparison:
    p1 = Product(description="Description")
    p2 = Product(description="Description 2")
    assert p1.equals(p2) == False
    p3 = copy.deepcopy(p1)
    assert p1.equals(p3) == True

    # test mandatory properties that are also metadata
    x.creator = ""
    a0 = "Me, myself and I"
    x.creator = a0
    assert x.creator == a0
    assert x.meta["creator"] == a0
    a1 = "or else"
    x.meta["creator"] = a1
    assert x.meta["creator"] == a1
    assert x.creator == a1

    # toString
    ts = x.toString()
    # print(ts)

    checkjson(x)
    checkgeneral(x)


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

def running(t):
    print('running ' + str(t))
    t()


if __name__ == '__main__' and __package__ is None:

    if 0:
        from os import sys, path
        print(path.abspath(__file__))
        print(path.dirname(path.abspath(__file__)))
        print(path.dirname(path.dirname(path.abspath(__file__))))
        sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

        print("TableDataset demo")
        demo_TableDataset()

        print("CompositeDataset demo")
        demo_CompositeDataset()

    running(test_deepcmp)
    running(test_serialization)
    running(test_ndprint)
    running(test_Annotatable)
    running(test_Composite)
    running(test_AbstractComposite)
    running(test_Copyable)
    running(test_EventSender)
    running(test_Parameter)
    running(test_Quantifiable)
    running(test_NumericParameter)
    running(test_MetaData)
    running(test_Attributable)
    running(test_DataWrapper)
    running(test_ArrayDataset)
    running(test_TableModel)
    running(test_TableDataset)
    running(test_Column)
    running(test_CompositeDataset)
    running(test_FineTime1)
    running(test_History)
    running(test_Product)
