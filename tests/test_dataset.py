# -*- coding: utf-8 -*-

import datetime
import fractions
import decimal
import traceback
from pprint import pprint
import copy
import sys
import threading
import functools
import time
import array
from math import sqrt
from datetime import timezone
import pytest

from fdi.dataset.annotatable import Annotatable
from fdi.dataset.copyable import Copyable
from fdi.dataset.odict import ODict
from fdi.dataset.eq import deepcmp
from fdi.dataset.classes import Classes
from fdi.dataset.deserialize import deserialize
from fdi.dataset.quantifiable import Quantifiable
from fdi.dataset.listener import EventSender, DatasetBaseListener, EventTypes, EventType, EventTypeOf
from fdi.dataset.messagequeue import MqttRelayListener, MqttRelaySender
from fdi.dataset.composite import Composite
from fdi.dataset.metadata import Parameter, MetaData, make_jsonable
from fdi.dataset.numericparameter import NumericParameter
from fdi.dataset.stringparameter import StringParameter
from fdi.dataset.dateparameter import DateParameter
from fdi.dataset.datatypes import DataTypes, DataTypeNames
from fdi.dataset.attributable import Attributable
from fdi.dataset.abstractcomposite import AbstractComposite
from fdi.dataset.datawrapper import DataWrapper, DataWrapperMapper
from fdi.dataset.arraydataset import ArrayDataset, Column
from fdi.dataset.tabledataset import TableDataset
from fdi.dataset.dataset import GenericDataset, CompositeDataset
from fdi.dataset.indexed import Indexed
from fdi.dataset.ndprint import ndprint
from fdi.dataset.datatypes import Vector, Vector2D, Quaternion
from fdi.dataset.invalid import INVALID
from fdi.dataset.finetime import FineTime, FineTime1
from fdi.dataset.history import History
from fdi.dataset.baseproduct import BaseProduct
from fdi.dataset.product import Product
from fdi.dataset.readonlydict import ReadOnlyDict
from fdi.dataset.testproducts import SP
from fdi.utils.checkjson import checkjson

# import __builtins__


if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
else:
    PY3 = False

Classes.updateMapping()

# make format output in /tmp/output.py
mk_output = 0

if __name__ == '__main__' and __package__ is None:
    # run by python3 tests/test_dataset.py

    from outputs import nds20, nds30, nds2, nds3, out_GenericDataset, out_ArrayDataset, out_TableDataset, out_CompositeDataset, out_FineTime
else:
    # run by pytest

    # This is to be able to test w/ or w/o installing the package
    # https://docs.python-guide.org/writing/structure/
    from pycontext import fdi

    from outputs import nds20, nds30, nds2, nds3, out_GenericDataset, out_ArrayDataset, out_TableDataset, out_CompositeDataset, out_FineTime

    import logging
    import logging.config
    # create logger
    if 1:
        from logdict import logdict
        logging.config.dictConfig(logdict)
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(name)8s %(process)d %(threadName)s %(levelname)s %(funcName)10s() %(lineno)3d- %(message)s')

    logger = logging.getLogger()
    logger.debug('logging level %d' % (logger.getEffectiveLevel()))
    # logging.getLogger().setLevel(logging.DEBUG)


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
    v = Ellipsis
    checkjson(v)
    v = b'\xde\xad\xbe\xef'
    checkjson(v)
    v = array.array('d', [1.2, 42])
    checkjson(v)
    v = [1.2, 'ww']
    checkjson(v)
    v = Product
    checkjson(v)
    # v = (1, 8.2, 'tt')
    # checkjson(v)
    # v = {(5, 4): 4, 'y': {('d', 60): 'ff', '%': '$'}}
    # with testpy.raises(TypeError):
    #     checkjson(v)

    # https://github.com/mverleg/pyjson_tricks
    # json_tricks/test_class.py
    class MyTestCls:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    v = [
        # arange(0, 10, 1, dtype=int).reshape((2, 5)),
        datetime.datetime(year=2017, month=1, day=19,
                          hour=23, minute=00, second=00),
        1 + 2j,
        decimal.Decimal(42),
        fractions.Fraction(1, 3),
        MyTestCls(s='ub', dct={'7': 7}),  # see later
        set(range(7)),
    ]
    # checkjson(v)


def test_sys():
    assert sys.int_info.bits_per_digit == 30
    assert sys.int_info.sizeof_digit == 4
    assert sys.float_info.dig == 15
    assert sys.maxsize == 2**63 - 1
    assert sys.hash_info.width == 64


def est_TupleKeys():
    a1 = ('1', '2')
    a2 = (3.333, 7)
    a3 = [a1, a2]
    v = ODict(a3)
    assert v[a1[0]] == a1[1]
    v = ODict([(a1, a2)])
    assert v[a1] == a2
    assert v.listoflists == [[['1', '2'], a2]]
    v1 = ODict()
    v1.listoflists = [[['1', '2'], a2]]
    assert v1 == v
    checkjson(v)


def ndlist(*args, atype=list):
    """ Generates an N-dimensional array with list or an array-type.

    atype: a sequence that can be initialized with a list of atype.
    ``ndlist(2, 3, 4, 5)`` will make a list of 2 lists of 3 lists of 4 lists of 5 elements of 0.
    https://stackoverflow.com/a/33460217
    """
    dp = 0
    for x in reversed(args):
        dp = atype([copy.deepcopy(dp) for i in range(x)])
    return dp


def test_ndprint():
    s = 42
    v = ndprint(s)
    # print(v)
    assert v == '42'
    s = [1, 2, 3]
    v = ndprint(s, headers=[], tablefmt3='plain')
    # print(v)
    # table, 1 column
    assert v == '1\n2\n3'
    v = ndprint(s, trans=False, headers=[], tablefmt3='plain')
    # print(v)
    # 1D matrix. 1 row.
    assert v == '1  2  3'
    s = [[i + j for i in range(2)] for j in range(3)]
    v = ndprint(s, headers=[], tablefmt2='plain')
    # print(v)
    # 2x3 matrix 3 columns 2 rows
    assert v == '0  1  2\n1  2  3\n\n'
    v = ndprint(s, trans=False, headers=[], tablefmt2='plain')
    # print(v)
    # 2x3 table view 2 columns 3 rows
    assert v == '0  1\n1  2\n2  3\n\n'

    s = ndlist(2, 3, 4, 5)
    s[0][1][0] = [0, 0, 0, 0, 0]
    s[0][1][1] = [0, 0, 0, 1, 0]
    s[0][1][2] = [5, 4, 3, 2, 1]
    s[0][1][3] = [0, 0, 0, 3, 0]
    v = ndprint(s, trans=False, headers=[], tablefmt2='plain')
    if mk_output:
        print(v)
        # print(nds2)
    else:
        assert v == nds2
    v = ndprint(s, headers=[], tablefmt2='plain')
    if mk_output:
        print(v)
    else:
        assert v == nds3
        # pprint.pprint(s)


def test_ODict():
    v = ODict()
    assert len(v.data) == 0


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
    assert issubclass(sets.__class__, ODict)

    # dict view
    a3 = 'k'
    a4 = 'focus'
    v[a3] = a4
    assert [k for k in v] == [a1, a3]
    assert [(k, v) for (k, v) in v.items()] == [(a1, a2), (a3, a4)]
    assert list(v.values()) == [a2, a4]

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


def test_EventType():
    # print(EventTypeOf)
    assert 'UNKNOWN_ATTRIBUTE_CHANGED' in EventTypes
    assert EventType.UNKNOWN_ATTRIBUTE_CHANGED == 'UNKNOWN_ATTRIBUTE_CHANGED'
    assert EventTypeOf['CHANGED']['UNKNOWN_ATTRIBUTE'] == 'UNKNOWN_ATTRIBUTE_CHANGED'


test123 = 0


@pytest.fixture()
def mocksndrlsnr():
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

    return MockFileWatcher, MockFileWatcher2, l1, l2


def test_EventSender(mocksndrlsnr):

    global test123
    MockFileWatcher, MockFileWatcher2, l1, l2 = mocksndrlsnr
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


def test_MqttRelay_mqtt(mocksndrlsnr):

    global test123
    MockFileWatcher, MockFileWatcher2, l1, l2 = mocksndrlsnr

    # MQ Relay
    v = MqttRelayListener(topics="test.mq.bounce2", host=None,
                          port=None, username=None, passwd=None,
                          client_id=None, callback=None, qos=1,
                          userdata=None, clean_session=None,)
    mf = MockFileWatcher()
    mf.addListener(v)
    w = MqttRelaySender(topics="test.mq.bounce2", host=None,
                        port=None, username=None, passwd=None,
                        client_id=None, callback=None, qos=1,
                        userdata=None, clean_session=None,)
    w.addListener(l1)
    w.last_msg = ''
    test123 = ''

    def snd():
        # send source_path
        mf.watchFiles()

    def rcv():
        t0 = time.time()
        while w.last_msg == '' and (time.time()-t0 < 3):
            time.sleep(0.2)
    t1 = threading.Thread(target=snd)
    t2 = threading.Thread(target=rcv)
    t1.start()
    t2.start()
    t2.join()
    t1.join()
    assert not t1.is_alive()
    assert not t2.is_alive()
    assert test123 == "['foo'] changed."
    assert w.last_msg == ['foo']


def test_datatypes():
    # constructor
    v = Vector()
    assert len(v) == 3
    assert v.getComponents() == [0, 0, 0]
    v = Vector([1, 2.3, 4.5])
    assert v.getComponents() == [1, 2.3, 4.5]
    checkjson(v)

    v = Vector2D()
    assert len(v) == 2
    assert v.getComponents() == [0, 0]
    v = Vector([1, 2.3])
    assert v.getComponents() == [1, 2.3]
    # comparison
    assert v > sqrt(1+2.3**2) - 1
    assert v < sqrt(1+2.3**2) + 1

    # assignment
    v.components = [0xaa, 1, 1e2]
    assert v.components == [0xaa, 1, 1e2]
    h = hash(v)
    checkjson(v)

    # Quaternion
    v = Quaternion([-1, 1, 2.3, 4.5])
    assert v.getComponents() == [-1, 1, 2.3, 4.5]
    # equal
    a1 = -1
    v2 = Quaternion([a1, 1+0, 1-a1+0.3, 4.5])
    assert v == v2
    h = hash(v)
    checkjson(v)


def test_Parameter_init():
    # python  keeps an array of integer objects for all integers
    # between -5 and 256 so do not use small int for testing
    # because one cannot make a copy

    # Creation

    # test constructor
    # standard: with keyword arguments
    a1 = 'a test parameter'
    a2 = 300
    a3 = 'integer'
    a4 = 9288
    a5 = ''
    v = Parameter(description=a1, value=a2, typ_=a3, default=a4, valid=a5)
    assert v.description == a1
    assert v.value == a2
    assert v.type == a3
    assert v.default == a4
    assert v.valid is None  # not ''

    # if value is None v.value is set to default
    v = Parameter(description=a1, value=None, typ_=a3, default=a4, valid=a5)
    assert v.value == v.default

    # with no argument
    v = Parameter()
    assert v.description == 'UNKNOWN'  # inherited from Anotatable
    assert v.value == v.default
    assert v.type == ''
    assert v.default is None
    assert v.valid is None

    # make a blank one then set attributes
    v = Parameter(description=a1)
    v.description = a1
    v.value = a2
    v.type = a3
    v.default = a4
    v.valid = a5
    assert v.description == a1
    assert v.value == a2
    assert v.type == a3
    assert v.default == a4
    assert v.valid is None  # not ''

    # other ways to make parameters
    # 1
    a2 = FineTime1(8765)
    v = Parameter(a2)  # description has a default so a2 -> 'value'
    assert v.description == 'UNKNOWN'  # inherited from Anotatable
    assert v.value == a2
    assert v.type == 'finetime1'  # automatically set to value's
    assert v.default is None
    assert v.valid is None
    # incompatible type
    a2 = DataWrapper()
    with pytest.raises(TypeError):
        v = Parameter(a2)
    # also only one positional argument, but with a keyword arg
    a1 = 'a test parameter'
    a2 = FineTime1(8765)
    v = Parameter(a2, description=a1)
    assert v.value == a2
    assert v.description == a1
    assert v.type == 'finetime1'
    # 2
    a1 = 'a test parameter'
    a2 = 'bar'
    a3 = 'foo'
    v = Parameter(a2, a3)  # two string type positional arguments
    assert v.value == a2
    assert v.description == a3
    assert v.type == 'string'
    # 3
    a1 = 'a test parameter'
    a2 = 3.3
    a4 = 'float'
    v = Parameter(a2, a1, a4)
    assert v.description == a1
    assert v.value == a2
    assert v.type == a4
    assert type(v.value).__name__ == DataTypes[a4]


def test_Parameter_valid():
    a1 = 'a test parameter'
    a2 = 300
    a3 = 'integer'
    a4 = 9288
    # empty valid causes valid to be set to None
    a5 = None
    v = Parameter(description=a1, value=a2, typ_=a3, default=a4, valid=a5)
    assert v.valid == None
    a5 = ''
    v = Parameter(description=a1, value=a2, typ_=a3, default=a4, valid=a5)
    assert v.valid == None
    a5 = {}
    v = Parameter(description=a1, value=a2, typ_=a3, default=a4, valid=a5)
    assert v.valid == None
    a5 = {(1, 22222): 'a'}
    v = Parameter(description=a1, value=a2, typ_=a3, default=a4, valid=a5)
    assert v.valid == [[[1, 22222], 'a']]
    # ranges
    a2 = 300
    a3 = 'integer'
    # set two ranges
    a5 = {(1, 2222): 'a', (3000, 3333): 'b'}
    v = Parameter(description=a1, value=a2, typ_=a3, default=a4, valid=a5)
    assert v.validate(a2) == (a2, 'a')
    assert v.isValid()
    # a different range, low edge
    assert v.validate(3000) == (3000, 'b')
    # high edge
    assert v.validate(3333) == (3333, 'b')
    # invalid
    assert v.validate(0) == (INVALID, 'Invalid')
    v.value = 0
    assert v.isValid() == False
    assert v.validate(2500) == (INVALID, 'Invalid')
    v.value = 2500
    assert not v.isValid()
    # discrete
    v.valid = {4321: 'hi there', 99: 'foo'}
    assert v.validate(4321) == (4321, 'hi there')
    assert v.validate(99) == (99, 'foo')
    assert v.validate(2500) == (INVALID, 'Invalid')
    # wrong type
    assert v.validate(2500.) == (INVALID, 'Type float')

    # binary masked
    v.valid = {
        (0b00110000, 0b00): 'off',
        (0b00110000, 0b01): 'mode 1',
        (0b00110000, 0b10): 'mode 2',
        # 0b00110000, 0b11): 'mode 3', undefined. invalid
        (0b00001111, 0b0000): 'reserved',
    }
    assert v.validate(0b00000000) == [(0b00, 'off', 6, 2),
                                      (0b0000, 'reserved', 4, 4)]
    v.value = 0
    assert v.isValid()
    assert v.validate(0b00010000) == [(0b01, 'mode 1', 6, 2),
                                      (0b0000, 'reserved', 4, 4)]
    # other bits are ignored
    assert v.validate(0b10100000) == [(0b10, 'mode 2', 6, 2),
                                      (0b0000, 'reserved', 4, 4)]
    assert v.validate(0b00110000) == [(INVALID, 'Invalid'),
                                      (0b0000, 'reserved', 4, 4)]
    assert v.validate(0b00001111) == [(0b00, 'off', 6, 2),
                                      (INVALID, 'Invalid')]
    # all invalid. [ (INVALID, 'Invalid'),
    #                                   (INVALID, 'Invalid') ]
    assert v.validate(0b11111111) == (INVALID, 'Invalid')

    # split
    v.value = 0b100110
    assert v.split() == {'0b110000': 0b10, '0b001111': 0b0110}
    assert v.split({0b110000: 'foo', 0b001111: 'bar'}) == {
        'foo': 0b10, 'bar': 0b0110}

    # display
    v = StringParameter('Right', 'str parameter. but only "" is allowed.',
                        valid={'': 'empty'}, default='cliche', typecode='B')
    assert v.validate() == (INVALID, 'Invalid')
    assert v.validate('') == ('', 'empty')
    assert v.toString(alist=True)[0] == 'Invalid (Right)'


def test_Parameter_features():
    # test equivalence of v.setXxxx(a) and v.xxx = a
    a1 = 'distance to earth'
    a2 = 98.33
    v = Parameter()
    v.description = a1
    v.value = a2
    v1 = Parameter()
    v1.setDescription(a1)
    v1.setValue(a2)
    assert v.description == v1.description
    assert v.value == v1.value

    # handle type diff
    a2 = 0B1011  # 11 in binary
    a4 = 'float'
    if 0:  # strict
        # exception if value and type are  different
        with pytest.raises(TypeError):
            v = Parameter(a2, a1, a4)
    else:  # smart
        # not recommendedxs
        v = Parameter(a2, a1, a4)
        # v = Parameter(typ_=a4)
        # v.value = a2
        assert type(v.value) == float
        assert v.value == 11
    a2 = 9.7
    a4 = 'hex'  # hex is internally int
    if 0:  # strict
        with pytest.raises(TypeError):
            v = Parameter(a2, a1, a4)
    else:  # smart
        v = Parameter(a2, a1, a4)
        assert v.value == 9
    # with known types this is ok
    a2 = [2.2, 3.3, 1.1, 0]
    a4 = 'quaternion'
    v = Parameter(a2, a1, a4)
    assert v.value == [2.2, 3.3, 1.1, 0]
    assert issubclass(v.value.__class__, list)
    v = NumericParameter(typ_='vector')
    v.value = [1, 2, 3]
    assert v.value == Vector([1, 2, 3])
    # ok for NumericParameter w/o explicite type
    v = NumericParameter()
    # with pytest.raises(TypeError):
    v.value = [9, 4, 1]

    # type not Number nor in DataTypes gets NotImplementedError
    a2 = 9
    a4 = 'guess'
    with pytest.raises(NotImplementedError):
        v = Parameter(a2, a1, a4)
    # value type not Number nor in DataTypes gets TypeError
    a2 = []
    a4 = 'integer'
    with pytest.raises(TypeError):
        v = Parameter(a2, a1, a4)

    # NotImplemented
    # arbitrary argument order here
    a1 = 'a test parameter'
    a2 = 0x3e
    v = Parameter(description=a1, value=a2)
    assert v.description == a1
    assert v.value == a2

    # getType
    assert v.getValue() == a2
    assert v.getType() == 'integer'  # NOT hex!!

    # test equals
    b1 = ''.join(a1)  # make a new string copy
    b2 = a2 + 0  # make a copy
    v1 = Parameter(description=b1, value=b2)

    # CHANNGED parameter equality behavior
    assert v.equals(v1)
    assert v.__eq__(v1)
    assert v.__eq__ == v1.__eq__
    assert v == v1
    v1.value = -4

    assert not v.equals(v1),   deepcmp(v, v1, verbose=True)
    assert v != v1
    b2 = a2 + 0  # make a copy
    v1.value = b2  # change it back
    v1.description = 'changed'
    if 0:
        assert not v.equals(v1)
        assert v != v1
    else:
        assert v.equals(v1)
        assert v == v1

    # comparison with simplified syntax w/o '.value'
    x = 4
    for t in [int, float, str, FineTime]:
        p = Parameter(value=t(x))
        assert p == t(x)
        assert p <= t(x)
        assert p >= t(x)
        assert p != t(x+1)
        assert p < t(x+1)
        assert p != t(x-1)
        assert p > t(x-1)
        # assert t(x) == p
        # assert t(x) >= p
        # assert t(x+1) > p

    # toString hex

    # serializing
    a1 = 'a test parameter'
    a2 = 300
    a3 = 'integer'
    a4 = 928
    a5 = {(3, 3000): 'kk'}
    v = Parameter(description=a1, value=a2, typ_=a3, default=a4, valid=a5)
    checkjson(v)
    b1 = 'a binary par'
    b2 = 6  # b'\xaa\x55'
    v = Parameter(description=b1)
    v.value = b2
    checkjson(v)

    a2 = [2.2, 3.3, 1.1, 0]
    a4 = 'quaternion'
    v = Parameter(a2, 'foo', a4)
    # serializing special types will fail
    # with pytest.raises(TypeError):
    checkjson(v)
    v = Parameter()
    v.type = a4
    v.value = a2

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
    b = 'I'
    v = Quantifiable(a, b)
    assert v.unit == a
    assert v.getUnit() == a
    assert v.typecode == b
    assert v.getTypecode() == b
    v = Quantifiable()
    v.setUnit(a)
    assert v.unit == a
    v.typecode = b
    assert v.getTypecode() == b


def test_NumericParameter():
    v = NumericParameter()
    assert v.description == 'UNKNOWN'
    assert v.value is None
    assert v.unit is None
    assert v.type == ''
    assert v.default is None
    assert v.valid is None
    assert v.typecode is None

    a1 = 'a test NumericParameter'
    a2 = 100.234
    a3 = 'second'
    a4 = 'float'
    a5 = 0
    a6 = ''
    a7 = 'f'
    v = NumericParameter(description=a1, value=a2, unit=a3,
                         typ_=a4, default=a5, valid=a6, typecode=a7)
    assert v.description == a1
    assert v.value == a2
    assert v.unit == a3
    assert v.type == a4
    assert v.default == a5
    assert v.valid is None
    assert v.typecode == a7

    checkjson(v)

    # arg position
    a1 = 'a test parameter'
    a2 = 3.3
    a4 = 'float'
    v = Parameter(a2, a1, a4)
    assert v.description == a1
    assert v.value == a2
    assert v.type == a4
    assert type(v.value).__name__ == DataTypes[a4]

    # type casting
    a8 = 4
    v.value = a8
    assert type(v.value).__name__ == DataTypeNames[v.type]
    # equality
    a1 = 'a test parameter'
    a2 = 3.3
    a3 = 'float'
    a4 = 'm'
    a5 = None
    a6 = None
    a7 = 'd'
    v = NumericParameter(a2, a1, a3, unit=a4, default=a5,
                         valid=a6, typecode=a7)
    a3 = ''.join(a3)  # same contents
    v1 = NumericParameter(description=a1, value=a2,
                          typ_=a3, unit=a4, typecode=a7)
    assert v == v1
    assert v1 == v
    v1.typecode = 'f'
    assert v != v1
    assert v1 != v

    checkgeneral(v)


def test_NumericParameter():
    v = NumericParameter()
    assert v.description == 'UNKNOWN'
    assert v.value is None
    assert v.unit is None
    assert v.type == ''
    assert v.default is None
    assert v.valid is None
    assert v.typecode is None
    h = v.hash()

    a1 = 'a test NumericParameter'
    a2 = 100.234
    a3 = 'second'
    a4 = 'float'
    a5 = 0
    a6 = ''
    a7 = 'f'
    v = NumericParameter(description=a1, value=a2, unit=a3,
                         typ_=a4, default=a5, valid=a6, typecode=a7)
    assert v.description == a1
    assert v.value == a2
    assert v.unit == a3
    assert v.type == a4
    assert v.default == a5
    assert v.valid is None
    assert v.typecode == a7

    checkjson(v)


def test_DateParameter():

    v = DateParameter()
    assert v.description == 'UNKNOWN'
    assert v.value == v.default
    assert v.type == 'finetime'
    def0 = FineTime(0)
    assert v.default == def0
    assert v.valid is None
    assert v.typecode == 'Q'
    assert v.value.format == FineTime.DEFAULT_FORMAT

    a1 = 'a test DateParameter'
    a2 = 765
    a5 = 9
    a6 = ''
    a7 = '%f'
    v = DateParameter(description=a1, value=a2,
                      default=a5, valid=a6)
    assert v.description == a1
    assert v.value == FineTime(a2)
    assert v.type == 'finetime'
    assert v.default == FineTime(a5)
    assert v.valid is None
    # if value and typecode are both given, typecode will be overwritten by value.format.
    assert FineTime.DEFAULT_FORMAT == v.value.format

    a8 = 9876
    v.value = a8
    assert v.value == FineTime(a8)

    v = DateParameter('2019-02-19T01:02:03.457')
    assert v.value.tai == 1929229360457000
    v.value.format = '%Y'
    print('********', v.value.isoutc(), ' ** ', v, '*******', v.toString(1))

    with pytest.raises(TypeError):
        DateParameter(3.3)
    vv = copy.copy(v)
    checkjson(v)


def test_StringParameter():

    v = StringParameter()
    assert v.description == 'UNKNOWN'
    assert v.value == v.default
    assert v.type == 'string'
    assert v.default == ''
    assert v.valid is None
    assert v.typecode == 'B'

    a1 = 'a test StringcParameter'
    a2 = 'eeeee'
    a3 = 'second'
    a4 = 'string'
    a5 = ''
    a6 = '9B'
    v = StringParameter(description=a1, value=a2, default=a3,
                        valid=a5, typecode=a6)
    assert v.description == a1
    assert v.value == a2
    assert v.default == a3
    assert v.valid is None
    assert v.typecode == a6

    checkjson(v)

    a2 = '1'
    v = StringParameter(description=a1, value=a2, default=a3,
                        valid=a5, typecode=a6)
    assert v.description == a1
    assert v.value == a2
    checkjson(v)


def test_MetaData():
    # creation
    a1 = 'age'
    a2 = NumericParameter(description='since 2000',
                          value=20, unit='year', typ_='integer')
    v = MetaData()
    v.set(a1, a2)
    assert v.get(a1) == a2
    # add more parameter
    a3 = 'Bob'
    v.set(name='name', newParameter=Parameter(a3))
    assert v.get('name').value == a3

    # access parameters in metadata
    v = MetaData()
    # a more readable way to set a parameter
    v[a1] = a2  # DRM doc case
    # a more readable way to get a parameter
    assert v[a1] == a2
    assert v.get(a1) == a2
    v['time'] = NumericParameter(description='another param',
                                 value=2.3, unit='sec')
    v['birthday'] = Parameter(description='was made on',
                              value=FineTime('2020-09-09T12:34:56.789098'))
    # names of all parameters
    assert [n for n in v] == [a1, 'time', 'birthday']

    h = v.hash()
    checkjson(v, dbg=0)

    v.remove(a1)  # inherited from composite
    assert v.size() == 2

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
    v1['foo'] = Parameter('bar')
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
    a4 = 'i'
    v = DataWrapper(description=a3)
    assert v.hasData() == False
    v.setData(a1)
    v.setUnit(a2)
    v.setTypecode(a4)
    assert v.hasData() == True
    assert v.data == a1
    assert v.unit == a2
    assert v.description == a3
    assert v.typecode == a4

    v = DataWrapper(data=a1, unit=a2, description=a3, typecode=a4)
    assert v.hasData() == True
    assert v.data == a1
    assert v.unit == a2
    assert v.description == a3
    assert v.typecode == a4

    checkgeneral(v)


def standardtestmeta():
    m = MetaData()
    m['a'] = NumericParameter(
        value=3.4, description='rule name, if is "valid", "", or "default", is ommited in value string.',
        typ_='float',
        default=2.,
        valid={(0, 31): 'valid', 99: ''})
    then = datetime.datetime(
        2019, 2, 19, 1, 2, 3, 456789, tzinfo=timezone.utc)
    m['b'] = DateParameter(value=FineTime(then), description='date param',
                           default=99,
                           valid={(0, 9876543210123456): 'xy'})
    m['c'] = StringParameter(
        value='IJK', description='this is a string parameter. but only "" is allowed.',
        valid={'': 'empty'},
        default='cliche',
        typecode='B')
    m['d'] = NumericParameter(
        value=0b01, description='valid rules described with binary masks',
        typ_='binary',
        default=0b00,
        valid={(0b011000, 0b01): 'on', (0b011000, 0b00): 'off'},
        typecode='H')
    return m


def test_GenericDataset():
    v = GenericDataset(description='test GD')
    v.data = 88.8
    v.meta = standardtestmeta()
    ts = 'level 0\n'
    ts += v.toString()
    ts += 'level 1, repr\n'
    ts += v.toString(1)
    ts += 'level 2,\n'
    ts += v.toString(2)
    if mk_output:
        print(ts)
        with open('/tmp/output.py', 'wt') as f:
            clsn = 'out_GenericDataset'
            f.write('%s = """%s"""\n' % (clsn, ts))
    else:
        assert ts == out_GenericDataset


class fa(array.array):
    def __init__(self, *args, **kwds):

        super().__init__('f', *args, **kwds)


def do_ArrayDataset_init(atype):
    # defaults
    v = ArrayDataset()
    assert v.data is None
    assert v.unit is None
    assert v.description == 'UNKNOWN'
    assert v.shape == ()
    assert v.typecode == 'UNKNOWN'
    # from DRM
    a1 = atype([1, 4.4, 5.4E3])      # an array of data
    a2 = 'ev'                 # unit
    a3 = 'three energy vals'  # description
    a4 = 'float'              # type
    a6 = 'f'                  # typecode
    a7 = (8, 9)
    v = ArrayDataset(data=a1, unit=a2, description=a3,
                     typ_=a4, shape=a7, typecode=a6)
    assert v.data == a1
    assert v.unit == a2
    assert v.description == a3
    assert v.typecode == a6
    assert v.shape == a7
    v = ArrayDataset(data=a1)
    assert v.data == a1
    assert v.unit is None
    assert v.description == 'UNKNOWN'
    assert v.typecode == 'UNKNOWN'
    assert v.shape == ()

    # omit the parameter names when instantiating, the orders are data, unit, description
    v2 = ArrayDataset(a1)
    assert v2.data == a1
    v2 = ArrayDataset(a1, a2)
    assert v2.data == a1
    assert v2.unit == a2
    v2 = ArrayDataset(a1, a2, a3)
    assert v2.data == a1
    assert v2.unit == a2
    assert v2.description == a3


def check_MDP(x):
    for n, p in standardtestmeta().items():
        x.meta[n] = p
    # when ``alwaysMeta`` is set, a Parameeter type attrbute becomes a Parameeter
    assert x.alwaysMeta
    x.added_parameter = NumericParameter(42, description='A non-builtin param')
    assert x.meta['added_parameter'].value == 42
    assert issubclass(x.meta['added_parameter'].__class__, NumericParameter)
    # wont work if not a Parameeter type
    x.added_attribute = 111
    assert 'added_attribute' not in x.meta
    assert issubclass(x.added_attribute.__class__, int)


def do_ArrayDataset_func(atype):

    # test data and unit
    a1 = atype([1, 4.4, 5.4E3])      # an array of data
    a2 = 'ev'                 # unit
    a3 = atype([34, 9999])
    a4 = 'm'
    a5 = 'new description'
    v = ArrayDataset(data=a1)
    assert v.data == a1
    assert v.unit is None
    v.data = a3
    v.unit = a4
    assert v.data == a3
    assert v.unit == a4
    assert v.data[1] == 9999

    # test equality
    a1 = atype([1, 4.4, 5.4E3])
    a2 = 'ev'
    a3 = 'three energy vals'
    a6 = None
    v = ArrayDataset(data=a1, unit=a2, description=a3, typecode=a6)
    a4 = 'm1'
    a5 = NumericParameter(description='a param in metadata',
                          value=2.3, unit='sec')
    v.meta[a4] = a5

    # b[1-5] and v1 have the  same contents as a[1-5] and v
    b1 = atype([1, 4.4, 5.4E3])
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
    v1.data += atype([6])
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
    # v and v1 are not the same, really
    assert id(v) != id(v1)
    # change meta
    v1.meta[b4].value = 999
    assert v != v1
    assert v1 != v

    # COPY
    c = v.copy()
    assert v == c
    assert c == v

    # data access
    d = atype([1, 2, 3, 4, 5, 6])
    x = ArrayDataset(data=d)
    assert x.data[5] == 6
    # slice [2:4] is [3,4]
    y = x[2:4]
    assert y[0] == 3
    # removal
    r0 = x[2]
    x.remove(r0)
    assert x[4] == 6  # x=[1,2,4,5,6]
    r0 = x[0]
    assert r0 == x.pop(0)
    assert x[0] == 2

    # iteration
    i = atype([])
    for m in v:
        i.append(m)
    assert i == a1

    try:
        d = atype([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    except TypeError:
        d = atype([2.3, 4e3, -9.9])
        x = ArrayDataset(data=d)
        for n, p in standardtestmeta().items():
            x.meta[n] = p
        ts = x.toString()
        # print(atype, ts)

        checkjson(x)
        checkgeneral(x)
        return

    # high dimension data access
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

    # toString()
    d = atype([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    x = ArrayDataset(data=d)
    for n, p in standardtestmeta().items():
        x.meta[n] = p
    ts = x.toString()
    # print(ts)
    s = ndlist(2, 3, 4, 5)
    x = ArrayDataset(data=s, description='toString tester AD', unit='lyr')
    x[0][1][0] = atype([0, 0, 0, 0, 0])
    x[0][1][1] = atype([0, 0, 0, 1, 0])
    x[0][1][2] = atype([5, 4, 3, 2, 1])
    x[0][1][3] = atype([0, 0, 0, 3, 0])

    check_MDP(x)
    ts = '\n\nlevel 0\n'
    ts += x.toString()
    i = ts.index('0  0  0')
    if mk_output:
        print(ts[i:])
    else:
        assert ts[i:] == nds2 + '\n'
    ts += '\n\nlevel 1\n'
    ts += x.toString(1)
    ts += '\n\nlevel 2, repr\n'
    ts += x.toString(2)
    ts += '\n\n'
    ts += 'an empty meta and long data level 2: \n'
    ts += ArrayDataset(data=[8]*8).toString(level=2)
    ts += '\n\n'
    if mk_output:
        print(ts)
        with open('/tmp/output.py', 'a') as f:
            clsn = 'out_ArrayDataset'
            f.write('%s = """%s"""\n' % (clsn, ts))
    else:
        assert ts == out_ArrayDataset

    h = hash(v)

    checkjson(x)
    checkgeneral(x)


def test_ArrayDataset_init():
    atype = list

    do_ArrayDataset_init(atype)


def test_ArrayDataset_func():
    atype = list
    do_ArrayDataset_func(atype)


def test_ArrayDataset_array_init():
    atype = functools.partial(array.array, 'f')
    do_ArrayDataset_init(atype)


def test_ArrayDataset_array_func():
    atype = functools.partial(array.array, 'f')
    do_ArrayDataset_func(atype)


def test_Column():
    v = Column()
    assert v.type == 'Column'
    v = Column(data=[4, 9], unit='m')
    assert v.data == [4, 9]
    s = v.hash()

    checkjson(v)


def test_TableModel():
    pass


def test_TableDataset_init():
    # constructor
    # if data is not in a required form an exception is thrown
    with pytest.raises(TypeError):
        t = 5
        t = TableDataset(data=42)

    if 1:
        with pytest.raises(DeprecationWarning):
            t = TableDataset(data=[{'name': 'a', 'column': Column(data=[])}])

        # setData format 1: data is a  mapping. Needs pytnon 3.6 to guarantee order
        a1 = {'col1': Column(data=[1, 4.4, 5.4E3], unit='eV'),
              'col2': Column(data=[0, 43.2, 2E3], unit='cnt')}

        v = TableDataset(data=a1)  # inherited from DataContaier
        assert v.getColumnCount() == len(a1)
        assert v.getColumnName(0) == 'col1'
        t = a1['col2'].data[1]  # 43.2
        assert v.getValueAt(rowIndex=1, columnIndex=1) == t

    # 2: add columns one by one
    v2 = TableDataset()
    v2['col1'] = Column(data=[1, 4.4, 5.4E3], unit='eV')
    v2['col2'] = Column(data=[0, 43.2, 2E3], unit='cnt')

    assert v2 == v

    # 3: another syntax, list of tuples that does not need to use Column
    v3 = TableDataset(data=[('col1', [1, 4.4, 5.4E3], 'eV'),
                            ('col2', [0, 43.2, 2E3], 'cnt')
                            ])
    assert v == v3, deepcmp(v, v3)

    # 4: quick and dirty. data are list of lists without names or units
    a5 = [[1, 4.4, 5.4E3], [0, 43.2, 2E3]]
    v5 = TableDataset(data=a5)
    assert [c.data for c in v5.data.values()] == a5
    assert v5['column1'][0] == 1
    assert v5['column2'][1] == 43.2


def test_TableDataset_func_row():
    # row ops
    v = TableDataset()
    c1 = Column([1, 4], 'sec')
    v.addColumn('col3', copy.deepcopy(c1))
    # for non-existing names set is addColum.
    c2 = Column([2, 3], 'eu')
    v['col4'] = copy.deepcopy(c2)

    # addRow
    assert v.rowCount == 2
    cc = copy.deepcopy(v['col3'])
    c33, c44 = 3.3, 4.4
    v.addRow({'col4': c44, 'col3': c33})
    assert v.rowCount == 3
    cc.append(c33)
    assert v['col3'] == cc   # [1, 4, 3.3]
    # add rows
    c33, c44 = [6.6, 9.9], [8.8, 12]
    v.addRow({'col4': c44, 'col3': c33}, rows=True)
    assert v.rowCount == 5
    cc.data.extend(c33)
    assert v['col3'] == cc
    # remove Row and rows
    assert v.removeRow(1) == [c1.data[1], c2.data[1]]
    assert v.rowCount == 4
    assert cc.pop(1) == c1.data[1]
    assert v['col3'] == cc
    # read rowa with slice
    s = v.getRow(slice(1, 3))
    assert s == [(3.3, 4.4), (6.6, 8.8)]
    assert [s[0][0], s[1][0]] == cc[1:3]
    assert v.getRowMap(slice(1, 3)) == {'col3': [3.3, 6.6], 'col4': [4.4, 8.8]}
    # remove rowa with slice
    assert v.removeRow(slice(1, 3)) == [[3.3, 6.6], [4.4, 8.8]]
    assert v.rowCount == 2
    del cc[1:3]
    assert v['col3'] == cc
    # acess rows


def test_TableDataset_func_column():
    # add, set, and replace columns
    # column set / get
    # http://herschel.esac.esa.int/hcss-doc-15.0/load/hcss_drm/api/herschel/ia/dataset/TableDataset.html#Z:Z__setitem__-java.lang.String-herschel.ia.dataset.Column-
    # add, replace
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

    # column names
    assert u.getColumnNames() == ['col3', 'col4']
    # unit access
    assert u['col4'].unit == 'j'
    # access index with indexOf
    assert u.indexOf('col3') == u.indexOf(c1)

    # access columns by name
    a1 = {'col1': Column(data=[1, 4.4, 5.4E3], unit='eV', description='1'),
          'col2': Column(data=[0, 43.2, 2E3], unit='cnt', description='2'),
          }
    c5 = Column(data=[-2, 9e-5, 8.888], unit='m', description='3')
    w = TableDataset(data=a1)  # inherited from DataWrapper
    w['col5'] = c5
    assert w['col5'] == c5

    # column by index
    assert w[1] == a1['col2']
    # write with index
    w[2] = a1['col1']  # now w['col3']==a1['col1']
    assert w['col5'] == a1['col1']
    assert w.getColumnNames() == ['col1', 'col2', 'col5']
    w[3] = a1['col2']
    assert w['column4'] == a1['col2']   # assigned col name is 'column'+3+1

    # getColumn
    a34 = [[11, 12, 13], [21, 22, 23], [31, 32, 33], [41, 42, 43]]
    v = TableDataset(data=a34)
    u = copy.deepcopy(a34)

    assert v.getColumn(3) == Column(u[3])
    assert v.getColumn('column4') == Column(u[3])
    assert v.getColumn([1, 2]) == [Column(u[1]), Column(u[2])]
    assert v.getColumn(['column2', 'column3']) == [Column(u[1]), Column(u[2])]
    assert v.getColumn([False, True, False, False]) == [Column(u[1])]
    assert v.getColumn([True, False]) == [Column(u[0])]
    assert v.getColumn([True, False, False, False, False]) == [Column(u[0])]
    assert v.getColumn([True, False, False, False, True]) == [Column(u[0])]

    # slice
    sliced = v[1:3]   # a list if the 2nd and 3rd cols
    assert len(sliced) == 2
    assert issubclass(sliced[0].__class__, Column)
    sl2 = v.getColumn(slice(1, 3,))   # [(name,col), (name,col)]
    assert sliced == [sl2[0], sl2[1]]
    # make a table out of the slice
    map12 = v.getColumnMap(slice(1, 3,))    # cannot use a lone int or str
    w2 = TableDataset(data=map12)
    assert w2.getColumnCount() == 2
    assert w2.getColumn(0) == v.getColumn(1)
    assert w2['column2'] == v['column2']
    assert id(w2['column2']) == id(v['column2'])
    assert w2['column3'] == v['column3']
    assert id(w2['column3']) == id(v['column3'])

    # remove column, check auxiliary list
    w3 = TableDataset(data=copy.deepcopy(a34))
    assert w3.list == a34
    w3.removeColumn('column1')
    assert w3[0] == w3['column2']
    assert w3.list == a34[1:]
    w3 = TableDataset(data=copy.deepcopy(a34))
    w3.removeColumn(slice(1, 3))  # 1,2 (column2,3) removed
    assert len(w3) == 2
    assert w3[0].data == a34[0]
    assert w3[1].data == a34[3]
    assert w3.list == [a34[0], a34[3]]
    w3.removeColumn(['column4', 'column1'])
    assert len(w3) == 0
    assert w3.list == []


def test_TableDataset_func():
    u = TableDataset()
    c1 = Column([1, 4], 'sec')
    u.addColumn('col3', c1)
    c2 = Column([2, 3], 'eu')
    u['col4'] = c2

    # access auxiliary list
    assert u.list == [c1.data, c2.data]

    # access cell value
    u.setValueAt(value=42, rowIndex=1, columnIndex=1)
    assert u.getValueAt(rowIndex=1, columnIndex=1) == 42

    # replace whole table. see constructor examples for making a1
    # make a deepcopy so when u changes data, v won't be affected
    a10 = {'col1': Column(data=[1, 4.4, 5.4E3], unit='eV', description='1'),
           'col2': Column(data=[0, 43.2, 2E3], unit='cnt', description='2')}
    c10 = copy.deepcopy(a10)
    assert id(a10['col1']) != id(c10['col1'])
    u.data = c10
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
    # generic column[index] names and None unit are given for the added columns
    assert u['column3'][1] == 7
    assert u['column3'].unit is None

    # syntax ``in``
    assert 'column3' in u

    # select
    a43 = [[11, 12, 13, 14], [21, 22, 23, 24], [31, 32, 33, 34]]
    v = TableDataset(data=a43)
    u = v.copy()
    u.removeRow(3)
    u.removeRow(0)
    assert v.select([1, 2]) == u
    u = v.copy()
    u.removeRow(3)
    u.removeRow(2)
    u.removeRow(0)
    assert v.select([False, True, False, False]) == u
    assert v.select([True, False]) == TableDataset(data=[[11], [21], [31]])
    assert v.select([True, False, False, False, False]
                    ) == TableDataset(data=[[11], [21], [31]])
    assert v.select([True, False, False, False, True]
                    ) == TableDataset(data=[[11], [21], [31]])

    # toString()
    v = TableDataset(data=a10)

    check_MDP(v)
    ts = '\n\nlevel 0\n'
    ts += v.toString()
    ts += '\n\nlevel 1\n'
    ts += v.toString(1)
    ts += '\n\nlevel 2, repr\n'
    ts += v.toString(2)
    ts += '\n\n'
    ts += 'an empty level 2: \n'
    ts += TableDataset().toString(level=2)
    ts += '\n\n'
    if mk_output:
        print(ts)
        with open('/tmp/output.py', 'a') as f:
            clsn = 'out_TableDataset'
            f.write('%s = """%s"""\n' % (clsn, ts))
    else:
        assert ts == out_TableDataset

    checkjson(u)
    checkgeneral(u)


def test_TableDataset_doc():
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
    # newR = ODict(Time=101, Energy=102, dist=103)
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

    # ts = x.toString()
    # print(ts)


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


def test_CompositeDataset_init():
    # constructor
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
    # def test_CompositeDataset_func():

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
    v1.meta[b11].value = 999
    assert v != v1
    assert v1 != v

    # nested datasets
    v['v1'] = v1
    assert v['v1'][a9] == a4

    # toString()
    v3 = CompositeDataset(description='test CD')
    for n, p in standardtestmeta().items():
        v3.meta[n] = p
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
    ts = 'level 0\n'
    ts += v3.toString()
    ts += 'level 1, repr\n'
    ts += v3.toString(1)
    ts += 'level 2,\n'
    ts += v3.toString(2)
    if mk_output:
        print(ts)
        with open('/tmp/output.py', 'a') as f:
            clsn = 'out_CompositeDataset'
            f.write('%s = """%s"""\n' % (clsn, ts))
    else:
        assert ts == out_CompositeDataset

    checkjson(v)
    checkgeneral(v)


def test_Indexed():
    # number of columns and rows
    Nc, Nr = 6, 7

    class IDX(Indexed):
        def __init__(self, c=Nc, r=Nr, **k):

            super().__init__(**k)
            self.data = [[n+m*10 for n in range(r)] for m in range(c)]

    # [[0, 1, 2...], [10, 11, 12...][20, 21, 22...], ...]
    array1 = [[n+m*10 for n in range(Nr)] for m in range(Nc)]
    # creation
    # default
    v = Indexed()
    assert len(v._tableOfContent) == 0
    # one column in indexPattern
    assert v._indexPattern == [0]
    v.data = copy.deepcopy(array1)
    assert len(v.data) == Nc
    # with keyword
    v2 = Indexed(indexPattern=[1, 3, 5])
    v2.indexPattern == [1, 3, 5]
    assert len(v2._tableOfContent) == 0
    assert v2.indexPattern == [1, 3, 5]
    # subclassing
    v3 = IDX(indexPattern=[1, 2])
    v3.indexPattern == [1, 2]
    assert len(v3._tableOfContent) == 0
    assert v3.indexPattern == [1, 2]

    # update
    # one column in indexPattern
    # all rows
    # generate table of content
    v.data = [[0, 1, 2, 3, 4]]
    v.updateToc()
    assert len(v.toc) == 5
    # check the index table
    for row in range(5):
        assert v.toc[v.data[0][row]] == row
    # test all record selections
    for sel in [None, [0], slice(0, 1)]:
        v.data = copy.deepcopy(array1)
        # generate table of content
        v.updateToc(which=[v.data[0]], for_records=sel)
        # change the 0th row

        assert [v.data[i][0]
                for i in range(Nc)] == [array1[i][0] for i in range(Nc)]
        v.data[0][0] += Nr  # make sure that the result is unique in the column
        assert [v.data[i][0]
                for i in range(Nc)] != [array1[i][0] for i in range(Nc)]
        assert len(v.toc) == Nr
        # make new toc
        v.updateToc(which=[v.data[0]], for_records=sel)
        assert len(v.toc) == Nr
        # check the index table
        for row in range(Nr):
            assert v.toc[v.data[0][row]] == row

    # multiple columns
    v2.data = copy.deepcopy(array1)
    # all rows
    v2.updateToc()
    for row in range(Nr):
        assert v2.toc[(v2.data[1][row], v2.data[3]
                       [row], v2.data[5][row])] == row
    # built-in from subclassing
    v3.updateToc()
    for row in range(Nr):
        assert v3.toc[(v3.data[1][row], v3.data[2][row])] == row

    # same index in #1,2 two rows
    v3.data = [[0, 1, 2], [1, 2, 2], [2, 3, 3]]
    v3.updateToc()
    # row 0 and 1 have the same key. only row 1 can be looked up
    assert len(v3.toc) == 2
    for row in [0, 2]:
        assert v3.toc[(v3.data[1][row], v3.data[2][row])] == row

    # look-up
    assert v2.vLookUp((11, 31, 51)) == 1
    assert v2.vLookUp((11, 31, 51), return_index=False) == [
        1+n*10 for n in range(Nc)]
    with pytest.raises(KeyError):
        assert v2.vLookUp((1, 31, 51)) == [1+n*10 for n in range(Nc)]

    # multiple keys
    assert v2.vLookUp([(11, 31, 51), (14, 34, 54)], multiple=1) == [1, 4]
    assert v2.vLookUp([(11, 31, 51), (14, 34, 54)], return_index=False, multiple=True) == [
        tuple(1+n*10 for n in range(Nc)), tuple(4+n*10 for n in range(Nc))]


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
    # <class 'fdi.dataset.dataset.CompositeDataset'>
    # {meta = "MetaData[]", _sets = ['MyArray', 'MyTable', 'MyComposite']}
    print(c.__class__)
    print(c)

    # ... print(information about child "MyComposite", and ...
    # <class 'fdi.dataset.dataset.CompositeDataset'>
    # {meta = "MetaData[]", _sets = ['Child1', 'Child2']}
    print(c["MyComposite"].__class__)
    print(c["MyComposite"])

    # ... that of a nested child ...
    # <class 'fdi.dataset.dataset.CompositeDataset'>
    # {meta = "MetaData[]", _sets = []}
    print(c["MyComposite"]["Child1"].__class__)
    print(c["MyComposite"]["Child1"])

    # ... or using java syntax to access Child1:
    # {meta = "MetaData[]", _sets = []}
    print(c.get("MyComposite").get("Child1"))

    # or alternatively:
    # <class 'fdi.dataset.dataset.CompositeDataset'>
    # {meta = "MetaData[]", _sets = ['Child1', 'Child2']}
    child = c["MyComposite"]
    print(child.__class__)
    print(child)


def test_FineTime():
    # default
    v = FineTime()
    assert v.tai == 0
    assert v.format == v.DEFAULT_FORMAT
    assert v.toDatetime().year == 1958
    # at Epoch, TAI=0
    v = FineTime(v.EPOCH)
    assert v.tai == 0
    # at TAI = 1, UTC ...
    v = FineTime(1)
    assert v.toDatetime().microsecond == 1
    # from string
    v = FineTime('1990-09-09T12:34:56.789098 UTC')
    print(v)
    # comparison
    v1 = FineTime(12345678901234)
    v2 = FineTime(12345678901234)
    v3 = FineTime(1234567890123)
    assert id(v1) != id(v2)
    assert v1 == v2
    assert v1 >= v2
    assert v2 <= v1
    assert v3 != v2
    assert v3 < v2
    assert v2 > v3
    assert v2 > 5
    assert v3 <= v2
    assert v2 >= v3

    # arithemetics
    v = FineTime(1234567)
    assert v + 1 == FineTime(1234568)
    assert v - 1 == FineTime(1234566)
    assert v - FineTime(1) == 1234566
    # two FineTime instances cannot add
    with pytest.raises(TypeError):
        assert v + FineTime(1) == FineTime(1234568)
    with pytest.raises(TypeError):
        1 + v

    # leap seconds
    v1 = FineTime(datetime.datetime(2015, 6, 30, 23, 59, 59))
    #v2 = FineTime(datetime.datetime(2015, 6, 30, 23, 59, 60))
    v3 = FineTime(datetime.datetime(2015, 7, 1, 0, 0, 0))
    assert v3-v1 == 2000000  # leapsecond added
    # assert v3-v2 == 1000000  # 59:60 != 00:00

    dt0 = datetime.datetime(
        2019, 2, 19, 1, 2, 3, 456789, tzinfo=timezone.utc)
    posix_epoch = datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    # unix seconds has no leap seconds
    unsec = (dt0 - FineTime.EPOCH).total_seconds()
    assert dt0.timestamp() == unsec - (posix_epoch - FineTime.EPOCH).total_seconds()
    v = FineTime(dt0)
    assert unsec == 1929229323456789/1000000
    assert v.tai == 1929229360456789
    assert v.tai/1000000 - unsec == 37
    dt = v.toDatetime()
    assert int(dt.timestamp()) == int(dt0.timestamp())
    # So that timezone won't show on the left below
    d = dt.replace(tzinfo=None)
    assert d.isoformat() == '2019-02-19T01:02:03.456789'
    assert v.tai == v.datetimeToFineTime(dt)
    assert dt == v.toDatetime(v.tai)

    assert v.isoutc() == '2019-02-19T01:02:03.456789'

    # add 1min 1.1sec
    v2 = FineTime(datetime.datetime(
        2019, 2, 19, 1, 3, 4, 556789, tzinfo=timezone.utc))
    assert v != v2
    assert abs(v2.subtract(v) - 61100000) < 0.5
    checkjson(v)
    checkgeneral(v)


def test_FineTime1():
    # default
    v = FineTime1()
    assert v.tai == 0
    assert v.format == v.DEFAULT_FORMAT
    assert v.toDatetime().year == 2017
    # at Epoch, TAI=0
    v = FineTime1(v.EPOCH)
    assert v.tai == 0
    # at TAI = 1, UTC ...
    v = FineTime1(1)
    assert v.toDatetime().microsecond == 1000
    dt0 = datetime.datetime(
        2019, 2, 19, 1, 2, 3, 456789, tzinfo=timezone.utc)
    v = FineTime1(dt0)
    assert v.tai == 67309323457
    dt = v.toDatetime()
    assert int(dt.timestamp()) == int(dt0.timestamp())
    # So that timezone won't show on the left below
    d = dt.replace(tzinfo=None)
    assert d.isoformat() == '2019-02-19T01:02:03.457000'
    assert v.tai == v.datetimeToFineTime(dt)
    assert dt == v.toDatetime(v.tai)
    # format
    assert v.isoutc() == '2019-02-19T01:02:03.457000'
    # add 1min 1.1sec
    v2 = FineTime1(datetime.datetime(
        2019, 2, 19, 1, 3, 4, 556789, tzinfo=timezone.utc))
    assert v != v2
    assert abs(v2.subtract(v) - 61100) < 0.5
    checkjson(v)
    checkgeneral(v)


def test_FineTimes_toString():
    # toString
    ts = 'toString test\n'
    dt0 = datetime.datetime(
        2019, 2, 19, 1, 2, 3, 456789, tzinfo=timezone.utc)
    # format
    for vformat in [FineTime.DEFAULT_FORMAT, '%Y']:
        ts += '=========== format: "' + vformat + '" =======\n'
        for v in [FineTime(dt0), FineTime1(dt0)]:
            v.format = vformat
            ts += v.__class__.__name__ + '\n'
            for width in [0, 1]:
                # default width is 0
                for level in [0, 1, 2]:
                    s = v.toString(level=level, width=width)
                    ts += f'level={level} width={width}: {s}\n'
    if mk_output:
        print(ts)
        with open('/tmp/output.py', 'a') as f:
            clsn = 'out_FineTime'
            f.write('%s = """%s"""\n' % (clsn, ts))
    else:
        assert ts == out_FineTime


def test_History():
    v = History()
    checkjson(v)
    checkgeneral(v)


def test_BaseProduct():
    """ """

    x = BaseProduct(description="This is my product example")

    # print(x.__dict__)
    # print(x.meta.toString())
    assert x.meta['description'].value == "This is my product example"
    assert x.description == "This is my product example"
    assert x.meta['type'].value == x.__class__.__qualname__
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

    # default is the first dataset
    assert BaseProduct('empty').getDefault() is None
    d = x.getDefault()
    sets = x.getDataWrappers()
    # they are the same
    assert id(d) == id(sets['RawImage'])

    p = Parameter(value="2.1a",
                  description="patched")
    x.meta["Version"] = p
    assert x.meta["Version"] == p
    a1 = 'a test NumericParameter'
    a2 = 1
    a3 = 'second'
    v = NumericParameter(description=a1, value=a2, unit=a3)
    x.meta['numPar'] = v

    # test mandatory BaseProduct properties that are also metadata
    x.creator = ""
    a0 = "Me, myself and I"
    x.creator = a0
    assert x.creator == a0
    # metada by the same name is also set
    assert x.meta["creator"].value == a0
    # change the metadata
    a1 = "or else"
    x.meta["creator"] = Parameter(a1)
    # metada changed
    assert x.meta["creator"].value == a1
    # so did the property
    assert x.creator == a1

    # normal metadata
    # if the attitute does not exist, return None. This is an OrderedDict behavior.
    assert x.meta['notthere'] is None

    # test comparison:
    p1 = BaseProduct(description="oDescription")
    p2 = BaseProduct(description="Description 2")
    assert p1.equals(p2) == False
    p3 = copy.deepcopy(p1)  # XXX
    assert p1.equals(p3) == True

    # toString
    ts = x.toString()
    # print(ts)

    checkjson(x)
    checkgeneral(x)


def check_Product(AProd):
    """ """
    # creation
    x = AProd(description="This is my product example",
              instrument="MyFavourite", modelName="Flight")
    # print(x.__dict__)
    # print(x.meta.toString())
    # attribute added by Product
    if AProd.__name__ == x.zInfo['name']:
        assert x.meta['type'].value == x.__class__.__name__
    assert x.meta['description'].value == "This is my product example"
    assert x.meta['instrument'].value == "MyFavourite"
    assert x.modelName == "Flight"
    # positional arg
    x = AProd("product example", instrument='spam')
    # not stored in class variable projectInfo
    x2 = AProd("product example2", instrument='egg')
    assert x.description == "product example"
    assert x.instrument == 'spam'
    # Test metadata
    # add one
    x.meta['an'] = Parameter('other')
    assert x.meta['an'].value == 'other'
    # cannot use x.an
    with pytest.raises(AttributeError):
        t = x.an
    # remove it
    x.meta.remove('an')
    # gone
    assert 'an' not in x.meta

    # test mandatory Product project-level properties that are also metadata
    x.instrument = ""
    a0 = "Me, myself and I"
    x.instrument = a0
    assert x.instrument == a0
    # change it
    assert x.meta["instrument"].value == a0
    a1 = "or else"
    x.meta["instrument"] = Parameter(a1)
    assert x.meta["instrument"].value == a1
    assert x.instrument == a1

    # toString
    ts = x.toString()
    # print(ts)

    checkjson(x)
    checkgeneral(x)


def test_ReadOnlyDict():
    d = {3: 4, 5: {6: (7, 7)}, 'metadata': {
        'version': {'data_type': 'string'}}}
    v = ReadOnlyDict(d)
    assert v[3] == 4
    assert d['metadata']['version']['data_type'] == 'string'
    assert id(v) != id(d)
    assert id(v[5]) != id(d[5])
    assert issubclass(v[5].__class__, ReadOnlyDict)
    assert v[5][6] == (7, 7)
    with pytest.raises(AttributeError):
        v[3] = 2
    with pytest.raises(AttributeError):
        v[5] = 4
    with pytest.raises(AttributeError):
        v[5][6] = 4
    # multiple
    v2 = ReadOnlyDict(d)
    assert id(v) != id(v2)
    assert id(v[5]) != id(v2[5])
    assert id(v[5][6]) == id(v2[5][6])  # value is not list or dict
    assert id(v['metadata']['version']) != id(v2['metadata']['version'])
    assert id(v['metadata']['version']['data_type']) == id(
        v2['metadata']['version']['data_type'])  # value is not list or dict
    with pytest.raises(AttributeError):
        v[5][6] = [4.33]

    # update
    u = {}
    u.update(v)
    assert id(u[5]) != id(d[5])
    assert id(u[5]) == id(v[5])
    assert id(u['metadata']) != id(d['metadata'])
    # update returns the same object
    assert id(u['metadata']) == id(v['metadata'])

    # copy generates a normal dict that does not point to orginsl dict-type counterparts
    # cc = copy.deepcopy(v)
    # assert cc == d
    # assert issubclass(d[5].__class__, dict)
    # assert id(v[3]) == id(cc[3])
    # assert id(v[5]) != id(cc[5])
    # assert id(v[5][6]) == id(cc[5][6])


def test_Product():
    check_Product(Product)


def test_SubProduct():

    y = SP()

    # register it in Classes.mapping so deserializer knows how to instanciate.
    Classes.mapping.update({'SP': SP})

    check_Product(SP)

    from fdi.pal.context import MapContext

    class SSP(SP, MapContext):
        def __init__(self, **kwds):
            super().__init__(**kwds)

    x = SSP()
    x.instrument = 'ff'
    assert x.instrument == 'ff'
    x.rr = 'r'
    assert x.rr == 'r'


def est_yaml2python():
    import pkg_resources
    v = {'a': 1, 'b': 'foo', 'c': 4.5, 'd': FineTime1(0), 'e': Vector((7, 8, 9))
         }
    yf = pkg_resources.resource_filename(
        "fdi.dataset.resources", "Product.yml")
    pf = '/tmp/p.py'
    d = collections.OrderedDict(yaml.load(yf))
    yaml2python.__main__({'-y': yf, '-o': pf})
    with open(pf, 'r') as f:
        p = f.read()
    print(""" """+p)


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
#     #js = serialize(data)
#     # print(js)
#     #js = json.dumps(data)
#     print(js)
#     p = json.loads(js, cls=JSONObjectDecoder)
#     print(p['h'].b)

def running(t):
    print('running ' + str(t))
    t()


if __name__ == '__main__':

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
    running(test_ndprint0)
    running(test_Annotatable)
    running(test_Composite)
    running(test_AbstractComposite)
    running(test_Copyable)
    running(test_EventSender)
    running(test_datatypes)
    running(test_Parameter1)
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
    running(test_BaseProduct)
    running(test_Product)
