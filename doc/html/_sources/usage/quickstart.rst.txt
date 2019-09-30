================
spdc Quick Start
================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


dataset
=======

ArrayDataset
------------

Creation

>>> a1 = [1, 4.4, 5.4E3]      # a 1D array of data
>>> a2 = 'ev'                 # unit
>>> a3 = 'three energy vals'  # description
>>> v = ArrayDataset(data=a1, unit=a2, description=a3)
>>> v1 = ArrayDataset(a1, a2, description=a3)  # simpler but error-prone
>>> print(v)
ArrayDataset{ description = "three energy vals", meta = MetaData[], data = "[1, 4.4, 5400.0]", unit = "ev"}
>>> 
>>> print(v == v1)
True
>>> 

data access

>>> v1.data = [34]
>>> v1.unit = 'm'
>>> print('The diameter is %f %s.' % (v1.data[0], v1.unit))
The diameter is 34.000000 m.
>>> 
>>> # iteration
... 
>>> i = []
>>> for m in v:
...     i.append(m)
... 
>>> #assert i == a1
... 
>>> print(i)
[1, 4.4, 5400.0]
>>> 
>>> # slice
... 
>>> d = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
>>> x = ArrayDataset(data=d)
>>> x
ArrayDataset{ description = "UNKNOWN", meta = MetaData[], data = "[[1, 2, 3], [4, 5, 6], [7, 8, 9]]", unit = "None"}
>>> 
>>> x[0:2]
[[1, 2, 3], [4, 5, 6]]
>>> 
 
Run this to see a demo of the ``toString()`` function::

  # demo of toString()
  # make a 4-D array: a list of 2 lists of 3 lists of 4 lists of 5 elements.
  
  s = [[[[i + j + k + l for i in range(5)] for j in range(4)]
         for k in range(3)] for l in range(2)]
   
  x = ArrayDataset(data=s)
   
  print(x.toString())
   
and you get::

   # ArrayDataset
   # description = "UNKNOWN"
   # meta = MetaData{[], listeners = []}
   # unit = "None"
   # data = 
   
   0 1 2 3 
   1 2 3 4 
   2 3 4 5 
   3 4 5 6 
   4 5 6 7 
   
   
   1 2 3 4 
   2 3 4 5 
   3 4 5 6 
   4 5 6 7 
   5 6 7 8 
   
   
   2 3 4 5 
   3 4 5 6 
   4 5 6 7 
   5 6 7 8 
   6 7 8 9 
   
   
   #=== dimension 4
   
   1 2 3 4 
   2 3 4 5 
   3 4 5 6 
   4 5 6 7 
   5 6 7 8 
   
   
   2 3 4 5 
   3 4 5 6 
   4 5 6 7 
   5 6 7 8 
   6 7 8 9 
   
   
   3 4 5 6 
   4 5 6 7 
   5 6 7 8 
   6 7 8 9 
   7 8 9 10 
   
   
   #=== dimension 4
   





TableDataset
------------

Creation

>>> from dataset.dataset import TableDataset, Column
>>> 
>>> a1 = [dict(name='col1', unit='eV', column=[1, 4.4, 5.4E3]),
...       dict(name='col2', unit='cnt', column=[0, 43.2, 2E3])
...       ]
>>> v = TableDataset(data=a1)
>>> 
>>> #  many other ways to create a TableDataset
... 
>>> a4 = dict(col1=Column(data=[1, 4.4, 5.4E3], unit='eV'),
...           col2=Column(data=[0, 43.2, 2E3], unit='cnt'))
>>> v4 = TableDataset(data=a4)
>>> v == v4
True
>>> 
>>> v3 = TableDataset(data=[('col1', [1, 4.4, 5.4E3], 'eV'),
...                         ('col2', [0, 43.2, 2E3], 'cnt')])
>>> v == v3
True

>>> 
>>> # add columns, replace columns
... u = TableDataset()
>>> c = Column([1, 4], 'sec')
>>> u.addColumn('col3', c)
>>> # for non-existing names set is addColum.
... u['col4'] = Column([2, 3], 'eu')
>>> print(u['col4'][0])  # == 2
2
>>> # replace column for existing names
... u['col4'] = c
>>> print(u['col4'][0])  # == 1
1
>>>

access

>>> # unit access
... print(u['col4'].unit)  # == 'sec'
sec
>>> 
>>> # with indexOf
... print(u.indexOf('col3'))  # == u.indexOf(c)
0
>>> print(u.indexOf(c))
0
>>> 
>>> # set cell value
... u.setValueAt(aValue=42, rowIndex=1, columnIndex=1)
>>> print(u.getValueAt(rowIndex=1, columnIndex=1))
42
>>> 
>>> # replace whole table. see constructor examples for making a1
... u.data = a1
>>> print(v == u)
True
>>> 
>>> # syntax ``in``
... [c for c in u]  # list of column names
['col1', 'col2']

run this to see ``toString()``

.. code-block::
   
   from dataset.dataset import TableDataset
   # creation:
   ELECTRON_VOLTS = 'eV'
   SECONDS = 'sec'
   t = [x * 1.0 for x in range(10)]
   e = [2 * x + 100 for x in t]

   # creating a table dataset to hold the quantified data
   x = TableDataset(description="Example table")
   x["Time"] = Column(data=t, unit=SECONDS)
   x["Energy"] = Column(data=e, unit=ELECTRON_VOLTS)
   ts = x.toString()
   print(ts)

the output is::
  
  # TableDataset
  # description = "Example table"
  # meta = MetaData{[], listeners = []}
  # data = 

  # Time Energy
  # sec eV
  0.0 100.0 
  1.0 102.0 
  2.0 104.0 
  3.0 106.0 
  4.0 108.0 
  5.0 110.0 
  6.0 112.0 
  7.0 114.0 
  8.0 116.0 
  9.0 118.0 

Metadata and Parameter
----------------------

Creation

>>> from dataset.metadata import Parameter, NumericParameter, MetaData
>>> 
>>> # creation
... 
>>> v = MetaData()
>>> a1 = 'foo'
>>> a2 = Parameter(description='test param', value=900)
>>> v.set(a1, a2)
>>> print(v)
MetaData['foo']

access

>>> # set parameter with several syntaxes
... a3 = 'more'
>>> v.set(name=a1, newParameter=a3)
>>> print(v[a1])  # == a3
more
>>> 
>>> a4 = NumericParameter(description='another param',
...                       value=2.3, unit='sec')
>>> v[a3] = a4
>>> print(v)
MetaData['foo', 'more']
>>> v.toString()
'MetaData{[more = NumericParameter{ description = "another param", value = "2.3", unit = "sec", type = ""}, ], listeners = []}'
>>> 
>>> # remove parameter
... v.remove(a1)  # inherited from composite
'more'
>>> print(v.size())  # == 1
1


Product
-------

Creation:

>>> from dataset.product import Product
>>> from dataset.dataset import ArrayDataset, TableDataset
>>> 
>>> x = Product(description="This is my product example",
...             instrument="MyFavourite", modelName="Flight")
>>> 
>>> print(x.meta['description'])  # == "This is my product example"
This is my product example
>>> 
>>> print(x.instrument)  # == "MyFavourite"
MyFavourite

Ways to add datasets

>>> i0 = 6
>>> i1 = [[1, 2, 3], [4, 5, i0], [7, 8, 9]]
>>> i2 = 'ev'                 # unit
>>> i3 = 'img1'  # description
>>> image = ArrayDataset(data=i1, unit=i2, description=i3)
>>> 
>>> x["RawImage"] = image
>>> print(x["RawImage"].data)  # [1][2] == i0
[[1, 2, 3], [4, 5, 6], [7, 8, 9]]
>>> 
>>> # no unit or description. diff syntax same function as above
... x.set('QualityImage', ArrayDataset(
...     [[0.1, 0.5, 0.7], [4e3, 6e7, 8], [-2, 0, 3.1]]))
>>> print(x["QualityImage"].unit)  # is None
None
>>> 
>>> # add a tabledataset
... s1 = [('col1', [1, 4.4, 5.4E3], 'eV'),
...       ('col2', [0, 43.2, 2E3], 'cnt')
...       ]
>>> spec = TableDataset(data=s1)
>>> x["Spectrum"] = spec
>>> 
>>> # mandatory properties are also in metadata
... x.creator = ""
>>> a0 = "Me, myself and I"
>>> x.creator = a0
>>> print(x.creator)  # == a0
Me, myself and I
>>> 
>>> print(x.meta["creator"])  # == a0
Me, myself and I
>>>

``toString()`` function::

  # Product
  # description = "This is my product example"
  # meta = MetaData{[description = This is my product example, creator = Me, myself and I, creationDate = 2000-01-01T00:00:00.000000 TAI(0), instrument = MyFavourite, startDate = , endDate = , rootCause = UNKNOWN, modelName = Flight, type = UNKNOWN, mission = SVOM, ], listeners = [Product 7696578744448 "This is my product example", ]}
  # History
  # description = "UNKNOWN"
  # meta = MetaData{[], listeners = []}
  # data = 

  # data = 


  # [ RawImage ]
  # ArrayDataset
  # description = "img1"
  # meta = MetaData{[], listeners = []}
  # unit = "ev"
  # data = 

  1 4 7 
  2 5 8 
  3 6 9 


  # [ QualityImage ]
  # ArrayDataset
  # description = "UNKNOWN"
  # meta = MetaData{[], listeners = []}
  # unit = "None"
  # data = 

  0.1 4000.0 -2 
  0.5 60000000.0 0 
  0.7 8 3.1 


  # [ Spectrum ]
  # TableDataset
  # description = "UNKNOWN"
  # meta = MetaData{[], listeners = []}
  # data = 

  # col1 col2
  # eV cnt
  1 0 
  4.4 43.2 
  5400.0 2000.0 




For more examples see tests/test_dataset.py

pal
===

Create a product and a productStorage with a pool registered
  
>>> import os
>>> 
>>> # disable debugging messages
... import logging
>>> logger = logging.getLogger('')
>>> logger.setLevel(logging.WARNING)
>>> 
>>> from dataset.product import Product
>>> from pal.productstorage import ProductStorage
>>> from pal.poolmanager import PoolManager
>>> from pal.context import MapContext
>>> from pal.common import getProductObject
>>> 
>>> # a pool for domostration will be create here
... demopoolpath = '/tmp/demopool'
>>> demopool = 'file://' + demopoolpath
>>> # clean possible data left from previous runs
... os.system('rm -rf ' + demopoolpath)
0
>>> 
>>> # create a prooduct
... x = Product(description='in store')
>>> print(x)
{meta = "MetaData['description', 'creator', 'creationDate', 'instrument', 'startDate', 'endDate', 'rootCause', 'modelName', 'type', 'mission']", _sets = [], history = {meta = "MetaData[]", _sets = []}}
>>> 
>>> # create a product store
... pstore = ProductStorage(pool=demopool)
>>> 

Save the product and get a reference

>>> prodref = pstore.save(x)
>>> print(prodref)
ProductRef{ ProductURN=urn:file:///tmp/demopool:Product:0, meta=MetaData['description', 'creator', 'creationDate', 'instrument', 'startDate', 'endDate', 'rootCause', 'modelName', 'type', 'mission']}
>>> 
>>> # create an empty mapcontext
... mc = MapContext()
>>> # put the ref in the context.
... # The manual has this syntax mc.refs.put('xprod', prodref)
... # but I like this for doing the same thing:
... mc['refs']['very-useful'] = prodref
>>> # get the urn string
... urn = prodref.urn
>>> print(urn)
urn:file:///tmp/demopool:Product:0


re-create a product only using the urn
  
>>> newp = getProductObject(urn)
>>> # the new and the old one are equal
... print(newp)  # == x
{meta = "MetaData['description', 'creator', 'creationDate', 'instrument', 'startDate', 'endDate', 'rootCause', 'modelName', 'type', 'mission']", _sets = [], history = {meta = "MetaData[]", _sets = []}}
>>> 

For more examples see tests/test_pal.py

pns
===

See the installation and testing sections of the pns page.
