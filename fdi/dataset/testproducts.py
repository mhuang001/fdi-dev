from fdi.dataset.product import _Model_Spec as PPI
from .product import Product
from ..pal.context import Context, MapContext
from .finetime import FineTime

import copy


class TP(Product):
    pass


class TC(Context):
    pass


class TM(MapContext):
    pass


# sub-classing testing class
# 'version' of subclass is int, not string

sp = copy.deepcopy(PPI)
sp['name'] = 'SP'
sp['metadata']['version']['data_type'] = 'integer'
sp['metadata']['version']['default'] = 9
sp['metadata']['type']['default'] = sp['name']
MdpInfo = sp['metadata']


class SP(Product):
    def __init__(self,
                 description='UNKNOWN',
                 typ_='SP',
                 creator='UNKNOWN',
                 version='9',
                 creationDate=FineTime(0),
                 rootCause='UNKNOWN',
                 startDate=FineTime(0),
                 endDate=FineTime(0),
                 instrument='UNKNOWN',
                 modelName='UNKNOWN',
                 mission='_AGS',
                 zInfo=None,
                 **kwds):
        metasToBeInstalled = copy.copy(locals())
        for x in ('self', '__class__', 'zInfo', 'kwds'):
            metasToBeInstalled.pop(x)

        self.zInfo = sp
        assert PPI['metadata']['version']['data_type'] == 'string'
        super().__init__(zInfo=zInfo, **metasToBeInstalled, **kwds)
        # super().installMetas(metasToBeInstalled)
