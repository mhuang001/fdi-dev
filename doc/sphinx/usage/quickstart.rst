
================
Quick Start
================

.. contents:: Contents:

   
The following quick start tutorial shows important ``dataset`` and ``pal`` functionalities.

.. tip::
   
   You can copy the code from code blocks by clicking the ``copy`` icon on the top-right, with he prompts and results removed.

.. highlight:: none

	       
>>> # Import these packages needed in the tutorial
... from fdi.dataset.product import Product
... from fdi.dataset.metadata import Parameter, NumericParameter, MetaData, StringParameter, DateParameter
... from fdi.dataset.finetime import FineTime, FineTime1
... from fdi.dataset.dataset import ArrayDataset, TableDataset, Column
... from fdi.dataset.classes import Classes
... from fdi.pal.context import Context, MapContext
... from fdi.pal.productref import ProductRef
... from fdi.pal.query import AbstractQuery, MetaQuery
... from fdi.pal.poolmanager import PoolManager, DEFAULT_MEM_POOL
... from fdi.pal.productstorage import ProductStorage
... import getpass
... import os
... from datetime import datetime, timezone
... import logging

>>> # initialize the white-listed class dictionary
... cmap = Classes.updateMapping()


dataset
=======

First we show how to make and use components of the data model.

This section shows how to create data containers -- datasets, metadata, and Products, how to put data into the containers, read data out, modify data, remove data, inspect data.

ArrayDataset
------------


>>> # Creation with an array of data quickly
... a1 = [1, 4.4, 5.4E3, -22, 0xa2]
... v = ArrayDataset(a1)
... # Show it. This is the same as print(v) in a non-interactive environment.
... v
# ArrayDataset
description= {'UNKNOWN'},
meta= {
(empty)
MetaData-listeners = ListnerSet{}
},
type= {None},
default= {None},
typecode= {None},
unit= {None}
ArrayDataset-dataset =
1  4.4  5400  -22  162

>>> # Do it with built-in properties set.
... v = ArrayDataset(data=a1, unit='ev', description='5 elements',
...                  typ_='float', default=1.0, typecode='f')
... v
# ArrayDataset
description= {'5 elements'},
meta= {
(empty)
MetaData-listeners = ListnerSet{}
},
type= {'float'},
default= {1.0},
typecode= {'f'},
unit= {'ev'}
ArrayDataset-dataset =
1  4.4  5400  -22  162

>>> # add some metadats (see more about meta data below)
... v.meta['greeting'] = StringParameter('Hi there.')
... v.meta['year'] = NumericParameter(2020)
... v
# ArrayDataset
description= {'5 elements'},
meta= {
-------------------  ----------
greeting= Hi there.  year= 2020
-------------------  ----------
MetaData-listeners = ListnerSet{}
},
type= {'float'},
default= {1.0},
typecode= {'f'},
unit= {'ev'}
ArrayDataset-dataset =
1  4.4  5400  -22  162

>>> # data access: read the 2nd array element
... v[2]       # 5400
5400.0

>>> # built-in properties
... v.unit
'ev'

>>> # change it
... v.unit = 'm'
... v.unit
'm'

>>> # iteration
... for m in v:
...     print(m + 1)
2
5.4
5401.0
-21
163

>>> # a filter example
... [m**3 for m in v if m > 0 and m < 40]
[1, 85.18400000000003]

>>> # slice the ArrayDataset and only get part of its data
... v[2:-1]
[5400.0, -22]

>>> # set data to be a 2D array
... v.data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
... # slicing happens on the slowest dimension.
... v[0:2]
[[1, 2, 3], [4, 5, 6]]

>>> # Run this to see a demo of the ``toString()`` function::
... # make a 4-D array: a list of 2 lists of 3 lists of 4 lists of 5 elements.
... s = [[[[i + j + k + l for i in range(5)] for j in range(4)]
...       for k in range(3)] for l in range(2)]
... v.data = s
... print(v.toString())

::
   
   # ArrayDataset
   description= {'5 elements'},
   meta= {
   +----------+-----------+--------+---------+---------+-----------+--------+---------------+
   | name     | value     | unit   | type    | valid   | default   | code   | description   |
   +==========+===========+========+=========+=========+===========+========+===============+
   | greeting | Hi there. |        | string  | None    |           | B      | UNKNOWN       |
   +----------+-----------+--------+---------+---------+-----------+--------+---------------+
   | year     | 2020      | None   | integer | None    | None      | None   | UNKNOWN       |
   +----------+-----------+--------+---------+---------+-----------+--------+---------------+
   MetaData-listeners = ListnerSet{}},
   type= {'float'},
   default= {1.0},
   typecode= {'f'},
   unit= {'m'}
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

TableDataset is mainly a dictionary containing name-Column pairs and metadata.
Columns are basically ArrayDatasets under a different name.


>>> # Creation with a list of dicts with column names, data, and unit information.
... a1 = [dict(name='col1', unit='eV', column=[1, 4.4, 5.4E3]),
...       dict(name='col2', unit='cnt', column=[0, 43.2, 2E3])
...       ]
... v = TableDataset(data=a1)
... v
# TableDataset
description= {'UNKNOWN'},
meta= {
(empty)
MetaData-listeners = ListnerSet{}
}
TableDataset-dataset =
  col1     col2
  (eV)    (cnt)
------  -------
   1        0
   4.4     43.2
5400     2000

>>> # One of many other ways to create a TableDataset. See ``tests/test_dataset``
... v3 = TableDataset(data=[('col1', [1, 4.4, 5.4E3], 'eV'),
...                         ('col2', [0, 43.2, 2E3], 'cnt')])
... v == v3
True

>>> # Make a quick tabledataset. data are list of lists without names or units
... a5 = [[1, 4.4, 5.4E3], [0, 43.2, 2E3]]
... v5 = TableDataset(data=a5)
... print(v5.toString())
# TableDataset
description= {'UNKNOWN'},
meta= {
(empty)
MetaData-listeners = ListnerSet{}}
TableDataset-dataset =
    col1      col2
  (None)    (None)
--------  --------
     1         0
     4.4      43.2
  5400      2000




>>> # access
... # get names of all columns
... v5.getColumnNames()
['col1', 'col2']

>>> # get a list of all columns' data
... [c.data for c in v5.data.values()]   # == a5
[[1, 4.4, 5400.0], [0, 43.2, 2000.0]]

>>> # get column by name
... my_column = v5['col1']
... my_column
# Column
description= {'UNKNOWN'},
meta= {
(empty)
MetaData-listeners = ListnerSet{}
},
type= {None},
default= {None},
typecode= {None},
unit= {None}
Column-dataset =
1  4.4  5400

>>> #  indexOf by name
... v5.indexOf('col1')  # == u.indexOf(my_column)
0

>>> #  indexOf by column object
... v5.indexOf(my_column)
0

>>> # set cell value
... v5['col2'][1] = 123
... v5['col2'][1]    # 123
123

>>> # unit access
... v3['col1'].unit  # == 'eV'
'eV'

>>> # add, set, and replace columns and rows
... # column set / get
... u = TableDataset()
... c1 = Column([1, 4], 'sec')
... # add
... u.addColumn('time', c1)
... u.columnCount        # 1
1

>>> # for non-existing names set is addColum.
... u['money'] = Column([2, 3], 'eu')
... u['money'][0]    # 2
... # column increases
... u.columnCount        # 2
2

>>> # addRow
... u.rowCount    # 2
2

>>> u.addRow({'money': 4.4, 'time': 3.3})
... u.rowCount    # 3
3

>>> # syntax ``in``
... [c for c in u]  # list of column names ['time', 'money']
['time', 'money']

>>> # run this to see ``toString()``
... ELECTRON_VOLTS = 'eV'
... SECONDS = 'sec'
... t = [x * 1.0 for x in range(10)]
... e = [2.5 * x + 100 for x in t]
... # creating a table dataset to hold the quantified data
... x = TableDataset(description="Example table")
... x["Time"] = Column(data=t, unit=SECONDS)
... x["Energy"] = Column(data=e, unit=ELECTRON_VOLTS)
... print(x.toString())
# TableDataset
description= {'Example table'},
meta= {
(empty)
MetaData-listeners = ListnerSet{}}
TableDataset-dataset =
   Time    Energy
  (sec)      (eV)
-------  --------
      0     100
      1     102.5
      2     105
      3     107.5
      4     110
      5     112.5
      6     115
      7     117.5
      8     120
      9     122.5


MetaData and Parameter: Parameter
---------------------------------

FDI datasets and products not only contain data, but also their metadata -- data about the "payload" data. Metadata is a collections of parameters.

A Parameter is a variable with associated information about its description, unit, type, valid ranges, default, format code etc. Type can be numeric, string, datetime, vector.

Often a parameter shows a property. So a parameter in the metadata of a dataset or product is often called a property.


>>> # Creation
... # The standard way -- with keyword arguments
... v = Parameter(value=9000, description='Average age', typ_='integer')
... v.description   # 'Average age'
'Average age'

>>> v.value   # == 9000
9000

>>> v.type   # == 'integer'
'integer'

>>> # test equals.
... # FDI DeepEqual integerface class recursively compares all components.
... v1 = Parameter(description='Average age', value=9000, typ_='integer')
... v.equals(v1)
True

>>> # more readable 'equals' syntax
... v == v1
True

>>> # make them not equal.
... v1.value = -4
... v.equals(v1)   # False
False

>>> # math syntax
... v != v1  # True
True

>>> # NumericParameter with two valid values and a valid range.
... v = NumericParameter(value=9000, valid={
...                      0: 'OK1', 1: 'OK2', (100, 9900): 'Go!'})
... # There are thee valid conditions
... v
Go! (9000)

>>> # The current value is valid
... v.isvalid()
True

>>> # check if other values are valid according to specification of this parameter
... v.validate(600)  # valid
(600, 'Go!')

>>> v.validate(20)  # invalid
(Invalid, 'Invalid')


MetaData and Parameter: Metadata
--------------------------------

A dict-like container for named parameters.


>>> # Creation. Start with numeric parameter.
... a1 = 'weight'
... a2 = NumericParameter(description='How heavey is the robot.',
...                       value=60, unit='kg', typ_='float')
... # make an empty MetaData instance.
... v = MetaData()
... # place the parameter with a name
... v.set(a1, a2)
... # get the parameter with the name.
... v.get(a1)   # == a2
60.0

>>> # add more parameter. Try a string type.
... v.set(name='job', newParameter=StringParameter('pilot'))
... # get the value of the parameter
... v.get('job').value   # == 'pilot'
'pilot'

>>> # access parameters in metadata
... # a more readable way to set/get a parameter than "v.set(a1,a2)", "v.get(a1)"
... v['job'] = StringParameter('waitor')
... v['job']   # == waitor
waitor

>>> # same result as...
... v.get('job')
waitor

>>> # Date type parameter use International Atomic Time (TAI) to keep time,
... # in 1-microsecond precission
... v['birthday'] = Parameter(description='was born on',
...                           value=FineTime('1990-09-09T12:34:56.789098 UTC'))
... # FDI use International Atomic Time (TAI) internally to record time.
... # The format is the integer number of microseconds since 1958-01-01 00:00:00 UTC.
... v['birthday'].value.tai
1031574896789098

>>> # names of all parameters
... [n for n in v]   # == ['weight', 'job', 'birthday']
['weight', 'job', 'birthday']

>>> # remove parameter from metadata.   # function inherited from Composite class.
... v.remove(a1)
... v.size()  # == 2
2


>>> # string representation. This is the same as v.toString(level=0), most detailed.
...: print(v.toString())

::
   
   +----------+------------------+--------+----------+---------+-----------+--------+---------------+
   | name     | value            | unit   | type     | valid   | default   | code   | description   |
   +==========+==================+========+==========+=========+===========+========+===============+
   | job      | waitress         |        | string   | None    |           | B      | UNKNOWN       |
   +----------+------------------+--------+----------+---------+-----------+--------+---------------+
   | birthday | 1990-09-09       |        | finetime | None    | None      |        | was born on   |
   |          | 12:34:56.789098  |        |          |         |           |        |               |
   |          | 1031574896789098 |        |          |         |           |        |               |
   +----------+------------------+--------+----------+---------+-----------+--------+---------------+
   MetaData-listeners = ListnerSet{}

>>> # simplifed string representation, toString(level=1), also what __repr__() runs.
...: v

::
   
   -------------  --------------------
   job= waitress  birthday= 1990-09-09
   12:34:56.789098
   1031574896789098
   -------------  --------------------
   MetaData-listeners = ListnerSet{}

>>> # simplest string representation, toString(level=2).
...: print(v.toString(level=2))
job, birthday, listeners = ListnerSet{}



Product
-------

The data Product is at the center of FDI data model. A product has
   * zero or more datasets (say images, tables, spectra etc...).
   * accompanying metadata,
   * history of this product: how was this data created.


>>> # Creation:
... x = Product(description="product example with several datasets",
...             instrument="Crystal-Ball", modelName="Mk II")
... x.meta['description'].value  # == "product example with several datasets"
'product example with several datasets'

>>> # The 'instrument' and 'modelName' built-in properties show the
... # origin of FDI -- processing data from scientific instruments.
... x.instrument  # == "Crystal-Ball"
'Crystal-Ball'

>>> # ways to add datasets
... i0 = 6
... i1 = [[1, 2, 3], [4, 5, i0], [7, 8, 9]]
... i2 = 'ev'                 # unit
... i3 = 'image1'     # description
... image = ArrayDataset(data=i1, unit=i2, description=i3)
... x["RawImage"] = image
... x["RawImage"].data  # == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
[[1, 2, 3], [4, 5, 6], [7, 8, 9]]

>>> # no unit or description. different syntax but same function as above
... x.set('QualityImage', ArrayDataset(
...     [[0.1, 0.5, 0.7], [4e3, 6e7, 8], [-2, 0, 3.1]]))
... x["QualityImage"].unit  # is None

>>> # add a tabledataset
... s1 = [('col1', [1, 4.4, 5.4E3], 'eV'),
...       ('col2', [0, 43.2, 2E3], 'cnt')]
... x["Spectrum"] = TableDataset(data=s1)

>>> # mandatory properties are also in metadata
... # test mandatory BaseProduct properties that are also metadata
... a0 = "Me, myself and I"
... x.creator = a0
... x.creator   # == a0
'Me, myself and I'

>>> # metada by the same name is also set
... x.meta["creator"].value   # == a0
'Me, myself and I'

>>> # change the metadata
... a1 = "or else"
... x.meta["creator"] = Parameter(a1)
... # metada changed
... x.meta["creator"].value   # == a1
'or else'

>>> # so did the property
... x.creator   # == a1
'or else'

>>> # load some metadata
... m = x.meta
... m['a'] = NumericParameter(
...     3.4, 'rule name, if is "valid", "", or "default", is ommited in value string.', 'float', 2., {(0, 31): 'valid', 99: ''})
... then = datetime(
...     2019, 2, 19, 1, 2, 3, 456789, tzinfo=timezone.utc)
... m['b'] = DateParameter(FineTime(then), 'date param', default=99,
...                        valid={(0, 9876543210123456): 'ever'}, typecode='%Y')
... m['c'] = StringParameter(
...     'Right', 'str parameter. but only "" is allowed.', {'': 'empty'}, 'cliche', 'B')
... m['d'] = NumericParameter(
...     0b01, 'valid rules described with binary masks', 'binary', 0b00, {(0b0110, 0b01): 'on', (0b0110, 0b00): 'off'})
... # Demo ``toString()`` function.
... print(x.toString())


::
   
   # Product
   meta= {
   +--------------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
   | name         | value             | unit   | type     | valid                | default         | code   | description       |
   +==============+===================+========+==========+======================+=================+========+===================+
   | description  | product example w |        | string   | None                 | UNKNOWN         | B      | Description of th |
   |              | ith several datas |        |          |                      |                 |        | is product        |
   |              | ets               |        |          |                      |                 |        |                   |
   +--------------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
   | type         | Product           |        | string   | None                 | BaseProduct     | B      | Product Type iden |
   |              |                   |        |          |                      |                 |        | tification. Name  |
   |              |                   |        |          |                      |                 |        | of class or CARD. |
   +--------------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
   | creator      | or else           |        | string   | None                 | None            |        | UNKNOWN           |
   +--------------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
   | creationDate | 1958-01-01        |        | finetime | None                 | 1958-01-01      |        | Creation date of  |
   |              | 00:00:00.000000   |        |          |                      | 00:00:00.000000 |        | this product      |
   |              | 0                 |        |          |                      | 0               |        |                   |
   +--------------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
   | rootCause    | UNKNOWN           |        | string   | None                 | UNKNOWN         | B      | Reason of this ru |
   |              |                   |        |          |                      |                 |        | n of pipeline.    |
   +--------------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
   | version      | 0.7               |        | string   | None                 | 0.7             | B      | Version of produc |
   |              |                   |        |          |                      |                 |        | t schema          |
   +--------------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
   | startDate    | 1958-01-01        |        | finetime | None                 | 1958-01-01      |        | Nominal start tim |
   |              | 00:00:00.000000   |        |          |                      | 00:00:00.000000 |        | e  of this produc |
   |              | 0                 |        |          |                      | 0               |        | t.                |
   +--------------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
   | endDate      | 1958-01-01        |        | finetime | None                 | 1958-01-01      |        | Nominal end time  |
   |              | 00:00:00.000000   |        |          |                      | 00:00:00.000000 |        |  of this product. |
   |              | 0                 |        |          |                      | 0               |        |                   |
   +--------------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
   | instrument   | Crystal-Ball      |        | string   | None                 | UNKNOWN         | B      | Instrument that g |
   |              |                   |        |          |                      |                 |        | enerated data of  |
   |              |                   |        |          |                      |                 |        | this product      |
   +--------------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
   | modelName    | Mk II             |        | string   | None                 | UNKNOWN         | B      | Model name of the |
   |              |                   |        |          |                      |                 |        |  instrument of th |
   |              |                   |        |          |                      |                 |        | is product        |
   +--------------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
   | mission      | _AGS              |        | string   | None                 | _AGS            | B      | Name of the missi |
   |              |                   |        |          |                      |                 |        | on.               |
   +--------------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
   | a            | 3.4               | None   | float    | (0, 31): valid       | 2.0             | None   | rule name, if is  |
   |              |                   |        |          | 99:                  |                 |        | "valid", "", or " |
   |              |                   |        |          |                      |                 |        | default", is ommi |
   |              |                   |        |          |                      |                 |        | ted in value stri |
   |              |                   |        |          |                      |                 |        | ng.               |
   +--------------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
   | b            | ever (2019-02-19  |        | finetime | [(0, 987654321012345 | 1958-01-01      |        | date param        |
   |              | 01:02:03.456789   |        |          | 6): ever]            | 00:00:00.000099 |        |                   |
   |              | 1929229323456789) |        |          |                      | 99              |        |                   |
   +--------------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
   | c            | Invalid (Right)   |        | string   | '': empty            | cliche          | B      | str parameter. bu |
   |              |                   |        |          |                      |                 |        | t only "" is allo |
   |              |                   |        |          |                      |                 |        | wed.              |
   +--------------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
   | d            | off (0b0)         | None   | binary   | (0b110, 0b1): on     | 0b0             | None   | valid rules descr |
   |              |                   |        |          | (0b110, 0b0): off    |                 |        | ibed with binary  |
   |              |                   |        |          |                      |                 |        | masks             |
   +--------------+-------------------+--------+----------+----------------------+-----------------+--------+-------------------+
   MetaData-listeners = ListnerSet{}},
   history= {},
   listeners= {ListnerSet{}}
   
   # History
   description= {'UNKNOWN'},
   HIST_SCRIPT= {''},
   PARAM_HISTORY= {''},
   TASK_HISTORY= {''},
   meta= {
   (empty)
   MetaData-listeners = ListnerSet{}}
   
   History-datasets =
   
   
   Product-datasets =
   
   #     [ RawImage ]
   # ArrayDataset
   description= {'image1'},
   meta= {
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
   meta= {
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
   meta= {
   (empty)
   MetaData-listeners = ListnerSet{}}
   TableDataset-dataset =
     col1     col2
     (eV)    (cnt)
   ------  -------
      1        0
      4.4     43.2
   5400     2000
   


pal
===

Products need to persist (be stored somewhere) in order to have a reference that can be used to re-create the product after its creation process ends.

Product Pool and Product References
-----------------------------------

This section shows how to store a product in a "pool" and get a reference back.


>>> # Create a product and a productStorage with a pool registered
... # First disable debugging messages
... logger = logging.getLogger('')
... logger.setLevel(logging.WARNING)
... # a pool (LocalPool) for demonstration will be create here
... demopoolpath = '/tmp/demopool_' + getpass.getuser()
... demopoolurl = 'file://' + demopoolpath
... # clean possible data left from previous runs
... os.system('rm -rf ' + demopoolpath)
... if PoolManager.isLoaded(DEFAULT_MEM_POOL):
...     PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
... PoolManager.removeAll()

>>> # create a prooduct and save it to a pool
... x = Product(description='save me in store')
... # add a tabledataset
... s1 = [('energy', [1, 4.4, 5.6], 'eV'), ('freq', [0, 43.2, 2E3], 'Hz')]
... x["Spectrum"] = TableDataset(data=s1)
... # create a product store
... pstore = ProductStorage(poolurl=demopoolurl)
... # see what is in it.
... pstore
ProductStorage { pool= 
#     [ demopool_mh ]
LocalPool { pool= demopool_mh } }

>>> # save the product and get a reference back.
... prodref = pstore.save(x)
... # This gives detailed information of the product being referenced
... print(prodref)
ProductRef {urn:demopool_mh:fdi.dataset.product.Product:0 Parents=[]
--------------------------  -------------------  -------------------
description= save me in st  type= Product        creator= UNKNOWN
ore
creationDate= 1958-01-01    rootCause= UNKNOWN   version= 0.7
00:00:00.000000
0
startDate= 1958-01-01       endDate= 1958-01-01  instrument= UNKNOWN
00:00:00.000000             00:00:00.000000
0                           0
modelName= UNKNOWN          mission= _AGS
--------------------------  -------------------  -------------------
MetaData-listeners = ListnerSet{}}

>>> # get the URN string
... urn = prodref.urn
... print(urn)    # urn:demopool_mh:fdi.dataset.product.Product:0
urn:demopool_mh:fdi.dataset.product.Product:0

>>> # re-create a product only using the urn
... newp = ProductRef(urn).product
... # the new and the old one are equal
... print(newp == x)   # == True
True


Context
-------

A Context is a Product with References. This section shows essencial steps how product references can be stored in a context.



>>> p1 = Product(description='p1')
... p2 = Product(description='p2')
... # create an empty mapcontext that can carry references with name labels
... map1 = MapContext(description='product with refs 1')
... # A ProductRef created with the syntax of a lone product argument will use a MemPool
... pref1 = ProductRef(p1)
... pref1
ProductRef {urn:defaultmem:fdi.dataset.product.Product:0 Parents=[] meta= None}

>>> # A productStorage with a LocalPool -- a pool on the disk.
... pref2 = pstore.save(p2)
... pref2.urn
'urn:demopool_mh:fdi.dataset.product.Product:1'

>>> # how many prodrefs do we have?
... map1['refs'].size()   # == 0
0

>>> # how many 'parents' do these prodrefs have before saved?
... len(pref1.parents)   # == 0
0

>>> len(pref2.parents)   # == 0
0

>>> # add a ref to the context. Every productref has a name in a MapContext
... map1['refs']['spam'] = pref1
... # add the second one
... map1['refs']['egg'] = pref2
... # how many prodrefs do we have?
... map1['refs'].size()   # == 2
2

>>> # parent list of the productref object now has an entry
... len(pref2.parents)   # == 1
1

>>> pref2.parents[0] == map1
True

>>> pref1.parents[0] == map1
True

>>> # remove a ref
... del map1['refs']['spam']
... map1.refs.size()   # == 1
1

>>> # how many prodrefs do we have?
... len(pref1.parents)   # == 0
0

>>> # add ref2 to another map
... map2 = MapContext(description='product with refs 2')
... map2.refs['also2'] = pref2
... map2['refs'].size()   # == 1
1

>>> # two parents
... len(pref2.parents)   # == 2
2

>>> pref2.parents[1] == map2
True


Query
-----

A ProductStorage with pools attached can be queried with tags, properties stored in metadata, or even data in the stored products, with Python syntax.


>>> # clean possible data left from previous runs
... defaultpoolpath = '/tmp/pool_' + getpass.getuser()
... newpoolname = 'newpool_' + getpass.getuser()
... newpoolpath = '/tmp/' + newpoolname
... os.system('rm -rf ' + defaultpoolpath)
... os.system('rm -rf ' + newpoolpath)
... if PoolManager.isLoaded(DEFAULT_MEM_POOL):
...     PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
... PoolManager.removeAll()
... # make a productStorage
... defaultpoolurl = 'file://'+defaultpoolpath
... pstore = ProductStorage(poolurl=defaultpoolurl)
... # make another
... newpoolurl = 'file://' + newpoolpath
... pstore2 = ProductStorage(poolurl=newpoolurl)

>>> # add some products to both storages. The product properties are different.
... n = 7
... for i in range(n):
...     # three counters for properties to be queried.
...     a0, a1, a2 = 'desc %d' % i, 'fatman %d' % (i*4), 5000+i
...     if i < 3:
...         # Product type
...         x = Product(description=a0, instrument=a1)
...         x.meta['extra'] = Parameter(value=a2)
...     elif i < 5:
... ...
...         x.meta['time'] = Parameter(value=FineTime1(a2))
...     if i < 4:
...         # some are stored in one pool
...         r = pstore.save(x)
...     else:
...         # some the other
...         r = pstore2.save(x)
...     print(r.urn)
... # Two pools, 7 products in 3 types
... # [P P P C] [C M M]
urn:pool_mh:fdi.dataset.product.Product:0
urn:pool_mh:fdi.dataset.product.Product:1
urn:pool_mh:fdi.dataset.product.Product:2
urn:pool_mh:fdi.pal.context.Context:0
urn:newpool_mh:fdi.pal.context.Context:0
urn:newpool_mh:fdi.pal.context.MapContext:0
urn:newpool_mh:fdi.pal.context.MapContext:1

>>> # register the new pool above to the  1st productStorage
... pstore.register(newpoolname)
... len(pstore.getPools())   # == 2
2

>>> # make a query on product metadata, which is the variable 'm'
... # in the query expression, i.e. ``m = product.meta; ...``
... # But '5000 < m["extra"]' does not work. see tests/test.py.
... q = MetaQuery(Product, 'm["extra"] > 5001 and m["extra"] <= 5005')
... # search all pools registered on pstore
... res = pstore.select(q)
... # we expect [#2, #3, #4, #5]
... len(res)   # == 4
4

>>> # see
... [r.product.description for r in res]
['desc 2', 'desc 3', 'desc 4', 'desc 5']

>>> def t(m):
...     # query is a function
...     import re
...     # 'instrument' matches the regex pattern
...     return re.match('.*n.1.*', m['instrument'].value)

>>> q = MetaQuery(Product, t)
... res = pstore.select(q)
... # expecting [3,4]
... [r.product.instrument for r in res]
['fatman 12', 'fatman 16']

>>> # same as above but query is on the product. this is slow.
... q = AbstractQuery(Product, 'p', '"n 1" in p.instrument')
... res = pstore.select(q)
... # [3,4]
... [r.product.instrument for r in res]
['fatman 12', 'fatman 16']

See the installation and testing sections of the pns page.


.. tip::
   
   The demo above was made by running ``fdi/resources/example.py`` with command ``elpy-shell-send-group-and-step [c-c c-y c-g]`` in ``emacs``. The command is further simplified to control-<tab> with the following in ~/.init.el:
   
   .. code-block::

      (add-hook 'elpy-mode-hook (lambda () (local-set-key \
          [C-tab] (quote elpy-shell-send-group-and-step))))
