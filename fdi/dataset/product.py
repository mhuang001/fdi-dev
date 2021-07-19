# -*- coding: utf-8 -*-

# Automatically generated from fdi/dataset/resources/Product.yml. Do not edit.

from collections import OrderedDict
from fdi.dataset.baseproduct import BaseProduct
from fdi.dataset.finetime import FineTime


from fdi.dataset.readonlydict import ReadOnlyDict

import itertools

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Product(BaseProduct):
    """ Product class schema 1.6 inheriting ['BaseProduct'].

Automatically generated from fdi/dataset/resources/Product.yml on 2021-06-18 16:19:33.999904.

Description:
Project level product

    Generally a Product (inheriting BaseProduct) has project-wide attributes and can be extended to define a plethora of specialized products.
    """


    def __init__(self,
                 description = 'UNKNOWN',
                 typ_ = 'Product',
                 level = 'ALL',
                 creator = 'UNKNOWN',
                 creationDate = FineTime(0),
                 rootCause = 'UNKNOWN',
                 version = '0.8',
                 FORMATV = '1.6.0.10',
                 startDate = FineTime(0),
                 endDate = FineTime(0),
                 instrument = 'UNKNOWN',
                 modelName = 'UNKNOWN',
                 mission = '_AGS',
                 zInfo=None,
                 **kwds):
        """ Initializes instances with more metadata as attributes, set to default values.

        Put description keyword argument here to allow e.g. BaseProduct("foo") and description='foo'
        """

        # collect MDPs from args-turned-local-variables.
        metasToBeInstalled = OrderedDict(
            itertools.filterfalse(
                lambda x: x[0] in ('self', '__class__', 'zInfo', 'kwds'),
                locals().items())
        )

        global Model
        if zInfo is None:
            zInfo = Model

        # print('@1 zInfo', id(self.zInfo['metadata']), id(self), id(self.zInfo),
        #      self.zInfo['metadata']['version'], list(metasToBeInstalled.keys()))

        # must be the first line to initiate meta
        super().__init__(zInfo=zInfo, **metasToBeInstalled, **kwds)

        #print(self.meta.keySet(), id(self.meta))

    @property
    def startDate(self): pass
    @property
    def endDate(self): pass
    @property
    def instrument(self): pass
    @property
    def modelName(self): pass
    @property
    def mission(self): pass
    pass

# Data Model specification for mandatory components
_Model_Spec = {
    'name': 'Product',
    'description': 'Project level product',
    'parents': [
        'BaseProduct',
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
                'default': 'Product',
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
        'startDate': {
                'id_zh_cn': '产品的标称起始时间',
                'fits_keyword': 'DATE-OBS',
                'data_type': 'finetime',
                'description': 'Nominal start time  of this product.',
                'description_zh_cn': '产品标称的起始时间',
                'default': 0,
                'valid': '',
                'valid_zh_cn': '',
                'typecode': None,
                },
        'endDate': {
                'id_zh_cn': '产品的标称结束时间',
                'fits_keyword': 'DATE-END',
                'data_type': 'finetime',
                'description': 'Nominal end time  of this product.',
                'description_zh_cn': '产品标称的结束时间',
                'default': 0,
                'valid': '',
                'valid_zh_cn': '',
                'typecode': None,
                },
        'instrument': {
                'id_zh_cn': '观测仪器名称',
                'data_type': 'string',
                'description': 'Instrument that generated data of this product',
                'description_zh_cn': '观测仪器名称',
                'default': 'UNKNOWN',
                'valid': '',
                'valid_zh_cn': '',
                'typecode': 'B',
                },
        'modelName': {
                'id_zh_cn': '样机名称',
                'fits_keyword': 'MODEL',
                'data_type': 'string',
                'description': 'Model name of the instrument of this product',
                'description_zh_cn': '观测仪器样机名称',
                'default': 'UNKNOWN',
                'valid': '',
                'valid_zh_cn': '',
                'typecode': 'B',
                },
        'mission': {
                'id_zh_cn': '任务名称',
                'fits_keyword': 'TELESCOP',
                'data_type': 'string',
                'description': 'Name of the mission.',
                'description_zh_cn': '任务名称',
                'default': '_AGS',
                'valid': '',
                'valid_zh_cn': '',
                'typecode': 'B',
                },
        },
    'datasets': {
        },
    }

Model = ReadOnlyDict(_Model_Spec)

MdpInfo = Model['metadata']

