
================
Quick Start
================

.. contents:: Contents:

   
The following demostrates important dataset and pal functionalities.

.. tip::
   
   You can copy the code from code blocks by clicking the ``copy`` icon on the top-right, with he prompts and results removed.

.. highlight:: none

	       
>>> from fdi.dataset.product import Product
...  from fdi.dataset.metadata import Parameter, NumericParameter, MetaData, StringParameter, DateParameter
...  from fdi.dataset.finetime import FineTime, FineTime1
...  from fdi.dataset.dataset import ArrayDataset, TableDataset, Column
...  from fdi.dataset.classes import Classes
...  from fdi.pal.context import Context, MapContext
...  from fdi.pal.productref import ProductRef
...  from fdi.pal.query import AbstractQuery, MetaQuery
...  from fdi.pal.poolmanager import PoolManager, DEFAULT_MEM_POOL
...  from fdi.pal.productstorage import ProductStorage

>>> import getpass
...  import os
...  from datetime import datetime, timezone
...  import logging

>>> # initialize the white-listed class dictionary
...  cmap = Classes.updateMapping()


dataset
=======
The data model.


ArrayDataset
------------


>>> # Creation
...  a1 = [1, 4.4, 5.4E3, -22, 0xa2]      # a 1D array of data
...  # quick
...  v = ArrayDataset(a1)
...  v

.. code-block:: none
		
		# ArrayDataset
		description= {'UNKNOWN'},
		meta= {
		(empty)
		},
		type= {None},
		default= {None},
		typecode= {None},
		unit= {None}
		ArrayDataset-dataset =
		1  4.4  5400  -22  162

>>> # clear
...  v = ArrayDataset(data=a1, unit='ev', description='5 elements',
...                   typ_='float', default=1.0, typecode='f')
...  v

.. code-block:: none
   
   # ArrayDataset
   description= {'5 elements'},
   meta= {
   (empty)
   },
   type= {'float'},
   default= {1.0},
   typecode= {'f'},
   unit= {'ev'}
   ArrayDataset-dataset =
   1  4.4  5400  -22  162

>>> # data access
...  v[2]
5400.0

>>> v.unit
'ev'

>>> # change attributes
...  v.unit = 'm'
...  v.unit
'm'

>>> # iteration
...  for m in v:
...      print(m)

::

   1
   4.4
   5400.0
   -22
   162

>>> # a filter example
...  [m**3 for m in v if m > 0 and m < 40]
[1, 85.18400000000003]

>>> # slice
...  v[1:3]
[4.4, 5400.0]

>>> v[2:-1]
[5400.0, -22]

>>> # a 2D array
...  v.data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
...  v[0:2]
[[1, 2, 3], [4, 5, 6]]

>>> # Run this to see a demo of the ``toString()`` function::
...  # make a 4-D array: a list of 2 lists of 3 lists of 4 lists of 5 elements.
...  s = [[[[i + j + k + l for i in range(5)] for j in range(4)]
...        for k in range(3)] for l in range(2)]
...  x = ArrayDataset(data=s)
...  print(x.toString())

::
   
   # ArrayDataset
   description= {'UNKNOWN'},
   meta= {# MetaData
   (empty)
   MetaData-listeners = ListnerSet{}},
   type= {None},
   default= {None},
   typecode= {None},
   unit= {None}
   ArrayDataset-dataset =
   0  1  2  3  4
   1  2  3  4  5
   2  3  4  5  6
   3  4  5  6  7


   1  2  3  4  5
   2  3  4  5  6
   3  4  5  6  7
   4  5  6  7  8


   2  3  4  5  6
   3  4  5  6  7
   4  5  6  7  8
   5  6  7  8  9


   #=== dimension 4

   1  2  3  4  5
   2  3  4  5  6
   3  4  5  6  7
   4  5  6  7  8


   2  3  4  5  6
   3  4  5  6  7
   4  5  6  7  8
   5  6  7  8  9


   3  4  5  6   7
   4  5  6  7   8
   5  6  7  8   9
   6  7  8  9  10


   #=== dimension 4




TableDataset
------------

TableDataset is mainly a name-Column pairs dictionary with metadata.
Columns are ArrayDatasets under a different name.

>>> # Creation
...  a1 = [dict(name='col1', unit='eV', column=[1, 4.4, 5.4E3]),
...        dict(name='col2', unit='cnt', column=[0, 43.2, 2E3])
...        ]
...  v = TableDataset(data=a1)
...  v

::

   # TableDataset
   description= {'UNKNOWN'},
   meta= {
   (empty)
   }
   TableDataset-dataset =
   ======  =======
   col1     col2
   (eV)    (cnt)
   ======  =======
      1        0
      4.4     43.2
   5400     2000
   ======  =======



>>> # one of many other ways to create a TableDataset
...  v3 = TableDataset(data=[('col1', [1, 4.4, 5.4E3], 'eV'),
...                          ('col2', [0, 43.2, 2E3], 'cnt')])
...  v == v3
True

>>> # quick tabledataset. data are list of lists without names or units
...  a5 = [[1, 4.4, 5.4E3], [0, 43.2, 2E3]]
...  v5 = TableDataset(data=a5)
...  print(v5.toString())

::

   # TableDataset
   description= {'UNKNOWN'},
   meta= {# MetaData
   (empty)
   MetaData-listeners = ListnerSet{}}
   TableDataset-dataset =
   ========  ========
   col1      col2
   (None)    (None)
   ========  ========
      1         0
      4.4      43.2
   5400      2000
   ========  ========

>>> # access
...  # get names of all column
...  v5.getColumnNames()
['col1', 'col2']

>>> # get a list of all columns' data
...  [c.data for c in v5.data.values()]   # == a5
[[1, 4.4, 5400.0], [0, 43.2, 2000.0]]

>>> # get column by name
...  my_column = v5['col1']
...  my_column

::
   
   # Column
   description= {'UNKNOWN'},
   meta= {
   (empty)
   },
   type= {None},
   default= {None},
   typecode= {None},
   unit= {None}
   Column-dataset =
   1  4.4  5400

>>> #  indexOf
...  v5.indexOf('col1')  # == u.indexOf(my_column)
0

>>> v5.indexOf(my_column)
0

>>> # set cell value
...  v5['col2'][1] = 123
...  v5['col2'][1]    # 123
123

>>> # unit access
...  v3['col1'].unit  # == 'eV'
'eV'

>>> # add, set, and replace columns and rows
...  # column set / get
...  u = TableDataset()
...  c1 = Column([1, 4], 'sec')
...  u.addColumn('time', c1)
...  u.columnCount        # 1
1

>>> # for non-existing names set is addColum.
...  u['money'] = Column([2, 3], 'eu')
...  u['money'][0]    # 2
2

>>> u.columnCount        # 2
2

>>> # addRow
...  u.rowCount    # 2
2

>>> u.addRow({'money': 4.4, 'time': 3.3})
...  u.rowCount    # 3
3

>>> # syntax ``in``
...  [c for c in u]  # list of column names ['time', 'money']
['time', 'money']

>>> # run this to see ``toString()``
...  ELECTRON_VOLTS = 'eV'
...  SECONDS = 'sec'
...  t = [x * 1.0 for x in range(10)]
...  e = [2 * x + 100 for x in t]
...  # creating a table dataset to hold the quantified data
...  x = TableDataset(description="Example table")
...  x["Time"] = Column(data=t, unit=SECONDS)
...  x["Energy"] = Column(data=e, unit=ELECTRON_VOLTS)
...  print(x.toString())

::

   # TableDataset
   description= {'Example table'},
   meta= {# MetaData
   (empty)
   MetaData-listeners = ListnerSet{}}
   TableDataset-dataset =
   =======  ========
   Time    Energy
   (sec)      (eV)
   =======  ========
   0       100
   1       102
   2       104
   3       106
   4       108
   5       110
   6       112
   7       114
   8       116
   9       118
   =======  ========


Parameter
---------


>>> # Creation
...  # standard way -- with keyword arguments
...  v = Parameter(value=9000, description='Average age', typ_='integer')
...  v.description   # 'Average age
'Average age'

>>> v.value   # == 9000
9000

>>> v.type   # == 'integer'
'integer'

>>> # test equals
...  v1 = Parameter(description='Average age', value=9000, typ_='integer')
...  v.equals(v1)
True

>>> v == v1
True

>>> v1.value = -4
...  v.equals(v1)   # False
False

>>> v != v1  # True
True

>>> # NumericParameter with two valid values and a valid range.
...  v = NumericParameter(value=9000, valid={
...                       0: 'OK1', 1: 'OK2', (100, 9900): 'Go!'})

>>> # There are thee valid conditions
...  v
9000

>>> # The current value is valid
...  v.isvalid()
True

>>> # check if other values are valid according to specification of this parameter
...  v.validate(600)  # valid
(600, 'Go!')

>>> v.validate(20)  # invalid
(Invalid, 'Invalid')

Metadata
--------
A container for named parameters.


>>> # Creation
...  a1 = 'weight'
...  a2 = NumericParameter(description='How heavey is the robot.',
...                        value=20, unit='kg', typ_='integer')
...  v = MetaData()
...  # place the parameter with a name
...  v.set(a1, a2)
...  # get the parameter with the name
...  v.get(a1)   # == a2
20

>>> # add more parameter
...  v.set(name='job', newParameter=StringParameter('teacher'))
...  # get the value of the parameter
...  v.get('job').value   # == 'teacher'
'teacher'

>>> # access parameters in metadata
...  v = MetaData()
...  # a more readable way to set/get a parameter than "v.set(a1,a2)", "v.get(a1)"
...  v[a1] = a2
...  v[a1]   # == a2
20

>>> # same result as...
...  v.get(a1)   # == a2
20

>>> # Date type parameter use International Atomic Time (TAI) to keep time,
...  # in 1-microsecond precission
...  v['birthday'] = Parameter(description='was made on',
...                            value=FineTime('2020-09-09T12:34:56.789098 UTC'))
...  v['birthday'].value.tai
1978346096789098

>>> # names of all parameters
...  [n for n in v]   # == ['weight', 'birthday']
['weight', 'birthday']

>>> # string presentation
...  print(v.toString())

::
   
   # MetaData
   +----------+------------------+--------+----------+---------+-----------+--------+--------------------+
   | name     | value            | unit   | type     | valid   | default   | code   | description        |
   +==========+==================+========+==========+=========+===========+========+====================+
   | weight   | 20               | kg     | integer  | None    | None      | None   | How heavey is the  |
   |          |                  |        |          |         |           |        | robot.             |
   +----------+------------------+--------+----------+---------+-----------+--------+--------------------+
   | birthday | 2020-09-09       | -      | finetime | None    | None      | -      | was made on        |
   |          | 12:34:56.789098  |        |          |         |           |        |                    |
   |          | 1978346096789098 |        |          |         |           |        |                    |
   +----------+------------------+--------+----------+---------+-----------+--------+--------------------+
   MetaData-listeners = ListnerSet{}

>>> # remove parameter
...  v.remove(a1)  # inherited from composite
...  print(v.size())  # == 1
1

>>> # simplifed string presentation
...  print(v)

::

   # MetaData

   (empty)

   MetaData-listeners = ListnerSet{}


Product
-------


>>> # Creation:
...  x = Product(description="product example with several datasets",
...              instrument="Crystal-Ball", modelName="Mk II")
...  x.meta['description'].value  # == "product example with several datasets"
'product example with several datasets'

>>> x.instrument  # == "Crystal-Ball"
'Crystal-Ball'

>>> # ways to add datasets
...  i0 = 6
...  i1 = [[1, 2, 3], [4, 5, i0], [7, 8, 9]]
...  i2 = 'ev'                 # unit
...  i3 = 'image1'     # description
...  image = ArrayDataset(data=i1, unit=i2, description=i3)
...  x["RawImage"] = image
...  x["RawImage"].data  # == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
[[1, 2, 3], [4, 5, 6], [7, 8, 9]]

>>> # no unit or description. different syntax but same function as above
...  x.set('QualityImage', ArrayDataset(
...      [[0.1, 0.5, 0.7], [4e3, 6e7, 8], [-2, 0, 3.1]]))
...  x["QualityImage"].unit  # is None

>>> # add a tabledataset
...  s1 = [('col1', [1, 4.4, 5.4E3], 'eV'),
...        ('col2', [0, 43.2, 2E3], 'cnt')]
...  x["Spectrum"] = TableDataset(data=s1)

>>> # mandatory properties are also in metadata
...  # test mandatory BaseProduct properties that are also metadata
...  a0 = "Me, myself and I"
...  x.creator = a0
...  x.creator   # == a0
'Me, myself and I'

>>> # metada by the same name is also set
...  x.meta["creator"].value   # == a0
'Me, myself and I'

>>> # change the metadata
...  a1 = "or else"
...  x.meta["creator"] = Parameter(a1)
...  # metada changed
...  x.meta["creator"].value   # == a1
'or else'

>>> # so did the property
...  x.creator   # == a1
'or else'

>>> # load some metadata
...  m = x.meta
...  m['a'] = NumericParameter(
...      3.4, 'num par', 'float', 2., {(0, 30): 'nok'})
...  then = datetime(
...      2019, 2, 19, 1, 2, 3, 456789, tzinfo=timezone.utc)
...  m['b'] = DateParameter(FineTime(then), 'date par', default=99,
...                         valid={(0, 9999999999): 'dok'}, typecode='%Y')
...  m['c'] = StringParameter(
...      'Right', 'str par', {'': 'sok'}, 'cliche', 'B')
...  # Demo ``toString()`` function. The result (detail level=0) should be ::
...  print(x.toString())

::
   
   # Product
   meta= {# MetaData
   +--------------+-------------------+--------+----------+----------------------------+-----------------+--------+--------------------+
   | name         | value             | unit   | type     | valid                      | default         | code   | description        |
   +==============+===================+========+==========+============================+=================+========+====================+
   | description  | product example w | -      | string   | None                       | UNKNOWN         | B      | Description of thi |
   |              | ith several datas |        |          |                            |                 |        | s product          |
   |              | ets               |        |          |                            |                 |        |                    |
   +--------------+-------------------+--------+----------+----------------------------+-----------------+--------+--------------------+
   | type         | Product           | -      | string   | None                       | BaseProduct     | B      | Product Type ident |
   |              |                   |        |          |                            |                 |        | ification. Name of |
   |              |                   |        |          |                            |                 |        |  class or CARD.    |
   +--------------+-------------------+--------+----------+----------------------------+-----------------+--------+--------------------+
   | creator      | or else           | -      | string   | None                       | None            | -      | UNKNOWN            |
   +--------------+-------------------+--------+----------+----------------------------+-----------------+--------+--------------------+
   | creationDate | 1958-01-01        | -      | finetime | None                       | 1958-01-01      | -      | Creation date of t |
   |              | 00:00:00.000000   |        |          |                            | 00:00:00.000000 |        | his product        |
   |              | 0                 |        |          |                            | 0               |        |                    |
   +--------------+-------------------+--------+----------+----------------------------+-----------------+--------+--------------------+
   | rootCause    | UNKNOWN           | -      | string   | None                       | UNKNOWN         | B      | Reason of this run |
   |              |                   |        |          |                            |                 |        |  of pipeline.      |
   +--------------+-------------------+--------+----------+----------------------------+-----------------+--------+--------------------+
   | version      | 0.6               | -      | string   | None                       | 0.6             | B      | Version of product |
   |              |                   |        |          |                            |                 |        |  schema            |
   +--------------+-------------------+--------+----------+----------------------------+-----------------+--------+--------------------+
   | startDate    | 1958-01-01        | -      | finetime | None                       | 1958-01-01      | -      | Nominal start time |
   |              | 00:00:00.000000   |        |          |                            | 00:00:00.000000 |        |   of this product. |
   |              | 0                 |        |          |                            | 0               |        |                    |
   +--------------+-------------------+--------+----------+----------------------------+-----------------+--------+--------------------+
   | endDate      | 1958-01-01        | -      | finetime | None                       | 1958-01-01      | -      | Nominal end time   |
   |              | 00:00:00.000000   |        |          |                            | 00:00:00.000000 |        | of this product.   |
   |              | 0                 |        |          |                            | 0               |        |                    |
   +--------------+-------------------+--------+----------+----------------------------+-----------------+--------+--------------------+
   | instrument   | Crystal-Ball      | -      | string   | None                       | UNKNOWN         | B      | Instrument that ge |
   |              |                   |        |          |                            |                 |        | nerated data of th |
   |              |                   |        |          |                            |                 |        | is product         |
   +--------------+-------------------+--------+----------+----------------------------+-----------------+--------+--------------------+
   | modelName    | Mk II             | -      | string   | None                       | UNKNOWN         | B      | Model name of the  |
   |              |                   |        |          |                            |                 |        | instrument of this |
   |              |                   |        |          |                            |                 |        |  product           |
   +--------------+-------------------+--------+----------+----------------------------+-----------------+--------+--------------------+
   | mission      | _AGS              | -      | string   | None                       | _AGS            | B      | Name of the missio |
   |              |                   |        |          |                            |                 |        | n.                 |
   +--------------+-------------------+--------+----------+----------------------------+-----------------+--------+--------------------+
   | a            | 3.4               | None   | float    | [[[0, 30], 'nok']          | 2.0             | None   | num par            |
   |              |                   |        |          | ]                          |                 |        |                    |
   +--------------+-------------------+--------+----------+----------------------------+-----------------+--------+--------------------+
   | b            | 2019-02-19        | -      | finetime | [[[0, 9999999999], 'dok']] | 1958-01-01      | -      | date par           |
   |              | 01:02:03.456789   |        |          |                            | 00:00:00.000099 |        |                    |
   |              | 1929229323456789  |        |          |                            | 99              |        |                    |
   +--------------+-------------------+--------+----------+----------------------------+-----------------+--------+--------------------+
   | c            | Right             | -      | string   | [['', 'sok']]              | cliche          | B      | str par            |
   +--------------+-------------------+--------+----------+----------------------------+-----------------+--------+--------------------+
   MetaData-listeners = ListnerSet{}},
   history= {},
   listeners= {ListnerSet{}}

   # History
   description= {'UNKNOWN'},
   HIST_SCRIPT= {''},
   PARAM_HISTORY= {''},
   TASK_HISTORY= {''},
   meta= {# MetaData
   (empty)
   MetaData-listeners = ListnerSet{}}

   History-datasets =


   Product-datasets =

   #     [ RawImage ]
   # ArrayDataset
   description= {'image1'},
   meta= {# MetaData
   (empty)
   MetaData-listeners = ListnerSet{}},
   type= {None},
   default= {None},
   typecode= {None},
   unit= {'ev'}
   ArrayDataset-dataset =
   1  2  3
   4  5  6
   7  8  9



   #     [ QualityImage ]
   # ArrayDataset
   description= {'UNKNOWN'},
   meta= {# MetaData
   (empty)
   MetaData-listeners = ListnerSet{}},
   type= {None},
   default= {None},
   typecode= {None},
   unit= {None}
   ArrayDataset-dataset =
      0.1  0.5    0.7
   4000    6e+07  8
     -2    0      3.1



   #     [ Spectrum ]
   # TableDataset
   description= {'UNKNOWN'},
   meta= {# MetaData
   (empty)
   MetaData-listeners = ListnerSet{}}
   TableDataset-dataset =
   ======  =======
   col1     col2
   (eV)    (cnt)
   ======  =======
      1        0
      4.4     43.2
   5400     2000
   ======  =======



pal
===

Store a Product in a Pool and Get a Reference Back
--------------------------------------------------


Create a product and a productStorage with a pool registered


>>> # disable debugging messages
...  logger = logging.getLogger('')
...  logger.setLevel(logging.WARNING)

>>> # a pool for demonstration will be create here
...  demopoolpath = '/tmp/demopool_' + getpass.getuser()
...  demopoolurl = 'file://' + demopoolpath
...  # clean possible data left from previous runs
...  os.system('rm -rf ' + demopoolpath)
...  if PoolManager.isLoaded(DEFAULT_MEM_POOL):
...      PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
...  PoolManager.removeAll()

>>> # create a prooduct and save it to a pool
...  x = Product(description='save me in store')
...  # add a tabledataset
...  s1 = [('energy', [1, 4.4, 5.6], 'eV'), ('freq', [0, 43.2, 2E3], 'Hz')]
...  x["Spectrum"] = TableDataset(data=s1)
...  # create a product store
...  pstore = ProductStorage(poolurl=demopoolurl)
...  pstore
ProductStorage { pool= 
#     [ demopool_mh ]
LocalPool { pool= demopool_mh } }

>>> # save the product and get a reference
...  prodref = pstore.save(x)
...  # This gives detailed information of the product being referenced
...  print(prodref)

::
   
   ProductRef {urn:demopool_mh:fdi.dataset.product.Product:0 Parents=[]# MetaData

   --------------------  ---------------  --------------------  --------------------
   description= 'save m  type= 'Product'  creator= 'UNKNOWN'    creationDate= 1958-0
   e in store'                                                  1-01T00:00:00.000000
   TAI(0)
   rootCause= 'UNKNOWN'  version= '0.6'   startDate= 1958-01-0  endDate= 1958-01-01T
   1T00:00:00.000000 TA  00:00:00.000000 TAI(
   I(0)                  0)
   --------------------  ---------------  --------------------  --------------------

   MetaData-listeners = ListnerSet{}}

>>> # get the urn string
...  urn = prodref.urn
...  print(urn)    # urn:demopool_mh:fdi.dataset.product.Product:0
urn:demopool_mh:fdi.dataset.product.Product:0

>>> newp = ProductRef(urn).product
...  # the new and the old one are equal
...  print(newp == x)   # == True
True


Context: a Product with References
----------------------------------


>>> # the reference can be stored in another product of Context class
...  p1 = Product(description='p1')
...  p2 = Product(description='p2')
...  # create an empty mapcontext that can carry references with name labels
...  map1 = MapContext(description='product with refs 1')
...  # A ProductRef created from a lone product will use a mempool
...  pref1 = ProductRef(p1)
...  pref1
ProductRef {urn:defaultmem:fdi.dataset.product.Product:0 Parents=[] meta= None}

>>> # A productStorage with a pool on disk
...  pref2 = pstore.save(p2)
...  pref2.urn
'urn:demopool_mh:fdi.dataset.product.Product:1'

>>> # how many prodrefs do we have? (do not use len() due to classID, version)
...  map1['refs'].size()   # == 0
0

>>> len(pref1.parents)   # == 0
0

>>> len(pref2.parents)   # == 0
0

>>> # add a ref to the contex. every ref has a name in mapcontext
...  map1['refs']['spam'] = pref1
...  # add the second one
...  map1['refs']['egg'] = pref2
...  # how many prodrefs do we have? (do not use len() due to classID, version)
...  map1['refs'].size()   # == 2
2

>>> len(pref2.parents)   # == 1
1

>>> pref2.parents[0] == map1
True

>>> pref1.parents[0] == map1
True

>>> # remove a ref
...  del map1['refs']['spam']
...  # how many prodrefs do we have? (do not use len() due to classID, version)
...  map1.refs.size()   # == 1
1

>>> len(pref1.parents)   # == 0
0

>>> # add ref2 to another map
...  map2 = MapContext(description='product with refs 2')
...  map2.refs['also2'] = pref2
...  map2['refs'].size()   # == 1
1

>>> # two parents
...  len(pref2.parents)   # == 2
2

>>> pref2.parents[1] == map2
True


Query a ProdStorage
-------------------


>>> # clean possible data left from previous runs
...  defaultpoolpath = '/tmp/pool_' + getpass.getuser()
...  newpoolname = 'newpool_' + getpass.getuser()
...  newpoolpath = '/tmp/' + newpoolname
...  os.system('rm -rf ' + defaultpoolpath)
...  os.system('rm -rf ' + newpoolpath)
...  if PoolManager.isLoaded(DEFAULT_MEM_POOL):
...      PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
...  PoolManager.removeAll()
...  # make a productStorage
...  defaultpoolurl = 'file://'+defaultpoolpath
...  pstore = ProductStorage(poolurl=defaultpoolurl)
...  # make another
...  newpoolurl = 'file://' + newpoolpath
...  pstore2 = ProductStorage(poolurl=newpoolurl)

>>> # add some products to both storages
...  n = 7
...  for i in range(n):
...      a0, a1, a2 = 'desc %d' % i, 'fatman %d' % (i*4), 5000+i
...      if i < 3:
...          x = Product(description=a0, instrument=a1)
...          x.meta['extra'] = Parameter(value=a2)
...      elif i < 5:
...          x = Context(description=a0, instrument=a1)
...          x.meta['extra'] = Parameter(value=a2)
...  ...
...          x = MapContext(description=a0, instrument=a1)
...          x.meta['extra'] = Parameter(value=a2)
...          x.meta['time'] = Parameter(value=FineTime1(a2))
...      if i < 4:
...          r = pstore.save(x)
...      else:
...          r = pstore2.save(x)
...      print(r.urn)
...  # Two pools, 7 products
...  # [P P P C] [C M M]

::
   
   urn:pool_mh:fdi.dataset.product.Product:0
   urn:pool_mh:fdi.dataset.product.Product:1
   urn:pool_mh:fdi.dataset.product.Product:2
   urn:pool_mh:fdi.pal.context.Context:0
   urn:newpool_mh:fdi.pal.context.Context:0
   urn:newpool_mh:fdi.pal.context.MapContext:0
   urn:newpool_mh:fdi.pal.context.MapContext:1

>>> # register the new pool above to the  1st productStorage
...  pstore.register(newpoolname)
...  len(pstore.getPools())   # == 2
2

>>> # make a query on product metadata, which is the variable 'm'
...  # in the query expression, i.e. ``m = product.meta; ...``
...  # But '5000 < m["extra"]' does not work. see tests/test.py.
...  q = MetaQuery(Product, 'm["extra"] > 5001 and m["extra"] <= 5005')
...  # search all pools registered on pstore
...  res = pstore.select(q)
...  # [2,3,4,5]
...  len(res)   # == 4
...  [r.product.description for r in res]
['desc 2', 'desc 3', 'desc 4', 'desc 5']

>>> def t(m):
...      # query is a function
...      import re
...      return re.match('.*n.1.*', m['instrument'].value)

>>> q = MetaQuery(Product, t)
...  res = pstore.select(q)
...  # [3,4]
...  [r.product.instrument for r in res]
['fatman 12', 'fatman 16']

>>> # same as above but query is on the product. this is slow.
...  q = AbstractQuery(Product, 'p', '"n 1" in p.instrument')
...  res = pstore.select(q)
...  # [3,4]
...  [r.product.instrument for r in res]
['fatman 12', 'fatman 16']

>>> 

pns
===

See the installation and testing sections of the pns page.


.. tip::
   
   The demo above was made by running ``fdi/resources/example.py`` with command ``elpy-shell-send-group-and-step [c-c c-y c-g]`` in ``emacs``. The command is further simplified to control-<tab> with the following in ~/.init.el:
   
   .. code-block::

      (add-hook 'elpy-mode-hook (lambda () (local-set-key \
          [C-tab] (quote elpy-shell-send-group-and-step))))
