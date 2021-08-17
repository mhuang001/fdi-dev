from fdi.dataset.product import _Model_Spec as PPI
from .product import Product
from .numericparameter import NumericParameter
from .dateparameter import DateParameter
from .stringparameter import StringParameter
from .datatypes import Vector
from .dataset import CompositeDataset
from .tabledataset import TableDataset
from .arraydataset import ArrayDataset, Column
from ..pal.context import Context, MapContext
from ..utils.loadfiles import loadMedia
from .finetime import FineTime

import copy
from math import sin, cos
from os import path as op


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
    A complex product as a reference for testing and demo.

    ```
    prodx --+-- meta --+-- speed
            |
            +-- Temperature -+-- data=[768, ...] , unit=C
            |                |
            |                +-- meta --+-- T0
            |
            +-- results --+-- calibration -- data=[[109..]], unit=count
                          |
                          +-- Time_Energy_Pos --+-- Time   : data=[...]
                          |                     +-- Energy : data=[...]
                          |                     +-- y      : data=[...]
                          |                     +-- z      : data=[...]
                          |
                          +-- Image -- data = b'\87PNG', content='Content-type: image/png'
    ```

    """
    prodx = Product('A complex product for demonstration.')
    prodx.creator = 'Frankenstein'
    # add a parameter with validity descriptors to the product
    prodx.meta['speed'] = NumericParameter(
        description='an extra param',
        value=Vector((1.1, 2.2, 3.3)),
        valid={(1, 22): 'normal', (30, 33): 'fast'}, unit='meter')

    # an arraydsets
    a1 = [768, 767, 766, 4.4, 4.5, 4.6, 5.4E3]
    a2 = 'C'
    a3 = 'Temperature'
    a4 = ArrayDataset(data=a1, unit=a2, description='An Array')
    # metadata to the dataset
    a11 = 'T0'
    a12 = DateParameter('2020-02-02T20:20:20.0202',
                        description='meta of composite')
    # This is not the best as a4.T0 does not exist
    # a4.meta[a11] = a12
    # this does it a4.T0 = a12 or:
    setattr(a4, a11, a12)
    # put the arraydataset to the product with a name a3.
    prodx[a3] = a4

    compo = CompositeDataset()
    prodx['results'] = compo
    a5 = [[109, 289, 9], [88, 3455, 564]]
    a8 = ArrayDataset(data=a5, unit='count', description='array in composite')
    a10 = 'calibration'
    # put the dataset to the compositedataset. here set() api is used
    compo.set(a10, a8)
    # a tabledataset
    ELECTRON_VOLTS = 'eV'
    SECONDS = 'sec'
    METERS = 'm'
    t = [x * 1.0 for x in range(9)]
    e = [2 * x + 100 for x in t]
    y = [10 * sin(x*2*3.14/len(t)) for x in t]
    z = [10 * cos(x*2*3.14/len(t)) for x in t]
    x = TableDataset(description="A table")
    x["Time"] = Column(data=t, unit=SECONDS)
    x["Energy"] = Column(data=e, unit=ELECTRON_VOLTS)
    x["y"] = Column(data=y, unit=METERS)
    x["z"] = Column(data=z, unit=METERS)
    # set a tabledataset ans an arraydset, with a parameter in metadata
    compo['Time_Energy_Pos'] = x

    # an image
    fname = 'imageBlue.png'
    fname = op.join(op.join(op.abspath(op.dirname(__file__)),
                            'resources'), fname)
    image = loadMedia(fname)
    image.file = fname
    prodx['Image'] = image

    return prodx
