# -*- coding: utf-8 -*-

from fdi.utils.jsonpath import jsonPath, flatten_compact
from fdi.utils.validator import getValidator, makeSchemaStore
from fdi.utils.common import lls
from fdi.dataset.serializable import serialize
from fdi.dataset.finetime import FineTime, FineTime1
from fdi.dataset.metadata import Parameter, MetaData, make_jsonable, guess_value
from fdi.dataset.listener import ListenerSet
from fdi.dataset.numericparameter import NumericParameter, BooleanParameter
from fdi.dataset.stringparameter import StringParameter
from fdi.dataset.dateparameter import DateParameter
from fdi.dataset.listener import EventSender, EventTypes, EventType, EventTypeOf, MetaDataListener, EventListener
from fdi.dataset.arraydataset import ArrayDataset, Column
from fdi.dataset.mediawrapper import MediaWrapper
from fdi.dataset.tabledataset import TableDataset
from fdi.dataset.dataset import Dataset, CompositeDataset

if 0:
    from fdi.dataset.annotatable import Annotatable
    from fdi.dataset.copyable import Copyable
    from fdi.dataset.odict import ODict
    from fdi.dataset.eq import deepcmp
    from fdi.dataset.classes import Classes
    from fdi.dataset.serializable import serialize
    from fdi.dataset.deserialize import deserialize
    from fdi.dataset.quantifiable import Quantifiable
    from fdi.dataset.messagequeue import MqttRelayListener, MqttRelaySender
    from fdi.dataset.composite import Composite
    from fdi.dataset.metadataholder import MetaDataHolder
    from fdi.dataset.datatypes import DataTypes, DataTypeNames
    from fdi.dataset.attributable import Attributable
    from fdi.dataset.abstractcomposite import AbstractComposite
    from fdi.dataset.datawrapper import DataWrapper, DataWrapperMapper
    from fdi.dataset.indexed import Indexed
    from fdi.dataset.ndprint import ndprint
    from fdi.dataset.datatypes import Vector, Vector2D, Quaternion
    from fdi.dataset.invalid import INVALID
    from fdi.dataset.history import History
    from fdi.dataset.baseproduct import BaseProduct
    from fdi.dataset.product import Product
    from fdi.dataset.browseproduct import BrowseProduct
    from fdi.dataset.readonlydict import ReadOnlyDict
    from fdi.dataset.unstructureddataset import UnstructuredDataset
from fdi.dataset.testproducts import SP, get_demo_product

import pytest
from pprint import pprint, pformat
import json
from jsonschema import validate, ValidationError, SchemaError
import copy
import datetime
from datetime import timezone
import os

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


SCHEMA_TEST_DATA = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), 'resources/schema')
SCHEMA_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../fdi/schemas'))
SSP = 'https://fdi.net/schemas/%s/%s'
""" Schema store prefix"""

verbose = False


@pytest.fixture(scope='package')
def schema_store():
    store = makeSchemaStore()
    return store


def check_examples_defaults(vtr, schema, jsn, paths):
    """check if "examples", "default" are valid."""

    if verbose:
        print(schema['title'])
        print('\n'.join(sorted(jsonPath(schema, '$..*', val='paths'))))

    for path in paths:
        for theproperty_name, theproperty in jsonPath(schema, path, val='full'):
            # theproperty_name is like 'allOf/1/properties/default/examples'
            mod = copy.deepcopy(jsn)
            if issubclass(theproperty.__class__, list):
                thelist = theproperty
            else:
                thelist = [theproperty]
            for n, example in enumerate(thelist):
                if verbose:
                    print('Auto Validating %s["%s"][%d] %s...' % (
                        schema['title'], theproperty_name, n, example))
                if 'properties/value' in theproperty_name:
                    mod['value'] = example
                    assert vtr.validate(mod) is None
                elif 'properties/examples' in theproperty_name or \
                        'examples' == theproperty_name:
                    mod = example
                    assert vtr.validate(mod) is None
                else:
                    prop = theproperty_name.split(
                        'properties/', 1)[-1].split('/', 1)[0]
                    if prop == 'default' and 'value' in jsn:
                        # default ,means value default
                        mod['value'] = example
                    else:
                        mod[prop] = example
                    assert vtr.validate(mod) is None


def test_FineTime(schema_store):
    scn = 'FineTime'
    sch = schema_store[SSP % ('dataset', scn)]

    if 1:
        jsn = json.loads(serialize(FineTime(123456789876543)))
    else:
        jsn_path = os.path.join(SCHEMA_TEST_DATA, scn0 + scn + '.jsn')
        with open(jsn_path, 'r') as file:
            jsn = json.load(file)
    # print(jsn)
    vtr = getValidator(sch, verbose=verbose)
    check_examples_defaults(vtr, sch, jsn, [
                            'properties.format.examples',
                            'examples',
                            ])

    assert vtr.validate(jsn) is None
    bad = copy.copy(jsn)
    bad['tai'] = 9.9
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None
    bad = copy.copy(jsn)
    bad['format'] = ''
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None
    bad = copy.copy(jsn)
    bad['_STID'] = None
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None


def test_urn(schema_store):
    scn = 'Urn'
    sch = schema_store[SSP % ('pal', scn)]

    if 1:
        jsn = json.loads(serialize('urn:pool:si.PL:20'))
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_examples_defaults(vtr, sch, jsn, [
                            'examples',
                            ])

    # invalid urn in 'urns'
    cpy = copy.copy(jsn)
    bad = cpy.replace("urn:", "urn::")
    with pytest.raises(ValidationError):
        assert getValidator(sch, verbose=verbose).validate(bad) is None


def test_STID(schema_store):
    scn = 'STID'
    sch = schema_store[SSP % ('dataset', scn)]

    if 1:
        jsn = json.loads(serialize('FineTime'))
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_examples_defaults(vtr, sch, jsn, [
                            'examples',
                            ])

    # invalid
    cpy = copy.copy(jsn)
    bad = cpy.replace("F", "#")
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None
    with pytest.raises(ValidationError):
        assert vtr.validate(None) is None


def test_ListenerSet(schema_store):
    scn = 'ListenerSet'
    sch = schema_store[SSP % ('dataset', scn)]

    if 1:
        jsn = json.loads(serialize(ListenerSet(), indent=4))
    if verbose:
        logger.info(jsn)
    assert jsn['_STID'] == 'ListenerSet'
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None
    bad = copy.copy(jsn)
    bad['_STID'] = None
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None
    # can be None
    assert vtr.validate(None) is None


def test_xParameter(schema_store):
    scn = 'Parameter'
    sch = schema_store[SSP % ('dataset', scn)]
    x = Parameter(3.14,
                  description="foo",
                  default=42,
                  valid={3.14: 'ok'},
                  typ_=None)
    jsn = json.loads(serialize(x, indent=4)
                     )
    if verbose:
        logger.info(jsn)
    assert jsn['type'] == 'float'
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_examples_defaults(vtr, sch, jsn, [
                            'allOf.[1].properties.default.examples',
                            'allOf.[1].properties.default.default',
                            'allOf.[1].properties.value.examples',
                            'examples',
                            ])

    assert jsn['valid'] is not None
    jsn['valid'] = None
    assert jsn['valid'] is None
    vtr.validate(jsn) is None
    jsn['description'] = None
    vtr.validate(jsn) is None

    # invalid
    bad = copy.copy(jsn)
    del bad['value']
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None
    bad = copy.copy(jsn)
    bad['valid'] = 4
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None
    st = copy.copy(jsn).pop('_STID')
    assert st == 'Parameter'
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None
    bad = copy.copy(jsn)
    bad['_STID'] = 'Fi'
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None

    bad = copy.copy(jsn)
    del bad['_STID']
    with pytest.raises(ValidationError):
        k = vtr.validate(bad)
    bad = copy.copy(jsn)
    bad['type'] = 'foo'
    with pytest.raises(ValidationError):
        k = vtr.validate(bad)
    bad = copy.copy(jsn)
    bad['valid'] = [[1, 2]]
    vtr.validate(bad) is None
    bad['valid'] = [[1], [1, 2]]
    with pytest.raises(ValidationError):
        vtr.validate(bad) is None
    # logger.warning(str(vtr.validate(bad)))


def test_BooleanParameter(schema_store):
    scn = 'BooleanParameter'
    sch = schema_store[SSP % ('dataset', scn)]

    if 1:
        jsn = json.loads(serialize(BooleanParameter(True,
                                                    description="foo?",
                                                    default=None,
                                                    ),
                                   indent=4)
                         )
    if verbose:
        logger.info(jsn)
    assert jsn['type'] == 'boolean'
    assert jsn['default'] is None
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_examples_defaults(vtr, sch, jsn, [
                            'allOf.[1].properties.value.examples',
                            'allOf.[1].properties.value.default',
                            'allOf.[1].properties.default.examples',
                            'allOf.[1].properties.default.default',
                            'examples',
                            ])

    # can be None?
    with pytest.raises(ValidationError):
        assert vtr.validate(None) is None

    # invalid
    bad = copy.copy(jsn)
    bad['type'] = 3
    bad['value'] = 'd'
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None


def test_StringParameter(schema_store):
    scn = 'StringParameter'
    sch = schema_store[SSP % ('dataset', scn)]

    if 1:
        jsn = json.loads(serialize(StringParameter("wahah",
                                                   description="tester",
                                                   typecode='10B'
                                                   ),
                                   indent=4)
                         )
    if verbose:
        logger.info(jsn)
    if 'type' in jsn:
        assert jsn['type'] == 'string'
    assert jsn['default'] is None
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_examples_defaults(vtr, sch, jsn, [
                            'allOf.[1].properties.value.examples',
                            'allOf.[1].properties.value.default',
                            'allOf.[1].properties.default.examples',
                            'allOf.[1].properties.default.default',
                            'allOf.[1].properties.typecode.examples',
                            'examples',
                            ])

    # can be None?
    with pytest.raises(ValidationError):
        assert vtr.validate(None) is None

    # invalid
    bad = copy.copy(jsn)
    bad['type'] = 3
    bad['value'] = 'd'
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None


def test_NumericParameter(schema_store):
    scn = 'NumericParameter'
    sch = schema_store[SSP % ('dataset', scn)]

    if 1:
        jsn = json.loads(serialize(NumericParameter(3.14,
                                                    description="foo",
                                                    default=42,
                                                    valid={0: 'ok'},
                                                    typ_=None,
                                                    unit='lyr'),
                                   indent=4)
                         )
    if verbose:
        logger.info(jsn)
    assert jsn['unit'] == 'lyr'
    assert jsn['typecode'] == None
    vtr = getValidator(sch, verbose=verbose)

    check_examples_defaults(vtr, sch, jsn, [
                            'properties.default.examples',
                            'properties.default.default',
                            'properties.value.examples',
                            'examples',
                            ])

    # can not be None.
    with pytest.raises(ValidationError):
        assert vtr.validate(None) is None
    assert vtr.validate(jsn) is None

    # invalid urn in 'urns'
    bad = copy.copy(jsn)
    bad['typecode'] = 3
    bad['value'] = 'd'
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None

    v = NumericParameter(
        value=[0b01], description='valid rules described with binary masks',
        typ_='list',
        default=[0b00],
        valid={(0b011000, 0b01): 'on', (0b011000, 0b00): 'off'},
        typecode='H')

    jsn = json.loads(serialize(v))
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    # Parameter won't cut it
    sch_para = schema_store[SSP % ('dataset', 'Parameter')]
    vtr_para = getValidator(sch_para, verbose=verbose)
    with pytest.raises(ValidationError):
        assert vtr_para.validate(jsn) is None
    x_para = Parameter(3.14,
                       description="foo",
                       default=42,
                       valid={3.14: 'ok'},
                       typ_=None)
    jsn_para = json.loads(serialize(x_para, indent=4))
    with pytest.raises(ValidationError):
        assert vtr.validate(jsn_para) is None


def test_DateParameter(schema_store):
    scn = 'DateParameter'
    sch = schema_store[SSP % ('dataset', scn)]
    then = datetime.datetime(
        2019, 2, 19, 1, 2, 3, 456789, tzinfo=timezone.utc)
    v = DateParameter(value=FineTime(then), description='date param',
                      default=99,
                      valid={(0, 9876543210123456): 'xy'})
    tc = v.typecode

    jsn = json.loads(serialize(v))

    if verbose:
        logger.info("JSON instance to test: %s" % jsn)
    assert jsn['default']['tai'] == 99
    assert jsn['typecode'] == tc == "%Y-%m-%dT%H:%M:%S.%f"
    vtr = getValidator(sch, verbose=verbose)

    check_examples_defaults(vtr, sch, jsn, [
                            'allOf.[1].properties.default.examples',
                            'allOf.[1].properties.default.default',
                            'allOf.[1].properties.value.examples',
                            'examples',
                            ])

    assert vtr.validate(jsn) is None
    # default can also be None and integer of TAI value.
    jsn['default'] = 0
    assert vtr.validate(jsn) is None
    # value is assigned with TAI
    v = DateParameter(value=1234, description='value=1234',
                      default=99,
                      valid={(0, 987): 'val'})
    # "value" attribute is still FineTime object
    assert issubclass(v.value.__class__, FineTime)
    assert v.value.tai == 1234
    jsn = json.loads(serialize(v))
    assert vtr.validate(jsn) is None

    # can not be None?
    with pytest.raises(ValidationError):
        assert vtr.validate(None) is None

    # invalid
    # value is not FineTime
    bad = copy.copy(jsn)
    bad['value'] = {"foo": 4}
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None
    bad = copy.copy(jsn)
    bad['typecode'] = 3
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None
    bad = copy.copy(jsn)
    bad['value'] = 'd'
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None

    v = StringParameter(
        value='IJK', description='this is a string parameter. but only "" is allowed.',
        valid={'': 'empty'},
        default='cliche',
        typecode='B')


def test_MetaData(schema_store):
    scn = 'MetaData'
    sch = schema_store[SSP % ('dataset', scn)]

    v = MetaData()
    v['par'] = Parameter(description='test param', value=534)
    a1 = 'a test NumericParameter'
    a2 = 100.234
    a3 = 'second'
    a4 = 'float'
    a5 = 0
    a6 = ''
    a7 = 'f'
    v['num'] = NumericParameter(description=a1, value=a2, unit=a3,
                                typ_=a4, default=a5, valid=a6, typecode=a7)
    then = datetime.datetime(
        2019, 2, 19, 1, 2, 3, 456789, tzinfo=timezone.utc)
    v['dat'] = DateParameter(value=FineTime(then), description='date param',
                             default=99,
                             valid={(0, 9876543210123456): 'xy'})

    a1 = 'a test BooleanParameter'
    a2 = 100.234
    a5 = True
    a6 = [[(True, False), "all"]]
    v['boo'] = BooleanParameter(description=a1, value=a2,
                                default=a5, valid=a6)
    a1 = 'a test StringcParameter'
    a2 = 'eeeee'
    a3 = 'second'
    a4 = 'string'
    a5 = ''
    a6 = '9B'
    v['str'] = StringParameter(description=a1, value=a2, default=a3,
                               valid=a5, typecode=a6)

    # listeners

    class MockMetaListener(MetaDataListener):
        pass
    lis1 = MockMetaListener('foo')
    lis2 = MockMetaListener('bar')

    v.addListener(lis1)
    v.addListener(lis2)

    jsn = json.loads(serialize(v))

    if 1 or verbose:
        logger.info("JSON instance to test: %s" %
                    lls(pformat(jsn, indent=4), 2000))
    # assert jsn['default']['tai'] == 99
    # assert jsn['typecode'] == tc == "%Y-%m-%dT%H:%M:%S.%f"
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None


def test_ArrayDataset(schema_store):
    scn = 'ArrayDataset'
    sch = schema_store[SSP % ('dataset', scn)]

    atype = list

    if issubclass(atype([]).__class__, (bytes, bytearray)):
        a1 = atype([1, 44, 0xff])      # an array of data
        a4 = 'integer'              # type
        a6 = 'H'                  # typecode
    else:
        a1 = atype([1, 4.4, 5.4E3])      # an array of data
        a4 = 'float'              # type
        a6 = 'f'                  # typecode
    a2 = 'ev'                 # unit
    a3 = 'three energy vals'  # description
    a7 = (8, 9)

    v = ArrayDataset(data=a1, unit=a2, description=a3,
                     typ_=a4, typecode=a6)

    #v.meta = MetaData(description='test ArrayDataset.MEtadata')
    #v.data = 987.4

    jsn = json.loads(serialize(v))

    if 1 or verbose:
        logger.info("JSON instance to test: %s" %
                    lls(pformat(jsn, indent=4), 2000))
    # assert jsn['default']['tai'] == 99
    # assert jsn['typecode'] == tc == "%Y-%m-%dT%H:%M:%S.%f"
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None


def test_Dataset(schema_store):
    scn = 'Dataset'
    sch = schema_store[SSP % ('dataset', scn)]

    v = Dataset(description='test Dataset')
    v.meta = MetaData(description='test Dataset.MEtadata')
    v.data = 987.4

    jsn = json.loads(serialize(v))

    if 1 or verbose:
        logger.info("JSON instance to test: %s" %
                    lls(pformat(jsn, indent=4), 2000))
    # assert jsn['default']['tai'] == 99
    # assert jsn['typecode'] == tc == "%Y-%m-%dT%H:%M:%S.%f"
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None


def te():
    try:
        assert validate(jsn, sch)
    except SchemaError as e:
        print("There is an error with the schema")
        assert False
    except ValidationError as e:
        print(e)

        print("---------")
        print(e.absolute_path)

        print("---------")
        print(e.absolute_schema_path)
        assert False
