"""
The following demostrates important dataset and pal functionalities. It was made by running fdi/resources/example.py with command ``elpy-shell-send-group-and-step [c-c c-y c-g]`` in ``emacs``. The command is further simplified to control-<tab> with the following in ~/.init.el:


.. code-bloc:: lisp
   (add-hook 'elpy-mode-hook
	  (lambda ()
	    (local-set-key [C-tab] (quote elpy-shell-send-group-and-step))))


You can copy the code from code blocks by clicking the ``copy`` icon on the top-right, with he proompts and results removed.
"""

# import these first.

from fdi.dataset.product import Product
from fdi.dataset.metadata import Parameter, NumericParameter, MetaData, StringParameter, DateParameter
from fdi.dataset.finetime import FineTime, FineTime1
from fdi.dataset.dataset import ArrayDataset, TableDataset, Column
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
The data model.
""")

print("""
ArrayDataset
------------
""")


# Creation
a1 = [1, 4.4, 5.4E3, -22, 0xa2]      # a 1D array of data
# quick
v = ArrayDataset(a1)
v

# clear
v = ArrayDataset(data=a1, unit='ev', description='5 elements',
                 typ_='float', default=1.0, typecode='f')
v

# data access
v[2]

v.unit

# change attributes
v.unit = 'm'
v.unit

# iteration
for m in v:
    print(m)

# a filter example
[m**3 for m in v if m > 0 and m < 40]

# slice
v[1:3]

v[2:-1]

# a 2D array
v.data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
v[0:2]

# Run this to see a demo of the ``toString()`` function::
# make a 4-D array: a list of 2 lists of 3 lists of 4 lists of 5 elements.
s = [[[[i + j + k + l for i in range(5)] for j in range(4)]
      for k in range(3)] for l in range(2)]
x = ArrayDataset(data=s)
print(x.toString())

print('''
TableDataset
------------

TableDataset is mainly a name-Column pairs dictionary with metadata.
Columns are ArrayDatasets under a different name.
''')

# Creation
a1 = [dict(name='col1', unit='eV', column=[1, 4.4, 5.4E3]),
      dict(name='col2', unit='cnt', column=[0, 43.2, 2E3])
      ]
v = TableDataset(data=a1)
v

# one of many other ways to create a TableDataset
v3 = TableDataset(data=[('col1', [1, 4.4, 5.4E3], 'eV'),
                        ('col2', [0, 43.2, 2E3], 'cnt')])
v == v3


# quick tabledataset. data are list of lists without names or units
a5 = [[1, 4.4, 5.4E3], [0, 43.2, 2E3]]
v5 = TableDataset(data=a5)
print(v5.toString())

# access
# get names of all column
v5.getColumnNames()

# get a list of all columns' data
[c.data for c in v5.data.values()]   # == a5

# get column by name
my_column = v5['col1']
my_column

#  indexOf
v5.indexOf('col1')  # == u.indexOf(my_column)

v5.indexOf(my_column)

# set cell value
v5['col2'][1] = 123
v5['col2'][1]    # 123

# unit access
v3['col1'].unit  # == 'eV'

# add, set, and replace columns and rows
# column set / get
u = TableDataset()
c1 = Column([1, 4], 'sec')
u.addColumn('time', c1)
u.columnCount        # 1

# for non-existing names set is addColum.
u['money'] = Column([2, 3], 'eu')
u['money'][0]    # 2

u.columnCount        # 2

# addRow
u.rowCount    # 2

u.addRow({'money': 4.4, 'time': 3.3})
u.rowCount    # 3

# syntax ``in``
[c for c in u]  # list of column names ['time', 'money']


# run this to see ``toString()``
ELECTRON_VOLTS = 'eV'
SECONDS = 'sec'
t = [x * 1.0 for x in range(10)]
e = [2 * x + 100 for x in t]
# creating a table dataset to hold the quantified data
x = TableDataset(description="Example table")
x["Time"] = Column(data=t, unit=SECONDS)
x["Energy"] = Column(data=e, unit=ELECTRON_VOLTS)
print(x.toString())

print("""
Parameter
---------
""")

# Creation
# standard way -- with keyword arguments
v = Parameter(value=9000, description='Average age', typ_='integer')
v.description   # 'Average age

v.value   # == 9000

v.type   # == 'integer'

# test equals
v1 = Parameter(description='Average age', value=9000, typ_='integer')
v.equals(v1)

v == v1

v1.value = -4
v.equals(v1)   # False

v != v1  # True

# NumericParameter with two valid values and a valid range.
v = NumericParameter(value=9000, valid={
                     0: 'OK1', 1: 'OK2', (100, 9900): 'Go!'})

# There are thee valid conditions
v

# The current value is valid
v.isvalid()


# check if other values are valid according to specification of this parameter
v.validate(600)  # valid

v.validate(20)  # invalid


print("""
Metadata
--------
A container for named parameters.
""")

# Creation
a1 = 'weight'
a2 = NumericParameter(description='How heavey is the robot.',
                      value=20, unit='kg', typ_='integer')
v = MetaData()
# place the parameter with a name
v.set(a1, a2)
# get the parameter with the name
v.get(a1)   # == a2

# add more parameter
v.set(name='job', newParameter=StringParameter('teacher'))
# get the value of the parameter
v.get('job').value   # == 'teacher'

# access parameters in metadata
v = MetaData()
# a more readable way to set/get a parameter than "v.set(a1,a2)", "v.get(a1)"
v[a1] = a2
v[a1]   # == a2

# same result as...
v.get(a1)   # == a2

# Date type parameter use International Atomic Time (TAI) to keep time,
# in 1-microsecond precission
v['birthday'] = Parameter(description='was made on',
                          value=FineTime('2020-09-09T12:34:56.789098 UTC'))
v['birthday'].value.tai

# names of all parameters
[n for n in v]   # == ['weight', 'birthday']

# string presentation
print(v.toString())

# remove parameter
v.remove(a1)  # inherited from composite
print(v.size())  # == 1

# simplifed string presentation
print(v)

print("""
Product
-------
""")

# Creation:
x = Product(description="product example with several datasets",
            instrument="Crystal-Ball", modelName="Mk II")
x.meta['description'].value  # == "product example with several datasets"

x.instrument  # == "Crystal-Ball"

# ways to add datasets
i0 = 6
i1 = [[1, 2, 3], [4, 5, i0], [7, 8, 9]]
i2 = 'ev'                 # unit
i3 = 'image1'     # description
image = ArrayDataset(data=i1, unit=i2, description=i3)
x["RawImage"] = image
x["RawImage"].data  # == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

# no unit or description. different syntax but same function as above
x.set('QualityImage', ArrayDataset(
    [[0.1, 0.5, 0.7], [4e3, 6e7, 8], [-2, 0, 3.1]]))
x["QualityImage"].unit  # is None

# add a tabledataset
s1 = [('col1', [1, 4.4, 5.4E3], 'eV'),
      ('col2', [0, 43.2, 2E3], 'cnt')]
x["Spectrum"] = TableDataset(data=s1)

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

# so did the property
x.creator   # == a1

# load some metadata
m = x.meta
m['a'] = NumericParameter(
    3.4, 'num par', 'float', 2., {(0, 30): 'nok'})
then = datetime(
    2019, 2, 19, 1, 2, 3, 456789, tzinfo=timezone.utc)
m['b'] = DateParameter(FineTime(then), 'date par', default=99,
                       valid={(0, 9999999999): 'dok'}, typecode='%Y')
m['c'] = StringParameter(
    'Right', 'str par', {'': 'sok'}, 'cliche', 'B')
# Demo ``toString()`` function. The result (detail level=0) should be ::
print(x.toString())
# For more examples see tests/test_dataset.py

print('''
pal
===

Store a Product in a Pool and Get a Reference Back
--------------------------------------------------


Create a product and a productStorage with a pool registered
''')

# disable debugging messages
logger = logging.getLogger('')
logger.setLevel(logging.WARNING)


# a pool for demonstration will be create here
demopoolpath = '/tmp/demopool_' + getpass.getuser()
demopoolurl = 'file://' + demopoolpath
# clean possible data left from previous runs
os.system('rm -rf ' + demopoolpath)
if PoolManager.isLoaded(DEFAULT_MEM_POOL):
    PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
PoolManager.removeAll()

# create a prooduct and save it to a pool
x = Product(description='save me in store')
# add a tabledataset
s1 = [('energy', [1, 4.4, 5.6], 'eV'), ('freq', [0, 43.2, 2E3], 'Hz')]
x["Spectrum"] = TableDataset(data=s1)
# create a product store
pstore = ProductStorage(poolurl=demopoolurl)
pstore

# save the product and get a reference
prodref = pstore.save(x)
# This gives detailed information of the product being referenced
print(prodref)

# get the urn string
urn = prodref.urn
print(urn)    # urn:demopool_mh:fdi.dataset.product.Product:0

# re-create a product only using the urn

newp = ProductRef(urn).product
# the new and the old one are equal
print(newp == x)   # == True


print("""
Context: a Product with References
----------------------------------
""")

# the reference can be stored in another product of Context class
p1 = Product(description='p1')
p2 = Product(description='p2')
# create an empty mapcontext that can carry references with name labels
map1 = MapContext(description='product with refs 1')
# A ProductRef created from a lone product will use a mempool
pref1 = ProductRef(p1)
pref1

# A productStorage with a pool on disk
pref2 = pstore.save(p2)
pref2.urn

# how many prodrefs do we have? (do not use len() due to classID, version)
map1['refs'].size()   # == 0

len(pref1.parents)   # == 0

len(pref2.parents)   # == 0

# add a ref to the contex. every ref has a name in mapcontext
map1['refs']['spam'] = pref1
# add the second one
map1['refs']['egg'] = pref2
# how many prodrefs do we have? (do not use len() due to classID, version)
map1['refs'].size()   # == 2

len(pref2.parents)   # == 1

pref2.parents[0] == map1

pref1.parents[0] == map1

# remove a ref
del map1['refs']['spam']
# how many prodrefs do we have? (do not use len() due to classID, version)
map1.refs.size()   # == 1

len(pref1.parents)   # == 0

# add ref2 to another map
map2 = MapContext(description='product with refs 2')
map2.refs['also2'] = pref2
map2['refs'].size()   # == 1

# two parents
len(pref2.parents)   # == 2

pref2.parents[1] == map2

print("""
Query a ProdStorage
-------------------
""")

# clean possible data left from previous runs
defaultpoolpath = '/tmp/pool_' + getpass.getuser()
newpoolname = 'newpool_' + getpass.getuser()
newpoolpath = '/tmp/' + newpoolname
os.system('rm -rf ' + defaultpoolpath)
os.system('rm -rf ' + newpoolpath)
if PoolManager.isLoaded(DEFAULT_MEM_POOL):
    PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
PoolManager.removeAll()
# make a productStorage
defaultpoolurl = 'file://'+defaultpoolpath
pstore = ProductStorage(poolurl=defaultpoolurl)
# make another
newpoolurl = 'file://' + newpoolpath
pstore2 = ProductStorage(poolurl=newpoolurl)

# add some products to both storages
n = 7
for i in range(n):
    a0, a1, a2 = 'desc %d' % i, 'fatman %d' % (i*4), 5000+i
    if i < 3:
        x = Product(description=a0, instrument=a1)
        x.meta['extra'] = Parameter(value=a2)
    elif i < 5:
        x = Context(description=a0, instrument=a1)
        x.meta['extra'] = Parameter(value=a2)
    else:
        x = MapContext(description=a0, instrument=a1)
        x.meta['extra'] = Parameter(value=a2)
        x.meta['time'] = Parameter(value=FineTime1(a2))
    if i < 4:
        r = pstore.save(x)
    else:
        r = pstore2.save(x)
    print(r.urn)
# Two pools, 7 products
# [P P P C] [C M M]
#  0 1 2 3   4 5 6

# register the new pool above to the  1st productStorage
pstore.register(newpoolname)
len(pstore.getPools())   # == 2

# make a query on product metadata, which is the variable 'm'
# in the query expression, i.e. ``m = product.meta; ...``
# But '5000 < m["extra"]' does not work. see tests/test.py.
q = MetaQuery(Product, 'm["extra"] > 5001 and m["extra"] <= 5005')
# search all pools registered on pstore
res = pstore.select(q)
# [2,3,4,5]
len(res)   # == 4
[r.product.description for r in res]


def t(m):
    # query is a function
    import re
    return re.match('.*n.1.*', m['instrument'].value)


q = MetaQuery(Product, t)
res = pstore.select(q)
# [3,4]
[r.product.instrument for r in res]

# same as above but query is on the product. this is slow.
q = AbstractQuery(Product, 'p', '"n 1" in p.instrument')
res = pstore.select(q)
# [3,4]
[r.product.instrument for r in res]
