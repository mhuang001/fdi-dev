"""
The following demostrates important dataset and pal functionalities. It was made by running fdi/resources/example.py with command ``elpy-shell-send-group-and-step [c-c c-y c-g]`` in ``emacs``. The command is further simplified to control-<tab> with the following in ~/.init.el:


.. code-bloc:: lisp
   (add-hook 'elpy-mode-hook
	  (lambda ()
	    (local-set-key [C-tab] (quote elpy-shell-send-group-and-step))))


You can copy the code from code blocks by clicking the ``copy`` icon on the top-right, with he proompts and results removed.
"""

# Import these packages needed in the tutorial
from fdi.dataset.product import Product, BaseProduct
from fdi.dataset.metadata import Parameter, MetaData
from fdi.dataset.numericparameter import NumericParameter
from fdi.dataset.stringparameter import StringParameter
from fdi.dataset.dateparameter import DateParameter
from fdi.dataset.finetime import FineTime, FineTime1
from fdi.dataset.arraydataset import ArrayDataset, Column
from fdi.dataset.tabledataset import TableDataset
from fdi.dataset.classes import Classes
from fdi.pal.context import Context, MapContext
from fdi.pal.productref import ProductRef
from fdi.pal.query import AbstractQuery, MetaQuery
from fdi.pal.poolmanager import PoolManager, DEFAULT_MEM_POOL
from fdi.pal.productstorage import ProductStorage
import getpass
import os
from datetime import datetime, timezone
import logging


# initialize the white-listed class dictionary
cmap = Classes.updateMapping()

print("""
dataset
=======

First we show how to make and use components of the data model.

This section shows how to create data containers -- datasets, metadata, and Products, how to put data into the containers, read data out, modify data, remove data, inspect data.

ArrayDataset -- sequence of data in the same unit and format
------------------------------------------------------------
""")


# Creation with an array of data quickly
a1 = [1, 4.4, 5.4E3, -22, 0xa2]
v = ArrayDataset(a1)
# Show it. This is the same as print(v) in a non-interactive environment.
# "Default Meta." means the metadata settings are all default values..
v

# Create an ArrayDataset with some built-in properties set.
v = ArrayDataset(data=a1, unit='ev', description='5 elements', typecode='f')
#
# add some metadats (see more about meta data below)
v.meta['greeting'] = StringParameter('Hi there.')
v.meta['year'] = NumericParameter(2020)
v

# data access: read the 2nd array element
v[2]       # 5400

# built-in properties
v.unit

# change it
v.unit = 'm'
v.unit

# iteration
for m in v:
    print(m + 1)

# a filter example
[m**3 for m in v if m > 0 and m < 40]

# slice the ArrayDataset and only get part of its data
v[2:-1]

# set data to be a 2D array
v.data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
# slicing happens on the slowest dimension.
v[0:2]

# Run this to see a demo of the ``toString()`` function:
# make a 4-D array: a list of 2 lists of 3 lists of 4 lists of 5 elements.
s = [[[[i + j + k + l for i in range(5)] for j in range(4)]
      for k in range(3)] for l in range(2)]
v.data = s
print(v.toString())

print('''
TableDataset -- a set of named Columns and their metadata
---------------------------------------------------------

TableDataset is mainly a dictionary containing named :class:`Column`\s and their metadata. Columns are basically ArrayDatasets under a different name.
''')

# Create an empty TableDataset then add columns one by one
v = TableDataset()
v['col1'] = Column(data=[1, 4.4, 5.4E3], unit='eV')
v['col2'] = Column(data=[0, 43.2, 2E3], unit='cnt')
v

# Do it with another syntax, with a list of tuples and no Column()
a1 = [('col1', [1, 4.4, 5.4E3], 'eV'),
      ('col2', [0, 43.2, 2E3], 'cnt')]
v1 = TableDataset(data=a1)
v == v1

# Make a quick tabledataset -- data are list of lists without names or units
a5 = [[1, 4.4, 5.4E3], [0, 43.2, 2E3], [True, True, False], ['A', 'BB', 'CCC']]
v5 = TableDataset(data=a5)
print(v5.toString())

# access
# get names of all columns (automatically given here)
v5.getColumnNames()

# get column by name
my_column = v5['column1']       # [1, 4.4, 5.4E3]
my_column.data

# by index
v5[0].data       # [1, 4.4, 5.4E3]

# get a list of all columns' data.
# Note the slice "v5[:]" and syntax ``in``
[c.data for c in v5[:]]   # == a5

#  indexOf by name
v5.indexOf('column1')  # == u.indexOf(my_column)

#  indexOf by column object
v5.indexOf(my_column)     # 0

# set cell value
v5['column2'][1] = 123
v5['column2'][1]    # 123

# row access bu row index -- multiple and in custom order
v5.getRow([2, 1])  # [(5400.0, 2000.0, False, 'CCC'), (4.4, 123, True, 'BB')]

# or with a slice
v5.getRow(slice(0, -1))

# unit access
v1['col1'].unit  # == 'eV'

# add, set, and replace columns and rows
# column set / get
u = TableDataset()
c1 = Column([1, 4], 'sec')
# add
u.addColumn('time', c1)
u.columnCount        # 1

# for non-existing names set is addColum.
u['money'] = Column([2, 3], 'eu')
u['money'][0]    # 2
# column increases
u.columnCount        # 2

# addRow
u.rowCount    # 2

u.addRow({'money': 4.4, 'time': 3.3})
u.rowCount    # 3

# run this to see ``toString()``
ELECTRON_VOLTS = 'eV'
SECONDS = 'sec'
t = [x * 1.0 for x in range(8)]
e = [2.5 * x + 100 for x in t]
d = [765 * x - 500 for x in t]
# creating a table dataset to hold the quantified data
x = TableDataset(description="Example table")
x["Time"] = Column(data=t, unit=SECONDS)
x["Energy"] = Column(data=e, unit=ELECTRON_VOLTS)
x["Distance"] = Column(data=d, unit='m')
# metadata is optional
x.meta['temp'] = NumericParameter(42.6, description='Ambient', unit='C')
print(x.toString())

print("""
Metadata and Parameter - Parameter
----------------------------------

""")

# Creation
# The standard way -- with keyword arguments
v = Parameter(value=9000, description='Average age', typ_='integer')
v.description   # 'Average age'

v.value   # == 9000

v.type   # == 'integer'

# test equals.
# FDI DeepEqual integerface class recursively compares all components.
v1 = Parameter(description='Average age', value=9000, typ_='integer')
v.equals(v1)

# more readable 'equals' syntax
v == v1

# make them not equal.
v1.value = -4
v.equals(v1)   # False

# math syntax
v != v1  # True

# NumericParameter with two valid values and a valid range.
v = NumericParameter(value=9000, valid={
                     0: 'OK1', 1: 'OK2', (100, 9900): 'Go!'})
# There are thee valid conditions
v

# The current value is valid
v.isValid()


# check if other values are valid according to specification of this parameter
v.validate(600)  # valid

v.validate(20)  # invalid


print("""
Metadata and Parameter - Metadata
---------------------------------

A :class:`Metadata` instance is mainly a dict-like container for named parameters.
""")

# Creation. Start with numeric parameter.
a1 = 'weight'
a2 = NumericParameter(description='How heavey is the robot.',
                      value=60, unit='kg', typ_='float')
# make an empty MetaData instance.
v = MetaData()
# place the parameter with a name
v.set(a1, a2)
# get the parameter with the name.
v.get(a1)   # == a2

# add more parameter. Try a string type.
v.set(name='job', newParameter=StringParameter('pilot'))
# get the value of the parameter
v.get('job').value   # == 'pilot'

# access parameters in metadata
# a more readable way to set/get a parameter than "v.set(a1,a2)", "v.get(a1)"
v['job'] = StringParameter('waitress')
v['job']   # == waitress

# same result as...
v.get('job')

# Date type parameter use International Atomic Time (TAI) to keep time,
# in 1-microsecond precission
v['birthday'] = Parameter(description='was born on',
                          value=FineTime('1990-09-09T12:34:56.789098 UTC'))
# FDI use International Atomic Time (TAI) internally to record time.
# The format is the integer number of microseconds since 1958-01-01 00:00:00 UTC.
v['birthday'].value.tai


# names of all parameters
[n for n in v]   # == ['weight', 'job', 'birthday']

# remove parameter from metadata.   # function inherited from Composite class.
v.remove(a1)
v.size()  # == 2

# The value of the next parameter is valid from 0 to 31 and can be 9
valid_rule = {(0, 31): 'valid', 99: ''}
v['a'] = NumericParameter(
    3.4, 'rule name, if is "valid", "", or "default", is ommited in value string.', 'float', 2., valid=valid_rule)
v['a'].isValid()    # True

then = datetime(
    2019, 2, 19, 1, 2, 3, 456789, tzinfo=timezone.utc)
# The value of the next parameter is valid from TAI=0 to 9876543210123456
valid_rule = {(0, 9876543210123456): 'alive'}
v['b'] = DateParameter(FineTime(then), 'date param', default=99,
                       valid=valid_rule)
# display format set to 'year' (%Y)
v['b'].format = '%Y-%M'
# The value of the next parameter has an empty rule set and is always valid.
v['c'] = StringParameter(
    'Right', 'str parameter. but only "" is allowed.', valid={'': 'empty'}, default='cliche', typecode='B')

# The value of the next parameter is for a detector status.
# The information is packed in a byte, and if extractab;e with suitable binary masks:
# Bit7~Bit6 port status [01: port 1; 10: port 2; 11: port closed];
# Bit5 processing using the main processir or a stand-by one [0:  stand by; 1: main];
# Bit4 PPS status [0: error; 1: normal];
# Bit3~Bit0 reserved.
valid_rule = {
    (0b11000000, 0b01): 'port_1',
    (0b11000000, 0b10): 'port_2',
    (0b11000000, 0b11): 'port closed',
    (0b00100000, 0b0): 'stand_by',
    (0b00100000, 0b1): 'main',
    (0b00010000, 0b0): 'error',
    (0b00010000, 0b1): 'normal',
    (0b00001111, 0b0): 'reserved'
}
v['d'] = NumericParameter(
    0b01010110, 'valid rules described with binary masks', valid=valid_rule)
# this returns the tested value, the rule name, the heiggt and width of every mask.
v['d'].validate(0b01010110)

# string representation. This is the same as v.toString(level=0), most detailed.
print(v.toString())

# simplifed string representation, toString(level=1)
v

# simplest string representation, toString(level=2).
print(v.toString(level=2))

print("""
Product with metadata and datasets
----------------------------------

""")

# Creation:
x = Product(description="product example with several datasets",
            instrument="Crystal-Ball", modelName="Mk II")
x.meta['description'].value  # == "product example with several datasets"

# The 'instrument' and 'modelName' built-in properties show the
# origin of FDI -- processing data from scientific instruments.
x.instrument  # == "Crystal-Ball"

# ways to add datasets
i0 = 6
i1 = [[1, 2, 3], [4, 5, i0], [7, 8, 9]]
i2 = 'ev'                 # unit
i3 = 'image1'     # description
image = ArrayDataset(data=i1, unit=i2, description=i3)
# put the dataset into the product
x["RawImage"] = image
# take the data out of the product
x["RawImage"].data  # == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

# Another syntax to put dataset into a product: set(name, dataset)
# Different but same function as above.
# Here no unit or description is given when making ArrayDataset
x.set('QualityImage', ArrayDataset(
    [[0.1, 0.5, 0.7], [4e3, 6e7, 8], [-2, 0, 3.1]]))
x["QualityImage"].unit  # is None

# add another tabledataset
s1 = [('col1', [1, 4.4, 5.4E3], 'eV'),
      ('col2', [0, 43.2, 2E3], 'cnt')]
x["Spectrum"] = TableDataset(data=s1)
# See the numer and types of existing datasets in the product
[type(d) for d in x.values()]

# mandatory properties are also in metadata
# test mandatory BaseProduct properties that are also metadata
a0 = "Me, myself and I"
x.creator = a0
x.creator   # == a0

# metada by the same name is also set
x.meta["creator"].value   # == a0

# change the metadata
a1 = "or else"
x.meta["creator"] = Parameter(a1)
# metada changed
x.meta["creator"].value   # == a1

# so was the property
x.creator   # == a1

# load some metadata
m = x.meta
m['ddetector'] = v['d']
# Demo ``toString()`` function.

print(x.toString())


print('''
pal - Product Access Layer
==========================

Products need to persist (be stored somewhere) in order to have a reference that can be used to re-create the product after its creation process ends.

Product Pool and Product References
-----------------------------------

This section shows how to store a product in a "pool" and get a reference back.
''')


# Create a product and a productStorage with a pool registered
# First disable debugging messages
logger = logging.getLogger('')
logger.setLevel(logging.WARNING)
# a pool (LocalPool) for demonstration will be create here
demopoolname = 'demopool_' + getpass.getuser()
demopoolpath = '/tmp/' + demopoolname
demopoolurl = 'file://' + demopoolpath
# clean possible data left from previous runs
os.system('rm -rf ' + demopoolpath)
if PoolManager.isLoaded(DEFAULT_MEM_POOL):
    PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
PoolManager.getPool(demopoolname, demopoolurl).removeAll()

# create a prooduct and save it to a pool
x = Product(description='save me in store')
# add a tabledataset
s1 = [('energy', [1, 4.4, 5.6], 'eV'), ('freq', [0, 43.2, 2E3], 'Hz')]
x["Spectrum"] = TableDataset(data=s1)
# create a product store
pstore = ProductStorage(poolurl=demopoolurl)
# see what is in it.
pstore

# save the product and get a reference back.
prodref = pstore.save(x)
# This gives detailed information of the product being referenced
print(prodref)

# get the URN string
urn = prodref.urn
print(urn)    # urn:demopool_mh:fdi.dataset.product.Product:0

# re-create a product only using the urn
newp = ProductRef(urn).product
# the new and the old one are equal
print(newp == x)   # == True


print("""
Context -- a Product with References
------------------------------------

This section shows essencial steps how product references can be stored in a context.
""")

p1 = Product(description='p1')
p2 = Product(description='p2')
# create an empty mapcontext that can carry references with name labels
map1 = MapContext(description='product with refs 1')
# A ProductRef created with the syntax of a lone product argument will use a MemPool
pref1 = ProductRef(p1)
pref1

# A productStorage with a LocalPool -- a pool on the disk.
pref2 = pstore.save(p2)
pref2.urn

# how many prodrefs do we have?
map1['refs'].size()   # == 0

# how many 'parents' do these prodrefs have before saved?
len(pref1.parents)   # == 0

len(pref2.parents)   # == 0

# add a ref to the context. Every productref has a name in a MapContext
map1['refs']['spam'] = pref1
# add the second one
map1['refs']['egg'] = pref2
# how many prodrefs do we have?
map1['refs'].size()   # == 2

# parent list of the productref object now has an entry
len(pref2.parents)   # == 1

pref2.parents[0] == map1

pref1.parents[0] == map1

# remove a ref
del map1['refs']['spam']
map1.refs.size()   # == 1

# how many prodrefs do we have?
len(pref1.parents)   # == 0

# add ref2 to another map
map2 = MapContext(description='product with refs 2')
map2.refs['also2'] = pref2
map2['refs'].size()   # == 1

# two parents
len(pref2.parents)   # == 2

pref2.parents[1] == map2

print("""
Query a Storage to get saved Products
-------------------------------------

A :class:`ProductStorage` with pools attached can be queried with tags, properties stored in metadata, or even data in the stored products, using Python syntax.
""")

# clean possible data left from previous runs
poolname = 'fdi_pool_' + getpass.getuser()
poolpath = '/tmp/' + poolname
newpoolname = 'fdi_newpool_' + getpass.getuser()
newpoolpath = '/tmp/' + newpoolname
os.system('rm -rf ' + poolpath)
os.system('rm -rf ' + newpoolpath)
poolurl = 'file://' + poolpath
newpoolurl = 'file://' + newpoolpath
if PoolManager.isLoaded(DEFAULT_MEM_POOL):
    PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
PoolManager.getPool(poolname, poolurl).removeAll()
PoolManager.getPool(newpoolname, newpoolurl).removeAll()
# make a productStorage
pstore = ProductStorage(poolurl=poolurl)
# make another
pstore2 = ProductStorage(poolurl=newpoolurl)

# add some products to both storages. The product properties are different.
n = 7
for i in range(n):
    # three counters for properties to be queried.
    a0, a1, a2 = 'desc %d' % i, 'fatman %d' % (i*4), 5000+i
    if i < 3:
        # Product type
        x = Product(description=a0, creator=a1)
        x.meta['extra'] = Parameter(value=a2)
    elif i < 5:
        # a different type
        x = Context(description=a0, creator=a1)
        x.meta['extra'] = Parameter(value=a2)
    else:
        # yet another type
        x = MapContext(description=a0, creator=a1)
        x.meta['extra'] = Parameter(value=a2)
        x.meta['time'] = Parameter(value=FineTime1(a2))
    if i < 4:
        # some are stored in one pool
        r = pstore.save(x)
    else:
        # some the other
        r = pstore2.save(x)
    print(r.urn)
# Two pools, 7 products in 3 types
# [P P P C] [C M M]
#  0 1 2 3   4 5 6

# register the new pool above to the  1st productStorage
pstore.register(newpoolname)
len(pstore.getPools())   # == 2

# make a query on product metadata, which is the variable 'm'
# in the query expression, i.e. ``m = product.meta; ...``
# But '5000 < m["extra"]' does not work. see tests/test.py.
q = MetaQuery(Product, 'm["extra"] > 5000 and m["extra"] <= 5005')
# search all pools registered on pstore
res = pstore.select(q)
# we expect [#2, #3] Contex is not a subclass of Product, which is being searched
len(res)   # == 2

# see
[r.product.description for r in res]

# another one


def t(m):
    # query is a function
    import re
    # 'creator' matches the regex pattern: 'n' + ? + '1'
    return re.match('.*n.1.*', m['creator'].value)


q = MetaQuery(BaseProduct, t)
res = pstore.select(q)
# expecting [3,4]
[r.product.creator for r in res]

# same as above but query is on the product. this is slow.
q = AbstractQuery(BaseProduct, 'p', '"n 1" in p.creator')
res = pstore.select(q)
# [3,4]
[r.product.creator for r in res]
