# -*- coding: utf-8 -*-

from fdi.utils.jsonpath import jsonPath, flatten_compact
from fdi.dataset.schemas import getValidator, makeSchemaStore, validateJson
from fdi.utils.common import lls
import fdi.dataset.serializable
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
from fdi.dataset.unstructureddataset import UnstructuredDataset
from fdi.dataset.history import History
from fdi.dataset.baseproduct import BaseProduct
from fdi.dataset.product import Product
from fdi.dataset.datatypes import Vector, Vector2D, Quaternion
from fdi.dataset.classes import Classes
from fdi.dataset.serializable import serialize, Serializable
from fdi.pal.context import MapContext
from fdi.pal.productref import ProductRef
if 0:
    from fdi.dataset.annotatable import Annotatable
    from fdi.dataset.copyable import Copyable
    from fdi.dataset.odict import ODict
    from fdi.dataset.eq import deepcmp
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
    from fdi.dataset.invalid import INVALID
    from fdi.dataset.browseproduct import BrowseProduct
    from fdi.dataset.readonlydict import ReadOnlyDict

from fdi.dataset.testproducts import SP, get_demo_product

from test_dataset import demo_TableDataset, demo_CompositeDataset

# from jsonschema import Draft7Validator as the_validator
from jsonschema import Draft201909Validator as the_validator
from jsonschema import RefResolver
from jsonschema.exceptions import RefResolutionError
from jsonschema import validate, ValidationError, SchemaError


import pytest
from pprint import pprint, pformat
import json
import copy
import array
import datetime
from datetime import timezone
import os
import os.path as op

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


SCHEMA_TEST_DATA = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), 'resources/schema')
SCHEMA_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../fdi/schemas'))
SSP = 'https://fdi.schemas/%s%s'
""" Schema store prefix"""

verbose = 1 #False


@pytest.fixture(scope='function')
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


def check_general(vtr, jsn, name):
    # STID
    assert vtr.validate(jsn) is None
    # change _STID
    bad = copy.deepcopy(jsn)
    bad['_STID'] = bad['_STID'][:-1]
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None
    # remove _STID
    bad = copy.deepcopy(jsn)
    st = bad.pop('_STID', '')
    assert name in st
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None
    bad = copy.deepcopy(jsn)
    # remove metadata
    if bad.pop('meta', 0) or bad.pop('_ATTR_meta', 0):
        with pytest.raises(ValidationError):
            assert vtr.validate(bad) is None

    if vtr.is_type(vtr.schema, 'object'):
        # change Require_STID to false
        sch = copy.deepcopy(vtr.schema)
        sch['$ref'] = "https://fdi.schemas/Require_STID_False"
        vtr = getValidator(sch, verbose=verbose)
        bad = copy.deepcopy(jsn)
        st = bad.pop('_STID', '')
        # STID is not required.
        assert vtr.validate(bad) is None


def test_validator():
    #fdi_sch_dir = op.dirname(op.join(op.abspath(__file__), '../fdi/schemas'))
    sch_dir = op.join(op.abspath(op.dirname(__file__)), 'resources/schemas')
    sch_path = op.join(sch_dir, 'prd_schema.jsn')
    with open(sch_path, 'r') as file:
        sch = json.load(file)

    from fdi.dataset.baseproduct import BaseProduct
    jsn = json.loads(BaseProduct().serialized())

    store = makeSchemaStore(sch_dir)
    assert getValidator(sch, schema_store=store, base_schema=sch,
                        verbose=1).validate(jsn) is None


def test_true_false(schema_store):
    # load schemas
    sch_True = schema_store[SSP % ('', 'True')]
    sch_False = schema_store[SSP % ('', 'False')]
    # "$ref": "True"  "foo": {"type": "string"} "bar": {"type": "string"}
    use_true = json.loads("""{
        "$id": "https://fdi.schemas/use_true",
        "if": {"$ref": "https://fdi.schemas/True"},
        "then": {
            "required": ["foo"]
        }
    }""")

    # pass
    vtr = getValidator(use_true, verbose=verbose)
    assert not validateJson({"foo": "k", "a": 1}, vtr)
    assert vtr.validate({"foo": "k"}) is None
    # error
    assert validateJson({"food": "k"}, vtr)
    with pytest.raises(ValidationError):
        assert vtr.validate({"food": "k", "a": 2}) is None
    with pytest.raises(ValidationError):
        assert vtr.validate({}) is None

    use_false = json.loads("""{
        "$id": "https://fdi.schemas/use_true",
        "if": {"$ref": "False"},
        "then": {
            "required": ["foo"]
        }
    }""")

    if 0:
        also_run = {
            "$id": "https://fdi.schemas/use_false",
            # "propertyNames": False,
            # "foo": "string",
            "if":
            False,
            "then": {
                "required": ["foo"]
            }
        }

    vtr = getValidator(use_false, verbose=verbose)
    # pass
    assert not validateJson({"foo": "k", "a": 1}, vtr)
    assert vtr.validate({"foo": "k"}) is None

    assert not validateJson({"food": "k"}, vtr)
    assert vtr.validate({"food": "k", "a": 2}) is None
    assert vtr.validate({}) is None


def test_bytes(schema_store):
    scn = 'bytes'
    sch = schema_store[SSP % ('', scn)]
    byts = b'0123456789\x0a\x0b\x0c\x0d\x0e\x0f\x10\xff'
    saved = fdi.dataset.serializable.GZIP
    vtr = getValidator(sch, verbose=verbose)
    try:
        for gzip in [True, False]:
            fdi.dataset.serializable.GZIP = gzip
            for typ in (bytes, bytearray):
                jsn = json.loads(serialize(typ(byts)))
                logger.info(jsn)
                assert vtr.validate(jsn) is None

            if gzip:
                # no valid STID
                bad = {
                    'code': 'H4sIABqX\n', '_S': 'bytes,gz,b64'}
                with pytest.raises(ValidationError):
                    assert vtr.validate(bad) is None
                # invalid _STID
                bad = {
                    'code': 'H4sIABqX\n', '_STID': 'bytes,gz,b64g'}
                with pytest.raises(ValidationError):
                    assert vtr.validate(bad) is None
                # invalid characters not checked
                bad = {'code': 'H4sI!@qX\n', '_STID': 'bytes,gz,b64'}
                # with pytest.raises(ValidationError):
                assert vtr.validate(bad) is None
            else:
                # invalid characters not checked
                bad = {'code': '3031323334350g', '_STID': 'bytes'}
                # with pytest.raises(ValidationError):
                assert vtr.validate(bad) is None
    finally:
        fdi.dataset.serializable.GZIP = saved

    # "example ignores jsn
    check_examples_defaults(vtr, sch, jsn, [
        'examples',
    ])


def test_a_array(schema_store):
    scn = 'a_array'
    sch = schema_store[SSP % ('', scn)]
    byts = b'0123456789\x0a\x0b\x0c\x0d\x0e\x0f'
    vtr = getValidator(sch, verbose=verbose)

    saved = fdi.dataset.serializable.GZIP
    try:
        for gzip in [True, False]:
            fdi.dataset.serializable.GZIP = gzip
            for tcode in ('I', 'H'):
                jsn = json.loads(serialize(array.array(tcode, byts)))
                logger.info(jsn)
                assert vtr.validate(jsn) is None

            if not gzip:
                # bad STID
                bad = {'_STID': '',
                       'code': '303132333435363738390a0b0c0d0e0f'}
                with pytest.raises(ValidationError):
                    assert vtr.validate(bad) is None
    finally:
        fdi.dataset.serializable.GZIP = saved

    # "example ignores jsn
    check_examples_defaults(vtr, sch, jsn, ['examples'])


def test_RQSTID(schema_store):
    """ Test setting requires:['_STID'] with schema "Require_STID".
    """
    scn = 'TEST_STID'
    sch = schema_store[SSP % ('', scn)]

    sch['$ref'] = "Require_STID_True"
    vtr = getValidator(sch, verbose=verbose)
    jsn = {"foo": "bar", "_STID": "byte"}
    assert vtr.validate(jsn) is None
    # error from no _STID
    jsn = {"foo": "bar", "m_STID": "byte"}
    with pytest.raises(ValidationError):
        assert vtr.validate(jsn) is None
    with pytest.raises(ValidationError):
        assert vtr.validate({}) is None

    # pass
    sch['$ref'] = "Require_STID_False"
    vtr = getValidator(sch, verbose=verbose)
    jsn = {"foo": "bar", "_STID": "byte"}
    assert vtr.validate(jsn) is None
    jsn = {"foo": "bar", "m_STID": "byte"}
    assert vtr.validate(jsn) is None
    assert vtr.validate({}) is None


def test_preset_STID(schema_store):

    scn = 'TEST_STID'
    sch = schema_store[SSP % ('', scn)]

    # constant preset _STID
    sch['properties']['_STID'] = {"const": "Foo"}
    vtr = getValidator(sch, verbose=verbose)
    jsn = {"foo": "bar", "_STID": "Foo"}
    assert vtr.validate(jsn) is None
    # wrong STID
    jsn = {"foo": "bar", "_STID": "bytes"}
    with pytest.raises(ValidationError):
        assert vtr.validate(jsn) is None
    # missing
    jsn = {"foo": "bar"}
    with pytest.raises(ValidationError):
        assert vtr.validate(jsn) is None
    # also wrong
    jsn = json.loads('{"foo":"bar", "_STID":"bytes,gz"}')
    with pytest.raises(ValidationError):
        assert vtr.validate(jsn) is None
    # empty
    with pytest.raises(ValidationError):
        assert vtr.validate({}) is None

    # modift schema to have list of possible IDs in preset _STID
    sch['properties']['_STID'] = {"enum": ["bytes", "bytes,gz"]}
    vtr = getValidator(sch, verbose=verbose)
    jsn = {"foo": "bar", "_STID": "bytes,gz"}
    assert vtr.validate(jsn) is None
    jsn = {"foo": "bar", "_STID": "bytes"}
    assert vtr.validate(jsn) is None

    # errors in STID in instane
    jsn = {"foo": "bar", "_STID": "bytes,g"}
    with pytest.raises(ValidationError):
        assert vtr.validate(jsn) is None
    with pytest.raises(ValidationError):
        assert vtr.validate({"_STID": None}) is None

    # Properties is anyOf
    del sch['properties']
    sch["anyOf"] = [
        {'properties': {
            "foo": {"const": "deadbeef"},
            "_STID": {"type": "string", "pattern": "^bytes$"}
        }},
        {'properties': {
            "_STID": {"type": "string", "pattern": "bytes.gz$"}}
         }
    ]

    vtr = getValidator(sch, verbose=verbose)
    jsn = {"foo": "bar", "_STID": "bytes,gz"}
    assert vtr.validate(jsn) is None
    jsn = {"foo": "deadbeef", "_STID": "bytes"}
    assert vtr.validate(jsn) is None

    # error in foo: when STID=='gzip'
    jsn = {"foo": "bar", "_STID": "bytes"}
    with pytest.raises(ValidationError):
        assert vtr.validate(jsn) is None

    # errors in STID in instane
    jsn = {"foo": "bar", "_STID": "bytes,g"}
    with pytest.raises(ValidationError):
        assert vtr.validate(jsn) is None
    with pytest.raises(ValidationError):
        assert vtr.validate({"_STID": None}) is None

    # modify STID to ""
    jsn = {"foo": "bar", "_STID": "g"}
    with pytest.raises(ValidationError):
        assert vtr.validate(jsn) is None


def test_urn(schema_store):
    scn = 'Urn'
    sch = schema_store[SSP % ('pal/', scn)]

    if 1:
        jsn = json.loads(serialize('urn:pool:si.PL:20'))
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_examples_defaults(vtr, sch, jsn, [
                            'examples',
                            ])

    # invalid urn in 'urns'
    cpy = copy.deepcopy(jsn)
    bad = cpy.replace("urn:", "urn::")
    with pytest.raises(ValidationError):
        assert getValidator(sch, verbose=verbose).validate(bad) is None


def test_STID(schema_store):
    scn = 'STID'
    sch = schema_store[SSP % ('', scn)]

    jsn = json.loads(serialize('FineTime'))
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_examples_defaults(vtr, sch, jsn, [
                            'examples',
                            ])

    # invalid
    cpy = copy.deepcopy(jsn)
    bad = cpy.replace("F", "#")
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None
    with pytest.raises(ValidationError):
        assert vtr.validate(None) is None

    # extended


def test_datetime(schema_store):
    scn = 'datetime'
    sch = schema_store[SSP % ('', scn)]

    then = datetime.datetime(
        2019, 2, 19, 1, 2, 3, 456789, tzinfo=timezone.utc)
    jsn = json.loads(serialize(then, indent=4))
    if verbose:
        logger.info(jsn)

    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_general(vtr, jsn, scn)

    # can be None
    assert vtr.validate(None) is None


def test_ListenerSet(schema_store):
    scn = 'ListenerSet'
    sch = schema_store[SSP % ('dataset/', scn)]

    jsn = json.loads(serialize(ListenerSet(), indent=4))
    if verbose:
        logger.info(jsn)

    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_general(vtr, jsn, scn)

    # can be None
    assert vtr.validate(None) is None


def test_FineTime(schema_store):
    scn = 'FineTime'
    sch = schema_store[SSP % ('dataset/', scn)]

    if 1:
        jsn = json.loads(serialize(FineTime(123456789876543)))
    else:
        jsn_path = os.path.join(SCHEMA_TEST_DATA, scn0 + scn + '.jsn')
        with open(jsn_path, 'r') as file:
            jsn = json.load(file)
    # print(jsn)
    vtr = getValidator(sch, verbose=verbose)
    check_general(vtr, jsn, scn)
    check_examples_defaults(vtr, sch, jsn, [
                            'properties.format.examples',
                            'examples',
                            ])

    assert vtr.validate(jsn) is None
    # invalid
    bad = copy.deepcopy(jsn)
    bad['tai'] = 9.9
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None
    bad = copy.deepcopy(jsn)
    bad['format'] = 'd'
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None


def test_xParameter(schema_store):
    scn = 'Parameter'
    sch = schema_store[SSP % ('dataset/', scn)]
    x = Parameter(3.14,
                  description="foo",
                  default=42,
                  valid={3.14: 'ok'},
                  typ_=None)
    jsn = json.loads(serialize(x, indent=4))

    if verbose:
        logger.info(jsn)
    assert jsn['type'] == 'float'
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_general(vtr, jsn, scn)
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
    bad = copy.deepcopy(jsn)
    del bad['value']
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None
    bad = copy.deepcopy(jsn)
    bad['valid'] = 4
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None

    bad = copy.deepcopy(jsn)
    bad['type'] = 'foo'
    with pytest.raises(ValidationError):
        k = vtr.validate(bad)
    bad = copy.deepcopy(jsn)
    bad['valid'] = [[1, 2]]
    vtr.validate(bad) is None
    bad['valid'] = [[1], [1, 2]]
    with pytest.raises(ValidationError):
        vtr.validate(bad) is None
    # logger.warning(str(vtr.validate(bad)))


def test_BooleanParameter(schema_store):
    scn = 'BooleanParameter'
    sch = schema_store[SSP % ('dataset/', scn)]

    if 1:
        jsn = json.loads(serialize(BooleanParameter(True,
                                                    description="foo?",
                                                    default=None,
                                                    ),
                                   indent=4))
    if verbose:
        logger.info(jsn)
    assert jsn['type'] == 'boolean'
    assert jsn['default'] is None
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_general(vtr, jsn, scn)
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
    bad = copy.deepcopy(jsn)
    bad['type'] = 3
    bad['value'] = 'd'
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None


def test_StringParameter(schema_store):
    scn = 'StringParameter'
    sch = schema_store[SSP % ('dataset/', scn)]

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

    check_general(vtr, jsn, scn)
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
    bad = copy.deepcopy(jsn)
    bad['type'] = 3
    bad['value'] = 'd'
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None


def test_NumericParameter(schema_store):
    scn = 'NumericParameter'
    sch = schema_store[SSP % ('dataset/', scn)]

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

    check_general(vtr, jsn, scn)
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

    # invalid
    bad = copy.deepcopy(jsn)
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
    sch_para = schema_store[SSP % ('dataset/', 'Parameter')]
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

    # Vector


def test_Vector(schema_store):
    scn = 'Vector'
    sch = schema_store[SSP % ('dataset/', scn)]

    if 1:
        jsn = json.loads(serialize(Vector((3.14, 5, 0xb),
                                          typecode='f',
                                          unit='au'),
                                   indent=4)
                         )
    if verbose:
        logger.info(jsn)
    assert jsn['unit'] == 'au'
    assert jsn['typecode'] == 'f'
    vtr = getValidator(sch, verbose=verbose)

    check_general(vtr, jsn, scn)
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

    # invalid
    bad = copy.deepcopy(jsn)
    bad['typecode'] = 3
    bad['value'] = 'd'
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None


def test_DateParameter(schema_store):
    scn = 'DateParameter'
    sch = schema_store[SSP % ('dataset/', scn)]
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

    check_general(vtr, jsn, scn)
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
    bad = copy.deepcopy(jsn)
    bad['value'] = {"foo": 4}
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None
    bad = copy.deepcopy(jsn)
    bad['typecode'] = 3
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None
    bad = copy.deepcopy(jsn)
    bad['value'] = 'd'
    with pytest.raises(ValidationError):
        assert vtr.validate(bad) is None


def test_MetaData(schema_store):
    scn = 'MetaData'
    sch = schema_store[SSP % ('dataset/', scn)]

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
    check_general(vtr, jsn, scn)


def test_Dataset(schema_store):
    scn = 'Dataset'
    sch = schema_store[SSP % ('dataset/', scn)]

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

    check_general(vtr, jsn, scn)


def test_ArrayDataset(schema_store):
    scn = 'ArrayDataset'
    sch = schema_store[SSP % ('dataset/', scn)]

    for atype in (list, bytes):

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

        jsn = json.loads(serialize(v))

        if verbose:
            logger.info("JSON instance to test: %s" %
                        lls(pformat(jsn, indent=4), 2000))
        # assert jsn['default']['tai'] == 99
        # assert jsn['typecode'] == tc == "%Y-%m-%dT%H:%M:%S.%f"
        vtr = getValidator(sch, verbose=verbose)
        assert vtr.validate(jsn) is None

        check_general(vtr, jsn, scn)

    # subclasses


def test_Column(schema_store):

    scn = 'Column'
    sch = schema_store[SSP % ('dataset/', scn)]
    v = Column(data=[4, 9], unit='m')
    jsn = json.loads(serialize(v))

    if verbose:
        logger.info("JSON instance to test: %s" %
                    lls(pformat(jsn, indent=4), 2000))
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_general(vtr, jsn, scn)


im_svg = '<svg aria-hidden="true" data-prefix="far" data-icon="copy" class="svg-inline--fa fa-copy fa-w-14" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path fill="#777" d="M433.941 65.941l-51.882-51.882A48 48 0 0 0 348.118 0H176c-26.51 0-48 21.49-48 48v48H48c-26.51 0-48 21.49-48 48v320c0 26.51 21.49 48 48 48h224c26.51 0 48-21.49 48-48v-48h80c26.51 0 48-21.49 48-48V99.882a48 48 0 0 0-14.059-33.941zM266 464H54a6 6 0 0 1-6-6V150a6 6 0 0 1 6-6h74v224c0 26.51 21.49 48 48 48h96v42a6 6 0 0 1-6 6zm128-96H182a6 6 0 0 1-6-6V54a6 6 0 0 1 6-6h106v88c0 13.255 10.745 24 24 24h88v202a6 6 0 0 1-6 6zm6-256h-64V48h9.632c1.591 0 3.117.632 4.243 1.757l48.368 48.368a6 6 0 0 1 1.757 4.243V112z"></path></svg>'


def test_MediaWrapper(schema_store):

    scn = 'MediaWrapper'
    sch = schema_store[SSP % ('dataset/', scn)]
    v = MediaWrapper(data=im_svg,
                     description='copybutton in svg',
                     typ_='image/svg'
                     )
    _s = serialize(v)

    jsn = json.loads(_s)

    if verbose:
        logger.info("JSON instance to test: %s" %
                    lls(pformat(jsn, indent=4), 2000))
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_general(vtr, jsn, scn)


def test_TableDataset(schema_store):
    scn = 'TableDataset'
    sch = schema_store[SSP % ('dataset/', scn)]

    v = demo_TableDataset()

    # v.meta = MetaData(description='test TableDataset.MEtadata')
    # v.data = 987.4

    jsn = json.loads(serialize(v))

    if 1 or verbose:
        logger.info("JSON instance to test: %s" %
                    lls(pformat(jsn, indent=4), 2000))
    # assert jsn['default']['tai'] == 99
    # assert jsn['typecode'] == tc == "%Y-%m-%dT%H:%M:%S.%f"
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None
    check_general(vtr, jsn, scn)


def test_CompositeDataset(schema_store):
    scn = 'CompositeDataset'
    sch = schema_store[SSP % ('dataset/', scn)]

    if 0:
        v = CompositeDataset(description="tester CompositeDataset",
                             data=[('col1', [1, 4.4, 5.4E3], 'eV'),
                                   ('col2', [0, 43.2, 2E3], 'cnt')
                                   ])
    v = demo_CompositeDataset()

    # v.meta = MetaData(description='test CompositeDataset.MEtadata')
    # v.data = 987.4

    jsn = json.loads(serialize(v))

    if 1 or verbose:
        logger.info("JSON instance to test: %s" %
                    lls(pformat(jsn, indent=4), 2000))
    # assert jsn['default']['tai'] == 99
    # assert jsn['typecode'] == tc == "%Y-%m-%dT%H:%M:%S.%f"
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_general(vtr, jsn, scn)


def test_UnstructuredDataset(schema_store):
    scn = 'UnstructuredDataset'
    sch = schema_store[SSP % ('dataset/', scn)]

    v = UnstructuredDataset()

    p = demo_CompositeDataset()
    v.put(p.serialized(), 'json')

    # v.meta = MetaData(description='test UnstructuredDataset.MEtadata')
    # v.data = 987.4

    jsn = json.loads(serialize(v))

    if 1 or verbose:
        logger.info("JSON instance to test: %s" %
                    lls(pformat(jsn, indent=4), 2000))
    # assert jsn['default']['tai'] == 99
    # assert jsn['typecode'] == tc == "%Y-%m-%dT%H:%M:%S.%f"
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_general(vtr, jsn, scn)


def test_History(schema_store):
    scn = 'History'
    sch = schema_store[SSP % ('dataset/', scn)]

    # p = get_demo_product()

    v = History()
    dt = datetime.datetime(
        2019, 2, 19, 1, 2, 3, 456789, tzinfo=timezone.utc)
    v.add_input(args={'id': 1, 'width': 2.33, 'name': 'asd',
                      'ok': True, 'speed': [4, 5],
                      'scores': array.array('f', [6, 7]),
                      'and': None, 'a': 'b', 'c': [11],
                      'dt': dt
                      },
                info=dict(c='d')
                )

    # odd ball
    parray = v.meta['scores']
    assert parray.value == array.array('f', [6, 7])
    sparray = json.loads(serialize(parray))
    pasc = schema_store[SSP % ('dataset/', 'Parameter')]
    tor = getValidator(pasc, verbose=verbose)
    res=tor.validate(sparray)
    assert res is None

    jsn = json.loads(serialize(v))

    if 1 or verbose:
        logger.info("JSON instance to test: %s" %
                    lls(pformat(jsn, indent=4), 2000))

    # assert jsn['default']['tai'] == 99
    # assert jsn['typecode'] == tc == "%Y-%m-%dT%H:%M:%S.%f"
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_general(vtr, jsn, scn)


def test_BaseProduct(schema_store):
    scn = 'BaseProduct'
    sch = schema_store[SSP % ('dataset/', scn)]

    # p = get_demo_product()

    v = BaseProduct(description='tester Base')
    i0 = 6
    i1 = [[1, 2, 3], [4, 5, i0], [7, 8, 9]]
    i2 = 'ev'                 # unit
    i3 = 'img1'  # description
    image = ArrayDataset(data=i1, unit=i2, description=i3)

    v["RawImage"] = image
    v.set('QualityImage', ArrayDataset(
        [[0.1, 0.5, 0.7], [4e3, 6e7, 8], [-2, 0, 3.1]]))
    # add a tabledataset
    s1 = [('col1', [1, 4.4, 5.4E3], 'eV'),
          ('col2', [0, 43.2, 2E3], 'cnt')
          ]
    spec = TableDataset(data=s1)
    v["Spectrum"] = spec

    # v.meta = MetaData(description='test BaseProduct.MEtadata')
    # v.data = 987.4

    jsn = json.loads(serialize(v))

    if 1 or verbose:
        logger.info("JSON instance to test: %s" %
                    lls(pformat(jsn, indent=4), 2000))
    # assert jsn['default']['tai'] == 99
    # assert jsn['typecode'] == tc == "%Y-%m-%dT%H:%M:%S.%f"
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_general(vtr, jsn, scn)


def test_MapContext(schema_store):
    scn = 'MapContext'
    sch = schema_store[SSP % ('dataset/', scn)]

    v = MapContext(description='MapContext demo')
    r = ProductRef(v)
    v.refs['self'] = r
    v['arr']=ArrayDataset([6,4,2])

    jsn = json.loads(serialize(v))

    if verbose:
        logger.info("JSON instance to test: %s" %
                    lls(pformat(jsn, indent=4), 2000))
    # assert jsn['default']['tai'] == 99
    # assert jsn['typecode'] == tc == "%Y-%m-%dT%H:%M:%S.%f"
    vtr = getValidator(sch, verbose=verbose)
    assert vtr.validate(jsn) is None

    check_general(vtr, jsn, scn)


def XXXtest_all(schema_store):

    all_cls = Classes.mapping
    all_schemas = list(schema_store)
    validator_list = {}
    for c_name, c_class in all_cls.items():
        if c_name == 'Serializable':
            continue
        if isinstance(c_class, type) and issubclass(c_class, Serializable):
            jsn = json.loads(serialize(c_class()))
            for sch_name, sch in schema_store.items():
                if c_name in sch_name:
                    logger.info('Found class %s for schema %s.' %
                                (c_name, sch_name))
                    if sch_name not in validator_list:
                        validator_list[sch_name] = getValidator(
                            sch, verbose=verbose)
                    assert validator_list[sch_name].validate(jsn) is None

    sch = schema_store[SSP % ('dataset/', scn)]

    v = get_demo_product()

    # v.meta = MetaData(description='test MapContext.MEtadata')
    # v.data = 987.4

    jsn = json.loads(serialize(v))


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
