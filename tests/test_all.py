import datetime


from dataset.logdict import doLogging, logdict
if doLogging:
    import logging
    import logging.config
    # create logger
    logging.config.dictConfig(logdict)
    logger = logging.getLogger()
    logger.debug('%s logging level %d' %
                 (__name__, logger.getEffectiveLevel()))

from dataset.eq import Annotatable, Copyable, serializeClassID, SerializableEncoder, deepcmp
from dataset.listener import EventSender, DatasetBaseListener
from dataset.composite import Composite
from dataset.metadata import Parameter, Quantifiable, NumericParameter, MetaDataHolder, MetaData, Attributable, DataWrapper, AbstractComposite
from dataset.dataset import ArrayDataset, TableDataset, CompositeDataset
from dataset.product import FineTime1, History, Product
from dataset.deserialize import deserializeClassID


def checkjson(obj):
    """ seriaizes the given object and deserialize. check equality.
    """

    dbg = True if issubclass(obj.__class__, MetaData) or issubclass(
        obj.__class__, CompositeDataset) else False

    js = obj.serialized()
    if dbg:
        print('checkjsom ' + obj.__class__.__name__ + ' serialized: ' + js)
    des = deserializeClassID(js, debug=dbg)
    if dbg:
        print('checkjson des ' + str(des) + str(des.__class__))
        # js2 = json.dumps(des, cls=SerializableEncoder)
        # print('des     serialized: ' + js)

        r = deepcmp(obj, des)
        print('deepcmp ' + 'identical' if r is None else r)
        # print(' DIR \n' + str(dir(obj)) + '\n' + str(dir(des)))
    if issubclass(obj.__class__, Product):
        obj.meta.listeners = []
        des.meta.listeners = []
    assert obj == des


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


def test_AbstractComposite():

    a1 = 'this'
    a2 = 'that'
    v = AbstractComposite()
    v.set(a1, a2)
    assert v.get(a1) == a2
    a3 = 'more'
    v.set(name=a1, dataset=a3)
    assert v[a1] == a3

    v = AbstractComposite()
    v[a1] = a2  # DRM doc case
    assert v[a1] == a2

    # test for containsKey, isEmpty, keySet, size
    v = AbstractComposite()
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

    # test dict view
    a3 = 'k'
    a4 = 'focus'
    v[a3] = a4
    assert [k for k in v] == [a1, a3]
    assert [(k, v) for (k, v) in v.items()] == [(a1, a2), (a3, a4)]

    # test for a1=none pending
    v = AbstractComposite()
    v.set(a1, a2)
    assert v.remove(a1) == a2
    assert v.size() == 0


def test_Copyable():
    """ tests in a subprocess. """
    class Ctest(Copyable):
        def __init__(self, _p, **kwds):
            self.p = _p
            super().__init__(**kwds)

        def get(self):
            return self.p

    old = [[1, 1, 1], [2, 2, 2], [3, 3, 3]]
    v = Ctest(old)
    new = v.copy().get()
    old[1][1] = 'AA'
    assert new[1][1] == 2
    assert id(old) != id(new)


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
    assert v.getType() == a2.__class__.__name__

    # test equals
    b1 = ''.join(a1)  # make a new string copy
    b2 = a2 + 0  # make a copy
    v1 = Parameter(description=b1, value=b2)
    assert v.equals(v1)
    assert v == v1
    v1.value = -4
    assert not v.equals(v1)
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
    b2 = b'\xaa\x55'
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


def test_MetaDataHolder():
    v = MetaDataHolder()
    assert v.getMeta().size() == 0
    a1 = MetaData()
    a1['this'] = Parameter(0.3)
    v = MetaDataHolder(meta=a1)
    assert v.getMeta() == a1


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


def test_ArrayDataset():
    # from DRM
    a1 = [1, 4.4, 5.4E3]      # a 1D array of data
    a2 = 'ev'                 # unit
    a3 = 'three energy vals'  # description
    v = ArrayDataset(data=a1, unit=a2, description=a3)
    v1 = ArrayDataset(a1, a2, description=a3)  # simpler but error-prone
    assert v == v1

    # COPY
    c = v.copy()
    assert v == c
    assert c == v

    # test data and unit
    a3 = [34]
    a4 = 'm'
    a5 = 'new description'
    v.data = a3
    v.unit = a4
    assert v.data == a3
    assert v.unit == a4

    # test equality
    a1 = [1, 4.4, 5.4E3]
    a2 = 'ev'
    a3 = 'three energy vals'
    v = ArrayDataset(data=a1, unit=a2, description=a3)
    a4 = 'm1'
    a5 = NumericParameter(description='a param in metadata',
                          value=2.3, unit='sec')
    v.meta[a4] = a5

    b1 = [1, 4.4, 5.4E3]
    b2 = ''.join(a2)
    b3 = ''.join(a3)
    v1 = ArrayDataset(data=b1, unit=b2, description=b3)
    b4 = ''.join(a4)
    b5 = NumericParameter(description='a param in metadata',
                          value=2.3, unit='sec')
    v1.meta[b4] = b5
    assert v == v1
    assert v1 == v
    # change data
    v1.data += [6]
    assert v != v1
    assert v1 != v
    v1.data = a1.copy()
    # change description
    v1.description = 'changed'
    assert v != v1
    assert v1 != v
    v1.description = ''.join(a3)
    # change meta
    v1.meta[b4].description = 'c'
    assert v != v1
    assert v1 != v

    checkjson(v)


def test_TableDataset():
    a1 = [dict(name='col1', unit='keV', column=[1, 4.4, 5.4E3]),
          dict(name='col2', unit='cnt', column=[0, 43.2, 2E3])
          ]
    v = TableDataset(data=a1)
    assert v.getColumnName(0) == 'col1'
    assert v.getColumnCount() == 2
    assert v.getValueAt(rowIndex=1, columnIndex=1) == 43.2
    v.setValueAt(aValue=42, rowIndex=1, columnIndex=1)
    assert v.getValueAt(rowIndex=1, columnIndex=1) == 42


def test_CompositeDataset():
    # test equality
    a1 = [768, 4.4, 5.4E3]
    a2 = 'ev'
    a3 = 'arraydset 1'
    a4 = ArrayDataset(data=a1, unit=a2, description=a3)
    a5, a6, a7 = [[1.09, 289], [3455, 564]], 'count', 'arraydset 1'
    a8 = ArrayDataset(data=a5, unit=a6, description=a7)
    v = CompositeDataset()
    a9 = 'dataset 1'
    a10 = 'dataset 2'
    v.set(a9, a4)
    v.set(a10, a8)
    assert len(v.sets) == 2
    a11 = 'm1'
    a12 = NumericParameter(description='and different param in metadata',
                           value=2.3, unit='sec')
    v.meta[a11] = a12

    b1 = a1.copy()
    b2 = ''.join(a2)
    b3 = ''.join(a3)
    b4 = ArrayDataset(data=b1, unit=b2, description=b3)
    b5, b6, b7 = a5.copy(), ''.join(a6), ''.join(a7)
    b8 = ArrayDataset(data=b5, unit=b6, description=b7)
    v1 = CompositeDataset()
    b9 = ''.join(a9)
    b10 = ''.join(a10)
    v1.set(b9, b4)
    v1.set(b10, b8)
    assert len(v1.sets) == 2
    b11 = ''.join(a11)
    b12 = NumericParameter(description='and different param in metadata',
                           value=2.3, unit='sec')
    v1.meta[b11] = b12

    assert v == v1
    assert v1 == v

    # change data
    v1.sets[b9].data[1] += 0
    assert v == v1
    v1.sets[b9].data[1] += 0.1
    assert v != v1
    assert v1 != v
    b4 = a4.copy()
    v1.set(b9, b4)
    assert v == v1
    # change meta
    v1.meta[b11].description = 'c'
    assert v != v1
    assert v1 != v

    checkjson(v)


def test_FineTime1():
    v = FineTime1(datetime.datetime(2019, 2, 19, 1, 2, 3, 456789,
                                    tzinfo=datetime.timezone.utc))
    dt = v.toDate()
    # So that timezone won't show on the left below
    d = dt.replace(tzinfo=None)
    assert d.isoformat() + ' TAI' == '2019-02-19T01:02:03.456789 TAI'

    v2 = FineTime1(datetime.datetime(2019, 2, 19, 1, 3, 4, 556789,
                                     tzinfo=datetime.timezone.utc))
    assert v != v2
    assert v2.subtract(v) == 61100000
    checkjson(v)


def test_History():
    v = History()
    checkjson(v)


def test_Product():
    """ """
    x = Product(description="This is my product example",
                instrument="MyFavourite", modelName="Flight")
    assert x.meta['description'] == "This is my product example" \
        and x.instrument == "MyFavourite" and x.modelName == "Flight"
    # ways to add datasets
    i0 = 6
    i1 = [[1, 2, 3], [4, 5, i0], [7, 8, 9]]
    i2 = 'ev'                 # unit
    i3 = 'img1'  # description
    image = ArrayDataset(data=i1, unit=i2, description=i3)
    s1 = [dict(name='col1', unit='keV', column=[1, 4.4, 5.4E3]),
          dict(name='col2', unit='cnt', column=[0, 43.2, 2E3])
          ]
    spec = TableDataset(data=s1)
    x["RawImage"] = image
    assert x.sets["RawImage"].data[1][2] == i0
    # dummy. diff syntax same function as above
    x.set('QualityImage', 'aQualityImage')
    assert x["QualityImage"] == 'aQualityImage'
    x.sets["Spectrum"] = spec
    assert x["Spectrum"].getValueAt(columnIndex=1, rowIndex=0) == 0

    # Test metadata
    x.creator = ""
    a0 = "Me, myself and I"
    x.creator = a0
    assert x.creator == a0
    assert x.meta["creator"] == a0

    x.meta["Version"] = 0
    p = Parameter(value="2.1.1a",
                  description="patch taken from download")
    x.meta["Version"] = p
    assert x.meta["Version"] == p
    a1 = 'a test NumericParameter, just b4 json'
    a2 = 1
    a3 = 'second'
    v = NumericParameter(description=a1, value=a2, unit=a3)
    x.meta['numPar'] = v

    checkjson(x)

    # test comparison:
    p1 = Product(description="Description")
    p2 = Product(description="Description 2")
    assert p1.equals(p2) == False
    p3 = p1.copy()
    deepcmp(p1, p3)
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


# serializing using package jsonconversion

# from collections import OrderedDict
# import datetime

#from jsonconversion.encoder import JSONObjectEncoder, JSONObject
#from jsonconversion.decoder import JSONObjectDecoder


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
