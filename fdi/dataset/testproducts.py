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


class SP(Product):
    def __init__(self,
                 description='UNKNOWN',
                 typ_='SP',
                 creator='UNKNOWN',
                 version=9,
                 creationDate=FineTime(0),
                 rootCause='UNKNOWN',
                 startDate=FineTime(0),
                 endDate=FineTime(0),
                 instrument='UNKNOWN',
                 modelName='UNKNOWN',
                 mission='_AGS',
                 **kwds):
        metasToBeInstalled = copy.copy(locals())
        for x in ('self', '__class__', 'kwds'):
            metasToBeInstalled.pop(x)

        sp = {}
        sp = copy.deepcopy(PPI)
        sp['name'] = self.__class__.__name__
        sp['metadata']['version']['data_type'] = 'integer'
        sp['metadata']['version']['default'] = 9
        sp['metadata']['type']['default'] = sp['name']
        self.zInfo = sp
        assert PPI['metadata']['version']['data_type'] == 'string'
        super().__init__(metasToBeInstalled=metasToBeInstalled, **kwds)
        super().installMetas(mtbi=metasToBeInstalled, prodInfo=self.zInfo)

    @ property
    def version(self): pass

    @ version.setter
    def version(self, p): pass
