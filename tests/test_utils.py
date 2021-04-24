# -*- coding: utf-8 -*-

import datetime
import traceback
import copy
import sys
import os

from fdi.dataset.annotatable import Annotatable
from fdi.dataset.copyable import Copyable
from fdi.dataset.odict import ODict
from fdi.dataset.eq import deepcmp
from fdi.dataset.classes import Classes
from fdi.dataset.deserialize import deserialize
from fdi.dataset.quantifiable import Quantifiable
from fdi.dataset.listener import EventSender, DatasetBaseListener, EventTypes, EventType, EventTypeOf
from fdi.dataset.composite import Composite
from fdi.dataset.metadata import Parameter, NumericParameter, MetaData, StringParameter, DateParameter, make_jsonable
from fdi.dataset.datatypes import DataTypes, DataTypeNames
from fdi.dataset.attributable import Attributable
from fdi.dataset.abstractcomposite import AbstractComposite
from fdi.dataset.datawrapper import DataWrapper, DataWrapperMapper
from fdi.dataset.dataset import ArrayDataset, TableDataset, CompositeDataset, Column
from fdi.dataset.ndprint import ndprint
from fdi.dataset.datatypes import Vector, Quaternion
from fdi.dataset.finetime import FineTime, FineTime1, utcobj
from fdi.dataset.history import History
from fdi.dataset.baseproduct import BaseProduct
from fdi.dataset.product import Product
from fdi.pal.urn import Urn
from fdi.utils.checkjson import checkjson
from fdi.utils.loadfiles import loadcsv
from fdi.utils import moduleloader
from fdi.utils.common import fullname, l2t
from fdi.utils.options import opt
from fdi.utils.fetch import fetch

# import __builtins__


if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
else:
    PY3 = False

Classes.updateMapping()

if __name__ == '__main__' and __package__ == 'tests':
    # run by python -m tests.test_dataset

    from outputs import nds2, nds3, out_TableDataset, out_CompositeDataset
else:
    # run by pytest

    # This is to be able to test w/ or w/o installing the package
    # https://docs.python-guide.org/writing/structure/
    from .pycontext import fdi

    from .outputs import nds2, nds3, out_TableDataset, out_CompositeDataset

    from .logdict import logdict
    import logging
    import logging.config
    # create logger
    logging.config.dictConfig(logdict)
    logger = logging.getLogger()
    logger.debug('%s logging level %d' %
                 (__name__, logger.getEffectiveLevel()))


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


def get_sample_product():
    """
    """
    compo = CompositeDataset()
    # two arraydsets
    a1 = [768, 4.4, 5.4E3]
    a2 = 'ev'
    a3 = 'arraydset 1'
    a4 = ArrayDataset(data=a1, unit=a2, description=a3)
    a5, a6, a7 = [[1.09, 289], [3455, 564]
                  ], 'count', 'background -- arraydset in compo'
    a8 = ArrayDataset(data=a5, unit=a6, description=a7)
    a10 = 'calibration_arraydset'
    compo.set(a10, a8)
    # a tabledataset
    ELECTRON_VOLTS = 'eV'
    SECONDS = 'sec'
    t = [x * 1.0 for x in range(5)]
    e = [2 * x + 100 for x in t]
    x = TableDataset(description="Example table")
    x["Time"] = Column(data=t, unit=SECONDS)
    x["Energy"] = Column(data=e, unit=ELECTRON_VOLTS)
    # set a tabledataset ans an arraydset, with a parameter in metadata
    a13 = 'energy_table'
    # metadata to the dataset
    compo[a13] = x
    a11 = 'm1'
    a12 = StringParameter('EX')
    compo.meta[a11] = a12

    prodx = Product('complex prod')
    prodx.meta['extra'] = NumericParameter(description='a different param in metadata',
                                           value=Vector((1.1, 2.2, 3.3)), valid={(1, 22): 'normal', (30, 33): 'fast'}, unit='meter')
    prodx[a3] = a4
    prodx['results'] = compo

    return prodx


def test_fetch():

    # simple nested structure
    v = {1: 2, 3: 4}
    u, s = fetch([3], v)
    assert u == 4
    assert s == '[3]'
    v = {'1': 2, 3: 4}
    u, s = fetch(['1'], v)
    assert u == 2
    assert s == '["1"]'
    v.update(d={'k': 99})
    u, s = fetch(['d', 'k'], v)
    assert u == 99
    assert s == '["d"]["k"]'

    # objects
    class al(list):
        ala = 0
        def alb(): pass

        def __init__(self, *a, i=[8], **k):
            super().__init__(*a, **k)
            self.ald = i
        alc = {3: 4}
        ale = [99, 88]

    v = al(i=[1, 2])
    u, s = fetch(['ald'], v)
    assert u == [1, 2]
    assert s == '.ald'

    u, s = fetch(['ale', 1], v)
    assert u == 88
    assert s == '.ale[1]'

    class ad(dict):
        ada = 'p'
        adb = al([0, 6])

    v = ad(z=5, x=['b', 'n', {'m': 'j'}])
    v.ade = 'adee'

    u, s = fetch(['ada'], v)
    assert u == 'p'
    assert s == '.ada'

    u, s = fetch(['adb', 'ald', 0], v)
    assert u == 8
    assert s == '.adb.ald[0]'

    u, s = fetch(['x', 2, 'm'], v)
    assert u == 'j'
    assert s == '["x"][2]["m"]'

    # products
    p = get_sample_product()
    v, s = fetch(["description"], p)
    assert v == p.description
    assert s == '.description'
    # metadata
    e = p.meta['extra']
    v, s = fetch(["meta", "extra"], p)
    assert v == p.meta['extra']
    assert s == '.meta["extra"]'
    # parameter
    v, s = fetch(["meta", "extra", "unit"], p)
    assert v == 'meter'
    assert v == p.meta['extra'].unit
    assert s == '.meta["extra"].unit'

    v, s = fetch(["meta", "extra", "value"], p)
    assert v == Vector((1.1, 2.2, 3.3))
    assert v == p.meta['extra'].value
    assert s == '.meta["extra"].value'
    v, s = fetch(["meta", "extra", "valid"], p)
    mkj = make_jsonable({(1, 22): 'normal', (30, 33): 'fast'})
    assert v == mkj
    assert v == make_jsonable(p.meta['extra'].valid)
    assert s == '.meta["extra"].valid'
    # TODO written is string
    # [[[1, 22], 'normal'], [[30, 33], 'fast']]
    v, s = fetch(["meta", "extra", "valid", 0, 1], p)
    assert v == 'normal'
    assert v == p.meta['extra'].valid[0][1]
    assert s == '.meta["extra"].valid[0][1]'
    #
    # validate execution
    v, s = fetch(["meta", "extra", "isValid", ], p)
    assert v == True
    assert v == p.meta['extra'].isValid()
    assert s == '.meta["extra"].isValid()'
    # datasets
    v, s = fetch(["arraydset 1", "unit"], p)
    assert v == 'ev'
    assert v == p['arraydset 1'].unit
    assert s == '["arraydset 1"].unit'

    v, s = fetch(["arraydset 1", "data"], p)
    assert v == [768, 4.4, 5.4E3]
    assert v == p['arraydset 1'].data
    assert s == '["arraydset 1"].data'

    # data of a column in tabledataset within compositedataset
    v, s = fetch(["results", "energy_table", "Energy", "data"], p)
    t = [x * 1.0 for x in range(5)]
    assert v == [2 * x + 100 for x in t]
    assert v == p['results']['energy_table']['Energy'].data
    assert s == '["results"]["energy_table"]["Energy"].data'
    # another dataset in compositedataset 'results'
    v, s = fetch(["results", 'calibration_arraydset', "unit"], p)
    assert v == 'count'
    assert v == p['results']['calibration_arraydset'].unit
    assert s == '["results"]["calibration_arraydset"].unit'


def test_loadcsv():
    csvf = '/tmp/testloadcsv.csv'
    a = 'as if ...'
    with open(csvf, 'w') as f:
        f.write(a)
    v = loadcsv(csvf, ' ')
    assert v[0] == ('col1', ['as'], '')
    assert v[1] == ('col2', ['if'], '')
    assert v[2] == ('col3', ['...'], '')

    a = ' \t\n'+a
    with open(csvf, 'w') as f:
        f.write(a)
    v = loadcsv(csvf, ' ')
    assert v[0] == ('col1', ['as'], '')
    assert v[1] == ('col2', ['if'], '')
    assert v[2] == ('col3', ['...'], '')

    # blank line skipped
    a = a + '\n1 2. 3e3'
    with open(csvf, 'w') as f:
        f.write(a)
    v = loadcsv(csvf, ' ')
    assert v[0] == ('col1', ['as', 1.0], '')
    assert v[1] == ('col2', ['if', 2.0], '')
    assert v[2] == ('col3', ['...', 3000.], '')

    # first line as header

    v = loadcsv(csvf, ' ', header=1)
    assert v[0] == ('as', [1.0], '')
    assert v[1] == ('if', [2.0], '')
    assert v[2] == ('...', [3000.], '')

    # a mixed line added. delimiter changed to ','
    a = 'as, if, ...\nm, 0.2,ev\n1, 2., 3e3'
    with open(csvf, 'w') as f:
        f.write(a)
    v = loadcsv(csvf, ',', header=1)
    assert v[0] == ('as', ['m', 1.0], '')
    assert v[1] == ('if', ['0.2', 2.0], '')
    assert v[2] == ('...', ['ev', 3000.], '')

    # anothrt line added. two header lines requested -- second line taken as unit line
    a = 'as, if, ...\n A, B, R \n m, 0.2,ev\n1, 2., 3e3'
    with open(csvf, 'w') as f:
        f.write(a)
    v = loadcsv(csvf, ',', header=2)
    assert v[0] == ('as', ['m', 1.0], 'A')
    assert v[1] == ('if', ['0.2', 2.0], 'B')
    assert v[2] == ('...', ['ev', 3000.], 'R')


def test_moduleloader():

    moduleloader.main(ipath=os.path.abspath('tests'))


def test_fullname():
    assert fullname(Urn()) == 'fdi.pal.urn.Urn'
    assert fullname(Urn) == 'fdi.pal.urn.Urn'
    assert fullname('l') == 'str'


def test_opt():
    options = [
        {'long': 'helpme', 'char': 'h', 'default': False,
         'description': 'print help'},
        {'long': 'name=', 'char': 'n', 'default': 'Boo',
         'description': 'name of ship'},
        {'long': 'verbose', 'char': 'v', 'default': True,
         'description': 'print info'}
    ]
    # no args. defaults returned
    out = opt(options, [])
    assert out[0]['result'] == False
    assert out[1]['result'] == 'Boo'
    assert out[2]['result'] == True

    assert options[1]['long'] == 'name='

    # options given in short format
    out = opt(options, ['exe', '-h', '-n Awk', '-v'])
    assert out[0]['result'] == True
    # leading and trailing white spaces in args are removed
    assert out[1]['result'] == 'Awk'
    # the switch always results in True!
    assert out[2]['result'] == True

    # options given in long format
    out = opt(options, ['exe', '--helpme', '--name=Awk', '--verbose'])
    assert out[0]['result'] == True
    assert out[1]['result'] == 'Awk'
    # the switch always results in True!
    assert out[2]['result'] == True

    # type of result is determines by that of the default
    options[0]['default'] = 0
    out = opt(options, ['exe', '--helpme', '--name=Awk', '--verbose'])
    assert out[0]['result'] == 1

    # unplanned option and '--help' get exception and exits
    try:
        out = opt(options, ['exe', '--helpme', '--name=Awk', '-y'])
    except SystemExit:
        pass
    else:
        assert 0, 'failed to exit.'

    try:
        h = copy.copy(options)
        h[0]['long'] = 'help'
        out = opt(h, ['exe', '--help', '--name=Awk', '-v'])
    except SystemExit:
        pass
    else:
        assert 0, 'failed to exit.'
