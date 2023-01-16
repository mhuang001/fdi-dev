from fdi.dataset.product import _Model_Spec as PPI
from .product import Product
from .baseproduct import BaseProduct
from .numericparameter import NumericParameter
from .dateparameter import DateParameter
from .stringparameter import StringParameter
from .datatypes import Vector
from .dataset import CompositeDataset
from .tabledataset import TableDataset
from .arraydataset import ArrayDataset, Column
from ..pal.context import Context, MapContext
from ..pal.productref import ProductRef
from ..utils.loadfiles import loadMedia
from .finetime import FineTime

import copy
from math import sin, cos, sqrt
import random
from os import path as op


class TB(BaseProduct):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.zInfo['name'] = 'TB'
        self.zInfo['description'] = 'Test class %s.' % self.zInfo['name']
        self.zInfo['metadata']['type']['default'] = self.zInfo['name']


class TP(Product):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.zInfo['name'] = 'TC'
        self.zInfo['description'] = 'Test class %s.' % self.zInfo['name']
        self.zInfo['metadata']['type']['default'] = self.zInfo['name']


class TC(Context):
    def __init__(self, *args, **kwds):

        super().__init__(*args, **kwds)
        self.zInfo['name'] = 'TC'
        self.zInfo['description'] = 'Test class %s.' % self.zInfo['name']
        self.zInfo['metadata']['type']['default'] = self.zInfo['name']


class TCC(TC):
    def __init__(self, *args, **kwds):

        super().__init__(*args, **kwds)
        self.zInfo['name'] = 'TCC'
        self.zInfo['description'] = 'Test class %s.' % self.zInfo['name']
        self.zInfo['metadata']['type']['default'] = self.zInfo['name']


class TM(MapContext):
    def __init__(self, *args, **kwds):

        super().__init__(*args, **kwds)
        self.zInfo['name'] = 'TM'
        self.zInfo['description'] = 'Test class %s.' % self.zInfo['name']
        self.zInfo['metadata']['type']['default'] = self.zInfo['name']

# sub-classing testing class
# 'version' of subclass is int, not string


sp = copy.deepcopy(PPI)
sp['name'] = 'SP'
sp['metadata']['version']['data_type'] = 'integer'
sp['metadata']['version']['default'] = 9
sp['metadata']['type']['default'] = sp['name']
MdpInfo = sp['metadata']


class SP(Product):
    """ A subclass of `Product` for tests. """

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


def makeCal2D(width=11, height=11):

    center_x = int(width / 2)
    center_y = int(height / 2)
    z = []
    for y in range(height):
        zx = []
        for x in range(width):
            dx = x-center_x
            dy = y-center_y
            r = sqrt(dx*dx+dy*dy)
            zx.append(sin(r)/r if r else 1.0)
        z.append(zx)
    return z


class DemoProduct(MapContext):
    def __init__(self, *args, **kwds):

        super().__init__(*args, **kwds)
        self.zInfo['name'] = 'DemoProduct'
        self.zInfo['description'] = 'Test class %s.' % self.zInfo['name']
        self.zInfo['metadata']['type']['default'] = self.zInfo['name']


def get_demo_product(desc=''):
    """
    A complex context product as a reference for testing and demo.

::

|__ meta                                          <MetaData>
    |   |__ description                                 <string>
    |   |__ type                                        <string>
    |   |__ level                                       <string>
    |   |__ creator                                     <string>
    |   |__ creationDate                              <finetime>
    |   |__ rootCause                                   <string>
    |   |__ version                                     <string>
    |   |__ FORMATV                                     <string>
    |   |__ speed                                       <vector>
    |   \__ listeners                               <ListenerSet>
    |__ measurements                          <CompositeDataset>
    |   |__ meta                                      <MetaData>
    |   |   \__ listeners                           <ListenerSet>
    |   |__ Time_Energy_Pos               <TableDataset> (5, 20)
    |   |   |__ meta                                  <MetaData>
    |   |   |   |__ description                         <string>
    |   |   |   |__ shape                                <tuple>
    |   |   |   |__ type                                <string>
    |   |   |   |__ version                             <string>
    |   |   |   |__ FORMATV                             <string>
    |   |   |   \__ listeners                       <ListenerSet>
    |   |   |__ Time                              <Column> (20,)
    |   |   |__ Energy                            <Column> (20,)
    |   |   |__ Error                             <Column> (20,)
    |   |   |__ y                                 <Column> (20,)
    |   |   \__ z                                 <Column> (20,)
    |   |__ calibration                  <ArrayDataset> (11, 11)
    |   \__ dset                                           <str>
    |__ Environment Temperature              <ArrayDataset> (7,)
    |__ Browse                               <image/png> (5976,)
    |__ refs                                      <RefContainer>
    |   |__ a_reference                             <ProductRef>
    |   \__ a_different_name                        <ProductRef>
    |__ history                                        <History>
    |   |__ PARAM_HISTORY                                  <str>
    |   |__ TASK_HISTORY                                   <str>
    |   \__ meta                                      <MetaData>
    |       \__ listeners                           <ListenerSet>
    \__ listeners                                   <ListenerSet>

    """

    prodx = DemoProduct(desc if desc else 'A complex product for demo/test.')
    prodx.creator = 'Frankenstein'
    # add a parameter with validity descriptors to the product
    prodx.meta['speed'] = NumericParameter(
        description='an extra param',
        value=Vector((1.1, 2.2, 3.3)),  # do not use list
        valid={(1, 22): 'normal', (30, 33): 'fast'}, unit='meter')

    # A CompositeDataset 'measurements' of two sub-datasets: calibration and measurements
    composData = CompositeDataset()
    prodx['measurements'] = composData
    # A 2-dimensional array of calibration data
    a5 = makeCal2D()
    a8 = ArrayDataset(data=a5, unit='count', description='array in composite')
    a10 = 'calibration'

    # a tabledataset as the measurements
    ELECTRON_VOLTS = 'eV'
    SECONDS = 'sec'
    METERS = 'm'
    t = [x * 1.0 for x in range(20)]
    e = [2 * x + 100 for x in t]
    err = [random.random() * 2 - 1 for x in t]
    y = [10 * sin(x*2*3.14/len(t)) for x in t]
    z = [10 * cos(x*2*3.14/len(t)) for x in t]

    x = TableDataset(description="A table of measurement reslts")
    x["Time"] = Column(data=t, unit=SECONDS)
    x["Energy"] = Column(data=e, unit=ELECTRON_VOLTS)
    x["Error"] = Column(data=err, unit=ELECTRON_VOLTS)
    x["y"] = Column(data=y, unit=METERS)
    x["z"] = Column(data=z, unit=METERS)
    # set a tabledataset ans an arraydset, with a parameter in metadata
    # this is the first dataset in composData
    composData['Time_Energy_Pos'] = x

    # put the dataset to the compositedataset. here set() api is used
    composData.set(a10, a8)

    # an arraydsets as environment temperature
    a1 = [768, 767, 766, 4.4, 4.5, 4.6, 5.4E3]
    a2 = 'C'
    a3 = 'Environment Temperature'
    a4 = ArrayDataset(data=a1, unit=a2,
                      description='A 2D array for environment temperature')
    # metadata to the dataset
    a11 = 'T0'
    a12 = DateParameter('2020-02-02T20:20:20.0202',
                        description='meta of compositeDs')
    # This is not the best as a4.T0 does not exist
    # a4.meta[a11] = a12
    # this does it a4.T0 = a12 or:
    setattr(a4, a11, a12)
    # put the arraydataset to the product with a name a3.
    prodx[a3] = a4

    # an image as Browse
    fname = 'imageBlue.png'
    fname = op.join(op.join(op.abspath(op.dirname(__file__)),
                            'resources'), fname)
    image = loadMedia(fname)
    image.file = fname
    prodx['Browse'] = image
    return prodx


def get_related_product():
    p = Product(description='A related Product')
    p['a dumb table'] = TableDataset([('pi', 'e'), (3.14, 2.72)])
    return p
