# -*- coding: utf-8 -*-

# Automatically generated from fdi/dataset/resources/Product.yml. Do not edit.

from collections import OrderedDict
from fdi.dataset.baseproduct import BaseProduct
from fdi.dataset.finetime import FineTime


from fdi.dataset.readonlydict import ReadOnlyDict

import copy

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Product(BaseProduct):
    """ Product class (level ALL) schema 1.4 inheriting ['BaseProduct'].

Automatically generated from fdi/dataset/resources/Product.yml on 2021-02-18 22:19:05.909785.

Description:
Project level product

    Generally a Product (inheriting BaseProduct) has project-wide attributes and can be extended to define a plethora of specialized products.
    """


    def __init__(self,
                 description = 'UNKNOWN',
                 typ_ = 'Product',
                 creator = 'UNKNOWN',
                 creationDate = FineTime(0),
                 rootCause = 'UNKNOWN',
                 version = '0.8',
                 FORMATV = '1.4.0.8',
                 startDate = FineTime(0),
                 endDate = FineTime(0),
                 instrument = 'UNKNOWN',
                 modelName = 'UNKNOWN',
                 mission = '_AGS',
                 **kwds):
        """ Initializes instances with more metadata as attributes, set to default values.

        Put description keyword argument here to allow e.g. BaseProduct("foo") and description='foo'
        """
        if 'metasToBeInstalled' in kwds:
            # This class is being called probably from super() in a subclass
            metasToBeInstalled = kwds['metasToBeInstalled']
            del kwds['metasToBeInstalled']

            # must be the first line to initiate meta and get description
            super().__init__(
                metasToBeInstalled=metasToBeInstalled, **kwds)
            return
        # this class is being called directly

        # list of local variables.
        metasToBeInstalled = copy.copy(locals())
        for x in ('self', '__class__', 'kwds'):
            metasToBeInstalled.pop(x)

        global ProductInfo
        self.zInfo = ProductInfo

        #print('@1 zInfo', id(self.zInfo['metadata']), id(self), id(self.zInfo),
        #      self.zInfo['metadata']['version'], list(metasToBeInstalled.keys()))

        # must be the first line to initiate meta and get description
        super().__init__(
            metasToBeInstalled=metasToBeInstalled, **kwds)

        super().installMetas(mtbi=metasToBeInstalled, prodInfo=ProductInfo)
        #print(self.meta.keySet(), id(self.meta))


    @property
    def type(self): pass

    @type.setter
    def type(self, p): pass


    @property
    def startDate(self): pass

    @startDate.setter
    def startDate(self, p): pass


    @property
    def endDate(self): pass

    @endDate.setter
    def endDate(self, p): pass


    @property
    def instrument(self): pass

    @instrument.setter
    def instrument(self, p): pass


    @property
    def modelName(self): pass

    @modelName.setter
    def modelName(self, p): pass


    @property
    def mission(self): pass

    @mission.setter
    def mission(self, p): pass


    @property
    def version(self): pass

    @version.setter
    def version(self, p): pass


    @property
    def FORMATV(self): pass

    @FORMATV.setter
    def FORMATV(self, p): pass





_Model_Spec = {
    'name': 'Product',
    'description': 'Project level product',
    'parents': [
        'BaseProduct',
        ],
    'level': 'ALL',
    'schema': '1.4',
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
                'valid_zh_cn': '',
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
                'default': '1.4.0.8',
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

ProductInfo = ReadOnlyDict(_Model_Spec)
