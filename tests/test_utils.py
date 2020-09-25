# -*- coding: utf-8 -*-

import datetime
import traceback
import copy
import sys
import os
import pdb

from fdi.dataset.annotatable import Annotatable
from fdi.dataset.copyable import Copyable
from fdi.dataset.odict import ODict
from fdi.dataset.eq import deepcmp
from fdi.dataset.classes import Classes
from fdi.dataset.deserialize import deserializeClassID
from fdi.dataset.quantifiable import Quantifiable
from fdi.dataset.listener import EventSender, DatasetBaseListener, EventTypes, EventType, EventTypeOf
from fdi.dataset.composite import Composite
from fdi.dataset.metadata import Parameter, NumericParameter, MetaData, ParameterTypes, ParameterDataTypes, StringParameter, DateParameter
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
from fdi.utils.checkjson import checkjson
from fdi.utils.loadfiles import loadcsv
from fdi.utils import moduleloader

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
    # pdb.set_trace()
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
