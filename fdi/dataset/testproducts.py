from fdi.dataset.product import _Model_Spec as PPI
from .product import Product
from .numericparameter import NumericParameter
from .stringparameter import StringParameter
from .datatypes import Vector
from .dataset import CompositeDataset
from .tabledataset import TableDataset
from .arraydataset import ArrayDataset, Column
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
