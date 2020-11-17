# -*- coding: utf-8 -*-

# Automatically generated from fdi/dataset/resources/Product.yml. Do not edit.

from collections import OrderedDict
from fdi.dataset.baseproduct import BaseProduct
from fdi.dataset.finetime import FineTime


import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Product(BaseProduct,):
    """ Product class (level ALL) schema 1.2 inheriting ['BaseProduct']. Automatically generated from fdi/dataset/resources/Product.yml on 2020-11-17 08:30:48.843903.

    Generally a Product (inheriting BaseProduct) has project-wide attributes and can be extended to define a plethora of specialized products.
    """


    def __init__(self,
                 description = """UNKNOWN""",
                 type_ = """Product""",
                 creator = """UNKNOWN""",
                 creationDate = FineTime(0),
                 rootCause = """UNKNOWN""",
                 version = """0.7""",
                 startDate = FineTime(0),
                 endDate = FineTime(0),
                 instrument = """UNKNOWN""",
                 modelName = """UNKNOWN""",
                 mission = """_AGS""",
                 **kwds):
        """ Initializes instances with more metadata as attributes, set to default values.

        Put description keyword argument here to allow 'BaseProduct("foo") and description='foo'
        """

        if 'metasToBeInstalled' not in kwds:
            # this class is being called directly

            # list of local variables.
            lvar = locals()
            lvar.pop('self')
            lvar.pop('__class__')
            lvar.pop('kwds')
            metasToBeInstalled = lvar
        else:
            # This class is being called probably from super() in a subclass
            metasToBeInstalled = kwds['metasToBeInstalled']
            del kwds['metasToBeInstalled']

	# must be the first line to initiate meta and get description
        super(Product , self).__init__(
            metasToBeInstalled=metasToBeInstalled, **kwds)

        global ProductInfo
        self.pInfo = ProductInfo
        super(Product , self).installMetas(
            mtbi=metasToBeInstalled, prodInfo=ProductInfo)



ProductInfo = {
    """name""": """Product""",
    """description""": """Project level product""",
    """parents""": [
        """BaseProduct""",
        ],
    """level""": """ALL""",
    """schema""": """1.2""",
    """metadata""": {
        """description""": {
                """current_id""": """description""",
                """id""": """description""",
                """id_zh_cn""": """描述""",
                """fits_keyword""": """DESCRIPT""",
                """data_type""": """string""",
                """description""": """Description of this product""",
                """description_zh_cn""": """对本产品的描述。""",
                """examples""": """SINGLE EXPOSURE""",
                """default""": """UNKNOWN""",
                """valid""": """""",
                """typecode""": """B""",
                },
        """type""": {
                """current_id""": """type""",
                """id""": """type""",
                """id_zh_cn""": """产品类型""",
                """data_type""": """string""",
                """description""": """Product Type identification. Name of class or CARD.""",
                """description_zh_cn""": """产品类型。完整Python类名或卡片名。""",
                """default""": """Product""",
                """valid""": """""",
                """valid_zh_cn""": """""",
                """typecode""": """B""",
                },
        """creator""": {
                """current_id""": """creator""",
                """id""": """creator""",
                """id_zh_cn""": """本产品生成者""",
                """fits_keyword""": """CREATOR""",
                """data_type""": """string""",
                """description""": """Generator of this product.""",
                """description_zh_cn""": """本产品生成方的标识，例如可以是单位、组织、姓名、软件、或特别算法等。""",
                """examples""": """SECM-EGSE""",
                """default""": """UNKNOWN""",
                """valid""": """""",
                """typecode""": """B""",
                },
        """creationDate""": {
                """current_id""": """creationDate""",
                """id""": """creationDate""",
                """id_zh_cn""": """产品生成时间""",
                """fits_keyword""": """DATE""",
                """data_type""": """finetime""",
                """description""": """Creation date of this product""",
                """description_zh_cn""": """本产品生成时间""",
                """examples""": """10361455509632""",
                """default""": 0,
                """valid""": """""",
                """typecode""": None,
                },
        """rootCause""": {
                """current_id""": """rootCause""",
                """id""": """rootCause""",
                """id_zh_cn""": """数据来源""",
                """fits_keyword""": """ROOTCAUS""",
                """data_type""": """string""",
                """description""": """Reason of this run of pipeline.""",
                """description_zh_cn""": """数据来源（此例来自鉴定件热真空罐）""",
                """examples""": """QM-ThermVac""",
                """default""": """UNKNOWN""",
                """valid""": """""",
                """typecode""": """B""",
                },
        """version""": {
                """current_id""": """formatVersion""",
                """id""": """version""",
                """id_zh_cn""": """格式版本""",
                """data_type""": """string""",
                """description""": """Version of product schema""",
                """description_zh_cn""": """产品格式版本""",
                """default""": """0.7""",
                """valid""": """""",
                """valid_zh_cn""": """""",
                """typecode""": """B""",
                },
        """startDate""": {
                """current_id""": """startDate""",
                """id""": """startTime""",
                """id_zh_cn""": """产品的标称起始时间""",
                """fits_keyword""": """DATE-OBS""",
                """data_type""": """finetime""",
                """description""": """Nominal start time  of this product.""",
                """description_zh_cn""": """产品标称的起始时间""",
                """default""": 0,
                """valid""": """""",
                """valid_zh_cn""": """""",
                """typecode""": None,
                },
        """endDate""": {
                """current_id""": """endDate""",
                """id""": """endTime""",
                """id_zh_cn""": """产品的标称结束时间""",
                """fits_keyword""": """DATE-END""",
                """data_type""": """finetime""",
                """description""": """Nominal end time  of this product.""",
                """description_zh_cn""": """产品标称的结束时间""",
                """default""": 0,
                """valid""": """""",
                """valid_zh_cn""": """""",
                """typecode""": None,
                },
        """instrument""": {
                """current_id""": """instrument""",
                """id""": """instrument""",
                """id_zh_cn""": """观测仪器名称""",
                """data_type""": """string""",
                """description""": """Instrument that generated data of this product""",
                """description_zh_cn""": """观测仪器名称""",
                """default""": """UNKNOWN""",
                """valid""": """""",
                """valid_zh_cn""": """""",
                """typecode""": """B""",
                },
        """modelName""": {
                """current_id""": """modelName""",
                """id""": """modelName""",
                """id_zh_cn""": """样机名称""",
                """fits_keyword""": """MODEL""",
                """data_type""": """string""",
                """description""": """Model name of the instrument of this product""",
                """description_zh_cn""": """观测仪器样机名称""",
                """default""": """UNKNOWN""",
                """valid""": """""",
                """valid_zh_cn""": """""",
                """typecode""": """B""",
                },
        """mission""": {
                """current_id""": """mission""",
                """id""": """mission""",
                """id_zh_cn""": """任务名称""",
                """fits_keyword""": """TELESCOP""",
                """data_type""": """string""",
                """description""": """Name of the mission.""",
                """description_zh_cn""": """任务名称""",
                """default""": """_AGS""",
                """valid""": """""",
                """valid_zh_cn""": """""",
                """typecode""": """B""",
                },
        },
    """datasets""": {
        },
    }
