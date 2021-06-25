# -*- coding: utf-8 -*-

# Automatically generated from fdi/dataset/resources/BaseProduct.yml. Do not edit.

from collections import OrderedDict
from fdi.dataset.finetime import FineTime


from fdi.dataset.readonlydict import ReadOnlyDict
from fdi.dataset.serializable import Serializable
from fdi.dataset.abstractcomposite import AbstractComposite
from fdi.dataset.listener import EventSender, EventType
from fdi.dataset.eq import deepcmp
from fdi.dataset.copyable import Copyable
from fdi.dataset.history import History

from collections import OrderedDict
import itertools

import logging
# create logger
logger = logging.getLogger(__name__)


class BaseProduct( AbstractComposite, Copyable, Serializable,  EventSender):
    """ A BaseProduct is the starting point of te whole  product tree, and a generic result that can be passed on between processes.

    In general a Product contains zero or more datasets, history,
    optional reference pointers and metadata some required metadata fields.
    A Product is expected to fully describe itself; this includes
    the way how this product was achieved (its history). As it is
    the result of a process, it should be able to save to and restore
    from an Archive device.

    Many times a Product may contain a single dataset and for this
    purpose the first dataset entry can be accessed by the getDefault()
    method. Note that the datasets may be a composite of datasets
    by themselves.

    A built-in attributes in `Model['metadata']` ("MetaData Parameter" or `MDP`) can be accessed with e.g. ``p.creator``, or p.meta['creator'].value::

        p.creator='foo'
    	assert p.creatur=='foo'
    	assert p.meta['creator']=='foo'
    	p.meta['creator']=Parameter('bar')
    	assert p.meta['creator']==Parameter('bar')

    =====
    BaseProduct class schema 1.6 inheriting [None].

Automatically generated from fdi/dataset/resources/BaseProduct.yml on 2021-06-18 16:19:33.951506.

Description:
FDI base class data model

    """

    def __init__(self,
                 description = 'UNKNOWN',
                 typ_ = 'BaseProduct',
                 level = 'ALL',
                 creator = 'UNKNOWN',
                 creationDate = FineTime(0),
                 rootCause = 'UNKNOWN',
                 version = '0.8',
                 FORMATV = '1.6.0.10',
                 zInfo=None,
                 **kwds):

        # collect MDPs from args-turned-local-variables.
        metasToBeInstalled = OrderedDict(
            itertools.filterfalse(
                lambda x: x[0] in ('self', '__class__', 'zInfo', 'kwds'),
                locals().items())
        )

        global Model
	# instance variable for Model to be passed down inhritance chains.
        if zInfo is None:
            zInfo = Model

        # must be the first line to initiate meta and zInfo
        # :class: `Attributable` will process MDPs
        super().__init__(zInfo=zInfo, **metasToBeInstalled, **kwds)

        self._history = History()


    @property
    def history(self):
        """ xx must be a property for ``self.xx = yy`` to work in super class after xx is set as a property also by a subclass.
        """
        return self._history

    @history.setter
    def history(self, history):
        self._history = history

    def accept(self, visitor):
        """ Hook for adding functionality to meta data object
        through visitor pattern."""
        visitor.visit(self)

    def getDefault(self):
        """ Convenience method that returns the first dataset \
        belonging to this product. """
        return list(self._sets.values())[0] if len(self._sets) > 0 else None



    def targetChanged(self, event):
        pass
        if event.source == self.meta:
            if event.type_ == EventType.PARAMETER_ADDED or \
               event.type_ == EventType.PARAMETER_CHANGED:
                # logger.debug(event.source.__class__.__name__ +   ' ' + str(event.change))
                pass

    def toString(self, level=0,
                 tablefmt='rst', tablefmt1='simple', tablefmt2='simple',
                 matprint=None, trans=True, beforedata='', **kwds):
        """ like AbstractComposite but with history
        """
        h = self.history.toString(
            level=level,
            tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
	    matprint=matprint, trans=trans, **kwds)
        s = super(BaseProduct, self).toString(
            level=level,
            tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
	    matprint=matprint, trans=trans, beforedata=h, **kwds)
        return s


    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        if 0:
            # remove self from meta's listeners because the deserialzed product will add itself during instanciation.
            print('1###' + self.meta.toString())
            metac = self.meta.copy()
            print('***' + metac.toString())
            print(deepcmp(self, metac.listeners[0]))
            metac.removeListener(self)

        ls = [
            ("meta", self.meta),
            ("_sets", self._sets if hasattr(self, '_sets') else None),
            ("history", self._history if hasattr(self, '_history') else None),
            ("listeners", self._listeners if hasattr(self, '_history') else None),
            ("_STID", self._STID if hasattr(self, '_STID') else None),
        ]

        return OrderedDict(ls)

    @property
    def description(self): pass
    @property
    def type(self): pass
    @property
    def level(self): pass
    @property
    def creator(self): pass
    @property
    def creationDate(self): pass
    @property
    def rootCause(self): pass
    @property
    def version(self): pass
    @property
    def FORMATV(self): pass
    pass

# Data Model specification for mandatory components
_Model_Spec = {
    'name': 'BaseProduct',
    'description': 'FDI base class data model',
    'parents': [
        None,
        ],
    'schema': '1.6',
    'metadata': {
        'description': {
                'id_zh_cn': '描述',
                'data_type': 'string',
                'description': 'Description of this product',
                'description_zh_cn': '对本产品的描述。',
                'default': 'UNKNOWN',
                'valid': '',
                'typecode': 'B',
                },
        'type': {
                'id_zh_cn': '产品类型',
                'data_type': 'string',
                'description': 'Product Type identification. Name of class or CARD.',
                'description_zh_cn': '产品类型。完整Python类名或卡片名。',
                'default': 'BaseProduct',
                'valid': '',
                'typecode': 'B',
                },
        'level': {
                'id_zh_cn': '产品xx',
                'data_type': 'string',
                'description': 'Product level.',
                'description_zh_cn': '产品xx',
                'default': 'ALL',
                'valid': '',
                'typecode': 'B',
                },
        'creator': {
                'id_zh_cn': '本产品生成者',
                'data_type': 'string',
                'description': 'Generator of this product.',
                'description_zh_cn': '本产品生成方的标识，例如可以是单位、组织、姓名、软件、或特别算法等。',
                'default': 'UNKNOWN',
                'valid': '',
                'typecode': 'B',
                },
        'creationDate': {
                'id_zh_cn': '产品生成时间',
                'fits_keyword': 'DATE',
                'data_type': 'finetime',
                'description': 'Creation date of this product',
                'description_zh_cn': '本产品生成时间',
                'default': 0,
                'valid': '',
                'typecode': None,
                },
        'rootCause': {
                'id_zh_cn': '数据来源',
                'data_type': 'string',
                'description': 'Reason of this run of pipeline.',
                'description_zh_cn': '数据来源（此例来自鉴定件热真空罐）',
                'default': 'UNKNOWN',
                'valid': '',
                'typecode': 'B',
                },
        'version': {
                'id_zh_cn': '版本',
                'data_type': 'string',
                'description': 'Version of product',
                'description_zh_cn': '产品版本',
                'default': '0.8',
                'valid': '',
                'typecode': 'B',
                },
        'FORMATV': {
                'id_zh_cn': '格式版本',
                'data_type': 'string',
                'description': 'Version of product schema and revision',
                'description_zh_cn': '产品格式版本',
                'default': '1.6.0.10',
                'valid': '',
                'typecode': 'B',
                },
        },
    'datasets': {
        },
    }

Model = ReadOnlyDict(_Model_Spec)

MdpInfo = Model['metadata']

