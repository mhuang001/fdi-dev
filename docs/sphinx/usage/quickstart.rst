
================
Quick Start
================

.. contents:: Contents:

   
The following quick start tutorial shows important ``dataset`` and ``pal`` functionalities.

Colors in examples:

>>> # Yellow: comments and explanation.
... if in code:
...    color = 'highlighted'
Cyan: for output.


.. tip::
   
   You can copy the code from code blocks by clicking the ``copy`` icon on the top-right, with he prompts and results removed.

.. highlight:: none

	       
>>> # Import these packages needed in the tutorial
... from fdi.dataset.product import Product, BaseProduct
... from fdi.dataset.metadata import Parameter, MetaData
... from fdi.dataset.numericparameter import NumericParameter
... from fdi.dataset.stringparameter import StringParameter
... from fdi.dataset.dateparameter import DateParameter
... from fdi.dataset.finetime import FineTime, FineTime1
... from fdi.dataset.arraydataset import ArrayDataset, Column
... from fdi.dataset.tabledataset import TableDataset
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

ArrayDataset -- sequence of data in the same unit and format
------------------------------------------------------------


>>> # Creation with an array of data quickly
... a1 = [1, 4.4, 5.4E3, -22, 0xa2]
... v = ArrayDataset(a1)
... # Show it. This is the same as print(v) in a non-interactive environment.
... # "Default Meta." means the metadata settings are all default values.
... v
ArrayDataset(Default Meta. data= [1, 4.4, 5400.0, -22, 162])

>>> # Create an ArrayDataset with some built-in properties set.
... v = ArrayDataset(data=a1, unit='ev', description='5 elements', typecode='f')
... #
... # add some metadats (see more about meta data below)
... v.meta['greeting'] = StringParameter('Hi there.')
... v.meta['year'] = NumericParameter(2020)
... v
ArrayDataset(description=5 elements, unit=ev, typecode=f, greeting=Hi there., year=2020. data= [1, 4.4, 5400.0, -22, 162])

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

>>> # Run this to see a demo of the ``toString()`` function:
... # make a 4-D array: a list of 2 lists of 3 lists of 4 lists of 5 elements.
... s = [[[[i + j + k + l for i in range(5)] for j in range(4)]
...       for k in range(3)] for l in range(2)]
... v.data = s
... print(v.toString())

::

   === ArrayDataset () ===
   meta= {
   ===========  ==========  ======  =======  =======  =========  ======  =====================
   name         value       unit    type     valid    default    code    description
   ===========  ==========  ======  =======  =======  =========  ======  =====================
   description  5 elements          string   None     UNKNOWN    B       Description of this d
   ataset
   unit         m                   string   None     None       B       Unit of every element
   .
   shape        ()                  tuple    None     ()                 Number of elements in
   each dimension. Quic
   k changers to the rig
   ht.
   typecode     f                   string   None     UNKNOWN    B       Python internal stora
   ge code.
   version      0.1                 string   None     0.1        B       Version of dataset
   FORMATV      1.6.0.1             string   None     1.6.0.1    B       Version of dataset sc
   hema and revision
   greeting     Hi there.           string   None                B       UNKNOWN
   year         2020        None    integer  None     None       None    UNKNOWN
   ===========  ==========  ======  =======  =======  =========  ======  =====================
   MetaData-listeners = ListnerSet{}}
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



TableDataset -- a set of named Columns and their metadata
---------------------------------------------------------

TableDataset is mainly a dictionary containing named :class:`Column`\s and their metadata. Columns are basically ArrayDatasets under a different name.


>>> # Create an empty TableDataset then add columns one by one
... v = TableDataset()
... v['col1'] = Column(data=[1, 4.4, 5.4E3], unit='eV')
... v['col2'] = Column(data=[0, 43.2, 2E3], unit='cnt')
... v
TableDataset(Default Meta.data= {"col1": Column(unit=eV. data= [1, 4.4, 5400.0]), "col2": Column(unit=cnt. data= [0, 43.2, 2000.0])})

>>> # Do it with another syntax, with a list of tuples and no Column()
... a1 = [('col1', [1, 4.4, 5.4E3], 'eV'),
...       ('col2', [0, 43.2, 2E3], 'cnt')]
... v1 = TableDataset(data=a1)
... v == v1
True

>>> # Make a quick tabledataset -- data are list of lists without names or units
... a5 = [[1, 4.4, 5.4E3], [0, 43.2, 2E3], [True, True, False], ['A', 'BB', 'CCC']]
... v5 = TableDataset(data=a5)
... print(v5.toString())
=== TableDataset () ===
meta= {
===========  =======  ======  ======  =======  =========  ======  =====================
name         value    unit    type    valid    default    code    description
===========  =======  ======  ======  =======  =========  ======  =====================
description  UNKNOWN          string  None     UNKNOWN    B       Description of this d
                                                                  ataset
version      0.1              string  None     0.1        B       Version of dataset
FORMATV      1.6.0.1          string  None     1.6.0.1    B       Version of dataset sc
                                                                  hema and revision
===========  =======  ======  ======  =======  =========  ======  =====================
MetaData-listeners = ListnerSet{}}
TableDataset-dataset =
  column1    column2  column3    column4
   (None)     (None)  (None)     (None)
---------  ---------  ---------  ---------
      1          0    True       A
      4.4       43.2  True       BB
   5400       2000    False      CCC




>>> # access
... # get names of all columns (automatically given here)
... v5.getColumnNames()
['column1', 'column2', 'column3', 'column4']

>>> # get column by name
... my_column = v5['column1']       # [1, 4.4, 5.4E3]
... my_column.data
[1, 4.4, 5400.0]

>>> # by index
... v5[0].data       # [1, 4.4, 5.4E3]
[1, 4.4, 5400.0]

>>> # get a list of all columns' data.
... # Note the slice "v5[:]" and syntax ``in``
... [c.data for c in v5[:]]   # == a5
[[1, 4.4, 5400.0], [0, 43.2, 2000.0], [True, True, False], ['A', 'BB', 'CCC']]

>>> #  indexOf by name
... v5.indexOf('column1')  # == u.indexOf(my_column)
0

>>> #  indexOf by column object
... v5.indexOf(my_column)     # 0
0

>>> # set cell value
... v5['column2'][1] = 123
... v5['column2'][1]    # 123
123

>>> # row access bu row index -- multiple and in custom order
... v5.getRow([2, 1])  # [(5400.0, 2000.0, False, 'CCC'), (4.4, 123, True, 'BB')]
[(5400.0, 2000.0, False, 'CCC'), (4.4, 123, True, 'BB')]

>>> # or with a slice
... v5.getRow(slice(0, -1))
[(1, 0, True, 'A'), (4.4, 123, True, 'BB')]

>>> # unit access
... v1['col1'].unit  # == 'eV'
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

>>> # run this to see ``toString()``
... ELECTRON_VOLTS = 'eV'
... SECONDS = 'sec'
... t = [x * 1.0 for x in range(8)]
... e = [2.5 * x + 100 for x in t]
... d = [765 * x - 500 for x in t]
... # creating a table dataset to hold the quantified data
... x = TableDataset(description="Example table")
... x["Time"] = Column(data=t, unit=SECONDS)
... x["Energy"] = Column(data=e, unit=ELECTRON_VOLTS)
... x["Distance"] = Column(data=d, unit='m')
... # metadata is optional
... x.meta['temp'] = NumericParameter(42.6, description='Ambient', unit='C')
... print(x.toString())
=== TableDataset () ===
meta= {
===========  =============  ======  ======  =======  =========  ======  =====================
name         value          unit    type    valid    default    code    description
===========  =============  ======  ======  =======  =========  ======  =====================
description  Example table          string  None     UNKNOWN    B       Description of this d
                                                                        ataset
version      0.1                    string  None     0.1        B       Version of dataset
FORMATV      1.6.0.1                string  None     1.6.0.1    B       Version of dataset sc
                                                                        hema and revision
temp         42.6           C       float   None     None       None    Ambient
===========  =============  ======  ======  =======  =========  ======  =====================
MetaData-listeners = ListnerSet{}}
TableDataset-dataset =
   Time    Energy    Distance
  (sec)      (eV)         (m)
-------  --------  ----------
      0     100          -500
      1     102.5         265
      2     105          1030
      3     107.5        1795
      4     110          2560
      5     112.5        3325
      6     115          4090
      7     117.5        4855




Metadata and Parameter - Parameter
----------------------------------



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
NumericParameter(description="UNKNOWN", type="integer", default=None, value=9000, valid=[[0, 'OK1'], [1, 'OK2'], [[100, 9900], 'Go!']], unit=None, typecode=None, _STID="NumericParameter")

>>> # The current value is valid
... v.isValid()
True

>>> # check if other values are valid according to specification of this parameter
... v.validate(600)  # valid
(600, 'Go!')

>>> v.validate(20)  # invalid
(Invalid, 'Invalid')

Metadata and Parameter - Metadata
---------------------------------

A :class:`Metadata` instance is mainly a dict-like container for named parameters.


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
NumericParameter(description="How heavey is the robot.", type="float", default=None, value=60.0, valid=None, unit="kg", typecode=None, _STID="NumericParameter")

>>> # add more parameter. Try a string type.
... v.set(name='job', newParameter=StringParameter('pilot'))
... # get the value of the parameter
... v.get('job').value   # == 'pilot'
'pilot'

>>> # access parameters in metadata
... # a more readable way to set/get a parameter than "v.set(a1,a2)", "v.get(a1)"
... v['job'] = StringParameter('waitress')
... v['job']   # == waitress
StringParameter(description="UNKNOWN", default="", value="waitress", valid=None, typecode="B", _STID="StringParameter")

>>> # same result as...
... v.get('job')
StringParameter(description="UNKNOWN", default="", value="waitress", valid=None, typecode="B", _STID="StringParameter")

>>> # Date type parameter use International Atomic Time (TAI) to keep time,
... # in 1-microsecond precission
... v['birthday'] = Parameter(description='was born on',
...                           value=FineTime('1990-09-09T12:34:56.789098 UTC'))
... # FDI use International Atomic Time (TAI) internally to record time.
... # The format is the integer number of microseconds since 1958-01-01 00:00:00 UTC.
... v['birthday'].value.tai
Time zone stripped for 1990-09-09T12:34:56.789098 UTC according to format.
1031574921789098

>>> # names of all parameters
... [n for n in v]   # == ['weight', 'job', 'birthday']
['weight', 'job', 'birthday']

>>> # remove parameter from metadata.   # function inherited from Composite class.
... v.remove(a1)
... v.size()  # == 2
2

>>> # The value of the next parameter is valid from 0 to 31 and can be 9
... valid_rule = {(0, 31): 'valid', 99: ''}
... v['a'] = NumericParameter(
...     3.4, 'rule name, if is "valid", "", or "default", is ommited in value string.', 'float', 2., valid=valid_rule)
... v['a'].isValid()    # True
True

>>> then = datetime(
...     2019, 2, 19, 1, 2, 3, 456789, tzinfo=timezone.utc)
... # The value of the next parameter is valid from TAI=0 to 9876543210123456
... valid_rule = {(0, 9876543210123456): 'alive'}
... v['b'] = DateParameter(FineTime(then), 'date param', default=99,
...                        valid=valid_rule)
... # display format set to 'year' (%Y)
... v['b'].format = '%Y-%M'
... # The value of the next parameter has an empty rule set and is always valid.
... v['c'] = StringParameter(
...     'Right', 'str parameter. but only "" is allowed.', valid={'': 'empty'}, default='cliche', typecode='B')

>>> # The value of the next parameter is for a detector status.
... # The information is packed in a byte, and if extractab;e with suitable binary masks:
... # Bit7~Bit6 port status [01: port 1; 10: port 2; 11: port closed];
... # Bit5 processing using the main processir or a stand-by one [0:  stand by; 1: main];
... # Bit4 PPS status [0: error; 1: normal];
... # Bit3~Bit0 reserved.
... valid_rule = {
...     (0b11000000, 0b01): 'port_1',
...     (0b11000000, 0b10): 'port_2',
...     (0b11000000, 0b11): 'port closed',
...     (0b00100000, 0b0): 'stand_by',
...     (0b00100000, 0b1): 'main',
...     (0b00010000, 0b0): 'error',
...     (0b00010000, 0b1): 'normal',
...     (0b00001111, 0b0): 'reserved'
... }
... v['d'] = NumericParameter(
...     0b01010110, 'valid rules described with binary masks', valid=valid_rule)
... # this returns the tested value, the rule name, the heiggt and width of every mask.
... v['d'].validate(0b01010110)
[(1, 'port_1', 8, 2),
 (0, 'stand_by', 6, 1),
 (1, 'normal', 5, 1),
 (Invalid, 'Invalid')]

>>> # string representation. This is the same as v.toString(level=0), most detailed.
... print(v.toString())

========  ====================  ======  ========  ====================  =================  ======  =====================
name      value                 unit    type      valid                 default            code    description
========  ====================  ======  ========  ====================  =================  ======  =====================
job       waitress                      string    None                                     B       UNKNOWN
birthday  1990-09-09T12:34:56.          finetime  None                  None                       was born on
          789098
          1031574921789098
a         3.4                   None    float     (0, 31): valid        2.0                None    rule name, if is "val
                                                  99:                                              id", "", or "default"
                                                                                                   , is ommited in value
                                                                                                    string.
b         alive (2019-02-19T01          finetime  (0, 9876543210123456  1958-01-01T00:00:  Q       date param
          :02:03.456789                           ): alive              00.000099
          1929229360456789)                                             99
c         Invalid (Right)               string    '': empty             cliche             B       str parameter. but on
                                                                                                   ly "" is allowed.
d         port_1 (0b01)         None    integer   11000000 0b01: port_  None               None    valid rules described
          stand_by (0b0)                          1                                                 with binary masks
          normal (0b1)                            11000000 0b10: port_
          Invalid                                 2
                                                  11000000 0b11: port
                                                  closed
                                                  00100000 0b0: stand_
                                                  by
                                                  00100000 0b1: main
                                                  00010000 0b0: error
                                                  00010000 0b1: normal
                                                  00001111 0b0000: res
                                                  erved
========  ====================  ======  ========  ====================  =================  ======  =====================
MetaData-listeners = ListnerSet{}

>>> # simplifed string representation, toString(level=1)
... v
job=waitress, birthday=1031574921789098, a=3.4, b=alive (1929229360456789), c=Invalid (Right), d=port_1 (0b01), stand_by (0b0), normal (0b1), Invalid.

>>> # simplest string representation, toString(level=2).
... print(v.toString(level=2))
job=waitress, birthday=FineTime(1990-09-09T12:34:56.789098), a=3.4, b=alive (FineTime(2019-02-19T01:02:03.456789)), c=Invalid (Right), d=port_1 (0b01), stand_by (0b0), normal (0b1), Invalid.


Product with metadata and datasets
----------------------------------



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
... # put the dataset into the product
... x["RawImage"] = image
... # take the data out of the product
... x["RawImage"].data  # == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
[[1, 2, 3], [4, 5, 6], [7, 8, 9]]

>>> # Another syntax to put dataset into a product: set(name, dataset)
... # Different but same function as above.
... # Here no unit or description is given when making ArrayDataset
... x.set('QualityImage', ArrayDataset(
...     [[0.1, 0.5, 0.7], [4e3, 6e7, 8], [-2, 0, 3.1]]))
... x["QualityImage"].unit  # is None

>>> # add another tabledataset
... s1 = [('col1', [1, 4.4, 5.4E3], 'eV'),
...       ('col2', [0, 43.2, 2E3], 'cnt')]
... x["Spectrum"] = TableDataset(data=s1)
... # See the numer and types of existing datasets in the product
... [type(d) for d in x.values()]
[fdi.dataset.arraydataset.ArrayDataset,
 fdi.dataset.arraydataset.ArrayDataset,
 fdi.dataset.tabledataset.TableDataset]

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

>>> # so was the property
... x.creator   # == a1
'or else'

>>> # load some metadata
... m = x.meta
... m['ddetector'] = v['d']

>>> print(x.toString())

::

   === Product () ===
   meta= {
   ============  ====================  ======  ========  ====================  =================  ======  =====================
   name          value                 unit    type      valid                 default            code    description
   ============  ====================  ======  ========  ====================  =================  ======  =====================
   description   product example with          string    None                  UNKNOWN            B       Description of this p
                  several datasets                                                                        roduct
   type          Product                       string    None                  Product            B       Product Type identifi
                                                                                                          cation. Name of class
                                                                                                           or CARD.
   level         ALL                           string    None                  ALL                B       Product level.
   creator       or else                       string    None                  None                       UNKNOWN
   creationDate  1958-01-01T00:00:00.          finetime  None                  1958-01-01T00:00:  Q       Creation date of this
                 000000                                                        00.000000                   product
                 0                                                             0
   rootCause     UNKNOWN                       string    None                  UNKNOWN            B       Reason of this run of
                                                                                                           pipeline.
   version       0.8                           string    None                  0.8                B       Version of product
   FORMATV       1.6.0.10                      string    None                  1.6.0.10           B       Version of product sc
                                                                                                          hema and revision
   startDate     1958-01-01T00:00:00.          finetime  None                  1958-01-01T00:00:  Q       Nominal start time  o
                 000000                                                        00.000000                  f this product.
                 0                                                             0
   endDate       1958-01-01T00:00:00.          finetime  None                  1958-01-01T00:00:  Q       Nominal end time  of
                 000000                                                        00.000000                  this product.
                 0                                                             0
   instrument    Crystal-Ball                  string    None                  UNKNOWN            B       Instrument that gener
                                                                                                          ated data of this pro
                                                                                                          duct
   modelName     Mk II                         string    None                  UNKNOWN            B       Model name of the ins
                                                                                                          trument of this produ
                                                                                                          ct
   mission       _AGS                          string    None                  _AGS               B       Name of the mission.
   ddetector     port_1 (0b01)         None    integer   11000000 0b01: port_  None               None    valid rules described
                 stand_by (0b0)                          1                                                 with binary masks
                 normal (0b1)                            11000000 0b10: port_
                 Invalid                                 2
                                                         11000000 0b11: port
                                                         closed
                                                         00100000 0b0: stand_
                                                         by
                                                         00100000 0b1: main
                                                         00010000 0b0: error
                                                         00010000 0b1: normal
                                                         00001111 0b0000: res
                                                         erved
   ============  ====================  ======  ========  ====================  =================  ======  =====================
   MetaData-listeners = ListnerSet{}},
   history= {},
   listeners= {ListnerSet{}}
   
   === History () ===
   PARAM_HISTORY= {''},
   TASK_HISTORY= {''},
   meta= {(No Parameter.) MetaData-listeners = ListnerSet{}}
   
   History-datasets =
   <ODict >
   
   Product-datasets =
   <ODict "RawImage":
   === ArrayDataset () ===
   meta= {
   ===========  =======  ======  ======  =======  =========  ======  =====================
   name         value    unit    type    valid    default    code    description
   ===========  =======  ======  ======  =======  =========  ======  =====================
   description  image1           string  None     UNKNOWN    B       Description of this d
                                                                     ataset
   unit         ev               string  None     None       B       Unit of every element
                                                                     .
   shape        ()               tuple   None     ()                 Number of elements in
                                                                      each dimension. Quic
                                                                     k changers to the rig
                                                                     ht.
   typecode     UNKNOWN          string  None     UNKNOWN    B       Python internal stora
                                                                     ge code.
   version      0.1              string  None     0.1        B       Version of dataset
   FORMATV      1.6.0.1          string  None     1.6.0.1    B       Version of dataset sc
                                                                     hema and revision
   ===========  =======  ======  ======  =======  =========  ======  =====================
   MetaData-listeners = ListnerSet{}}
   ArrayDataset-dataset =
   1  2  3
   4  5  6
   7  8  9
   
   
   "QualityImage":
   === ArrayDataset () ===
   meta= {
   ===========  =======  ======  ======  =======  =========  ======  =====================
   name         value    unit    type    valid    default    code    description
   ===========  =======  ======  ======  =======  =========  ======  =====================
   description  UNKNOWN          string  None     UNKNOWN    B       Description of this d
                                                                     ataset
   unit         None             string  None     None       B       Unit of every element
                                                                     .
   shape        ()               tuple   None     ()                 Number of elements in
                                                                      each dimension. Quic
                                                                     k changers to the rig
                                                                     ht.
   typecode     UNKNOWN          string  None     UNKNOWN    B       Python internal stora
                                                                     ge code.
   version      0.1              string  None     0.1        B       Version of dataset
   FORMATV      1.6.0.1          string  None     1.6.0.1    B       Version of dataset sc
                                                                     hema and revision
   ===========  =======  ======  ======  =======  =========  ======  =====================
   MetaData-listeners = ListnerSet{}}
   ArrayDataset-dataset =
      0.1  0.5    0.7
   4000    6e+07  8
     -2    0      3.1
   
   
   "Spectrum":
   === TableDataset () ===
   meta= {
   ===========  =======  ======  ======  =======  =========  ======  =====================
   name         value    unit    type    valid    default    code    description
   ===========  =======  ======  ======  =======  =========  ======  =====================
   description  UNKNOWN          string  None     UNKNOWN    B       Description of this d
                                                                     ataset
   version      0.1              string  None     0.1        B       Version of dataset
   FORMATV      1.6.0.1          string  None     1.6.0.1    B       Version of dataset sc
                                                                     hema and revision
   ===========  =======  ======  ======  =======  =========  ======  =====================
   MetaData-listeners = ListnerSet{}}
   TableDataset-dataset =
     col1     col2
     (eV)    (cnt)
   ------  -------
      1        0
      4.4     43.2
   5400     2000
   


>>> # Create a product and a productStorage with a pool registered
... # First disable debugging messages
... logger = logging.getLogger('')
... logger.setLevel(logging.WARNING)
... # a pool (LocalPool) for demonstration will be create here
... demopoolname = 'demopool_' + getpass.getuser()
... demopoolpath = '/tmp/' + demopoolname
... demopoolurl = 'file://' + demopoolpath
... # clean possible data left from previous runs
... os.system('rm -rf ' + demopoolpath)
... if PoolManager.isLoaded(DEFAULT_MEM_POOL):
...     PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
... PoolManager.getPool(demopoolname, demopoolurl).removeAll()

>>> # create a prooduct and save it to a pool
... x = Product(description='save me in store')
... # add a tabledataset
... s1 = [('energy', [1, 4.4, 5.6], 'eV'), ('freq', [0, 43.2, 2E3], 'Hz')]
... x["Spectrum"] = TableDataset(data=s1)
... # create a product store
... pstore = ProductStorage(poolurl=demopoolurl)
... # see what is in it.
... pstore
ProductStorage( pool= {'demopool_mh': <LocalPool poolname=demopool_mh, poolurl=file:///tmp/demopool_mh, _classes=<ODict>, _urns=<ODict>, _tags=<ODict>>} )

>>> # save the product and get a reference back.
... prodref = pstore.save(x)
... # This gives detailed information of the product being referenced
... print(prodref)
ProductRef {urn:demopool_mh:fdi.dataset.product.Product:0
# Parents=[]
# meta=
============  ====================  ======  ========  =======  =================  ======  =====================
name          value                 unit    type      valid    default            code    description
============  ====================  ======  ========  =======  =================  ======  =====================
description   save me in store              string    None     UNKNOWN            B       Description of this p
                                                                                          roduct
type          Product                       string    None     Product            B       Product Type identifi
                                                                                          cation. Name of class
                                                                                           or CARD.
level         ALL                           string    None     ALL                B       Product level.
creator       UNKNOWN                       string    None     UNKNOWN            B       Generator of this pro
                                                                                          duct.
creationDate  1958-01-01T00:00:00.          finetime  None     1958-01-01T00:00:  Q       Creation date of this
              000000                                           00.000000                   product
              0                                                0
rootCause     UNKNOWN                       string    None     UNKNOWN            B       Reason of this run of
                                                                                           pipeline.
version       0.8                           string    None     0.8                B       Version of product
FORMATV       1.6.0.10                      string    None     1.6.0.10           B       Version of product sc
                                                                                          hema and revision
startDate     1958-01-01T00:00:00.          finetime  None     1958-01-01T00:00:  Q       Nominal start time  o
              000000                                           00.000000                  f this product.
              0                                                0
endDate       1958-01-01T00:00:00.          finetime  None     1958-01-01T00:00:  Q       Nominal end time  of
              000000                                           00.000000                  this product.
              0                                                0
instrument    UNKNOWN                       string    None     UNKNOWN            B       Instrument that gener
                                                                                          ated data of this pro
                                                                                          duct
modelName     UNKNOWN                       string    None     UNKNOWN            B       Model name of the ins
                                                                                          trument of this produ
                                                                                          ct
mission       _AGS                          string    None     _AGS               B       Name of the mission.
============  ====================  ======  ========  =======  =================  ======  =====================
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

>>> print("""
... Context -- a Product with References
... ------------------------------------
... 
... This section shows essencial steps how product references can be stored in a context.
... """)

Context -- a Product with References
------------------------------------

This section shows essencial steps how product references can be stored in a context.


>>> p1 = Product(description='p1')
... p2 = Product(description='p2')
... # create an empty mapcontext that can carry references with name labels
... map1 = MapContext(description='product with refs 1')
... # A ProductRef created with the syntax of a lone product argument will use a MemPool
... pref1 = ProductRef(p1)
... pref1
ProductRef(urnobj=Urn(urn="urn:defaultmem:fdi.dataset.product.Product:0", _STID="Urn"), _STID="ProductRef")

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


Query a Storage to get saved Products
-------------------------------------

A :class:`ProductStorage` with pools attached can be queried with tags, properties stored in metadata, or even data in the stored products, using Python syntax.


>>> # clean possible data left from previous runs
... poolname = 'fdi_pool_' + getpass.getuser()
... poolpath = '/tmp/' + poolname
... newpoolname = 'fdi_newpool_' + getpass.getuser()
... newpoolpath = '/tmp/' + newpoolname
... os.system('rm -rf ' + poolpath)
... os.system('rm -rf ' + newpoolpath)
... poolurl = 'file://' + poolpath
... newpoolurl = 'file://' + newpoolpath
... if PoolManager.isLoaded(DEFAULT_MEM_POOL):
...     PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
... PoolManager.getPool(poolname, poolurl).removeAll()
... PoolManager.getPool(newpoolname, newpoolurl).removeAll()
... # make a productStorage
... pstore = ProductStorage(poolurl=poolurl)
... # make another
... pstore2 = ProductStorage(poolurl=newpoolurl)

>>> # add some products to both storages. The product properties are different.
... n = 7
... for i in range(n):
...     # three counters for properties to be queried.
...     a0, a1, a2 = 'desc %d' % i, 'fatman %d' % (i*4), 5000+i
...     if i < 3:
...         # Product type
...         x = Product(description=a0, creator=a1)
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
urn:fdi_pool_mh:fdi.dataset.product.Product:0
urn:fdi_pool_mh:fdi.dataset.product.Product:1
urn:fdi_pool_mh:fdi.dataset.product.Product:2
urn:fdi_pool_mh:fdi.pal.context.Context:0
urn:fdi_newpool_mh:fdi.pal.context.Context:0
urn:fdi_newpool_mh:fdi.pal.context.MapContext:0
urn:fdi_newpool_mh:fdi.pal.context.MapContext:1

>>> # register the new pool above to the  1st productStorage
... pstore.register(newpoolname)
... len(pstore.getPools())   # == 2
2

>>> # make a query on product metadata, which is the variable 'm'
... # in the query expression, i.e. ``m = product.meta; ...``
... # But '5000 < m["extra"]' does not work. see tests/test.py.
... q = MetaQuery(Product, 'm["extra"] > 5000 and m["extra"] <= 5005')
... # search all pools registered on pstore
... res = pstore.select(q)
... # we expect [#2, #3] Contex is not a subclass of Product, which is being searched
... len(res)   # == 2
2

>>> # see
... [r.product.description for r in res]
['desc 1', 'desc 2']

>>> def t(m):
...     # query is a function
...     import re
...     # 'creator' matches the regex pattern: 'n' + ? + '1'
...     return re.match('.*n.1.*', m['creator'].value)

>>> q = MetaQuery(BaseProduct, t)
... res = pstore.select(q)
... # expecting [3,4]
... [r.product.creator for r in res]
['fatman 12', 'fatman 16']

>>> # same as above but query is on the product. this is slow.
... q = AbstractQuery(BaseProduct, 'p', '"n 1" in p.creator')
... res = pstore.select(q)
... # [3,4]
... [r.product.creator for r in res]
['fatman 12', 'fatman 16']

>>>

END of examples

See the installation and testing sections of the pns page.


.. tip::
   
   The demo above was made by running ``fdi/resources/example.py`` with command ``elpy-shell-send-group-and-step [c-c c-y c-g]`` in ``emacs``. The command is further simplified to control-<tab> with the following in ~/.init.el:
   
   .. code-block::

      (add-hook 'elpy-mode-hook (lambda () (local-set-key \
          [C-tab] (quote elpy-shell-send-group-and-step))))
