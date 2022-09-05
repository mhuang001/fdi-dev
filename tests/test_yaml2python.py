# -*- coding: utf-8 -*-

from fdi.dataset.yaml2python import read_yaml
import os.path as op
import datetime
import fractions
import decimal
import traceback
from pprint import pprint
import copy
import json
import sys
import threading
import functools
import time
import locale
import array
from math import sqrt
from datetime import timezone
import pytest

from fdi.dataset.annotatable import Annotatable
from fdi.dataset.copyable import Copyable
from fdi.dataset.odict import ODict
from fdi.dataset.eq import deepcmp
from fdi.dataset.classes import Classes
from fdi.dataset.serializable import serialize
from fdi.dataset.deserialize import deserialize
from fdi.dataset.quantifiable import Quantifiable
from fdi.dataset.listener import EventSender, EventTypes, EventType, EventTypeOf, MetaDataListener, EventListener
from fdi.dataset.messagequeue import MqttRelayListener, MqttRelaySender
from fdi.dataset.composite import Composite
from fdi.dataset.metadata import Parameter, MetaData, make_jsonable
from fdi.dataset.metadataholder import MetaDataHolder
from fdi.dataset.numericparameter import NumericParameter, BooleanParameter
from fdi.dataset.stringparameter import StringParameter
from fdi.dataset.dateparameter import DateParameter
from fdi.dataset.datatypes import DataTypes, DataTypeNames
from fdi.dataset.attributable import Attributable
from fdi.dataset.abstractcomposite import AbstractComposite
from fdi.dataset.datawrapper import DataWrapper, DataWrapperMapper
from fdi.dataset.arraydataset import ArrayDataset, Column
from fdi.dataset.mediawrapper import MediaWrapper
from fdi.dataset.tabledataset import TableDataset
from fdi.dataset.dataset import Dataset, CompositeDataset
from fdi.dataset.indexed import Indexed
from fdi.dataset.ndprint import ndprint
from fdi.dataset.datatypes import Vector, Vector2D, Quaternion
from fdi.dataset.invalid import INVALID
from fdi.dataset.finetime import FineTime, FineTime1
from fdi.dataset.history import History
from fdi.dataset.baseproduct import BaseProduct
from fdi.dataset.product import Product
from fdi.dataset.browseproduct import BrowseProduct
from fdi.dataset.readonlydict import ReadOnlyDict
from fdi.dataset.unstructureddataset import UnstructuredDataset
from fdi.dataset.testproducts import SP, get_demo_product
from fdi.utils.checkjson import checkjson
from fdi.utils.loadfiles import loadMedia
from fdi.utils.ydump import ydump

from jsonpath_ng.parser import JsonPathParserError


if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
else:
    PY3 = False

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# make format output in /tmp/outputs.py
mk_outputs = 0
output_write = 'tests/outputs.py'

if mk_outputs:
    with open(output_write, 'wt', encoding='utf-8') as f:
        f.write('# -*- coding: utf-8 -*-\n')

if __name__ == '__main__' and __package__ is None:
    # run by python3 tests/test_dataset.py

    if not mk_outputs:
        from outputs import nds2, nds3, out_Dataset, out_ArrayDataset, out_TableDataset, out_CompositeDataset, out_FineTime, out_MetaData
else:
    # run by pytest

    # This is to be able to test w/ or w/o installing the package
    # https://docs.python-guide.org/writing/structure/
    #from pycontext import fdi
    import fdi
    if not mk_outputs:
        from outputs import nds2, nds3, out_Dataset, out_ArrayDataset, out_TableDataset, out_CompositeDataset, out_FineTime, out_MetaData

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

    logging.getLogger("requests").setLevel(logging.WARN)
    logging.getLogger("urllib3").setLevel(logging.WARN)
    logging.getLogger("filelock").setLevel(logging.WARN)


def test_read_yaml():
    resrc_dir = op.join(op.abspath(op.dirname(__file__)), 'resources')
    descriptor, input_files = read_yaml(resrc_dir, verbose=False)

    pprint(descriptor)
