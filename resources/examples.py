"""
The following demo for important dataset and pal functions are made by running fdi/resources/example.py with command ``elpy-shell-send-group-and-step [c-c c-y c-g]``
"""
import copy
from datetime import datetime
import logging
from fdi.dataset.product import Product
from fdi.dataset.metadata import Parameter, NumericParameter, MetaData
from fdi.dataset.finetime import FineTime1, utcobj
from fdi.dataset.dataset import ArrayDataset, TableDataset, Column
from fdi.pal.context import Context, MapContext
from fdi.pal.productref import ProductRef
from fdi.pal.productstorage import ProductStorage


a1 = [1, 4.4, 5.4E3, -22, 0xa2]      # a 1D array of data
v = ArrayDataset(data=a1, unit='ev', description='5 elements')
v

# data access
v[2]

v.unit

v.unit = 'm'
v.unit

# iteration
for m in v:
    print(m)

[m**3 for m in v if m > 0 and m < 40]

# slice
v[1:3]

v[2:-1]

v.data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
v[0:2]

'''
Run this to see a demo of the ``toString()`` function::

make a 4-D array: a list of 2 lists of 3 lists of 4 lists of 5 elements.
'''
s = [[[[i + j + k + l for i in range(5)] for j in range(4)]
      for k in range(3)] for l in range(2)]
x = ArrayDataset(data=s)
print(x.toString())

'''
TableDataset
------------

Creation
'''
a1 = [dict(name='col1', unit='eV', column=[1, 4.4, 5.4E3]),
      dict(name='col2', unit='cnt', column=[0, 43.2, 2E3])
      ]
v = TableDataset(data=a1)
v

# many other ways to create a TableDataset
v3 = TableDataset(data=[('col1', [1, 4.4, 5.4E3], 'eV'),
                        ('col2', [0, 43.2, 2E3], 'cnt')])
v == v3


# quick and dirty. data are list of lists without names or units
a5 = [[1, 4.4, 5.4E3], [0, 43.2, 2E3]]
v5 = TableDataset(data=a5)
[c.data for c in v5.data.values()]    # a5

v5['col1'][0]    # 1

v5['col2'][1]    # 43.2

# add, set, and replace columns
# column set / get
u = TableDataset()
c1 = Column([1, 4], 'sec')
u.addColumn('col3', c1)
u.columnCount        # 1

# for non-existing names set is addColum.
c2 = Column([2, 3], 'eu')
u['col4'] = c2
u['col4'][0]    # 2

u.columnCount        # 2

# replace column for existing names
c3 = Column([5, 7], 'j')
u['col4'] = c3
u['col4'][0]    # c3.data[0]

# addRow
u.rowCount    # 2

cc = copy.deepcopy(c1)
c33, c44 = 3.3, 4.4
cc.append(c33)
u.addRow({'col4': c44, 'col3': c33})
u.rowCount    # 3

u['col3']    # cc

# removeRow
u.removeRow(u.rowCount - 1)    # [c33, c44]

u.rowCount    # 2


# access

# unit access
u['col4'].unit  # == 'j'

# with indexOf
u.indexOf('col3')  # == u.indexOf(cc)

u.indexOf(c1)


# set cell value
u.setValueAt(aValue=42, rowIndex=1, columnIndex=1)
u.getValueAt(rowIndex=1, columnIndex=1)    # 42

# syntax ``in``
[c for c in u]  # list of column names ['col1', 'col2']

''
# run this to see ``toString()``
''
ELECTRON_VOLTS = 'eV'
SECONDS = 'sec'
t = [x * 1.0 for x in range(10)]
e = [2 * x + 100 for x in t]
# creating a table dataset to hold the quantified data
x = TableDataset(description="Example table")
x["Time"] = Column(data=t, unit=SECONDS)
x["Energy"] = Column(data=e, unit=ELECTRON_VOLTS)
print(x.toString())

"""
Parameter
---------

Creation
"""
# standard way -- with keyword arguments
a1 = 'a test parameter'
a2 = 300
a3 = 'integer'
v = Parameter(description=a1, value=a2, type_=a3)
v.description   # == a1

v.value   # == a2

v.type_   # == a3

# with no argument
v = Parameter()
v.description   # == 'UNKNOWN# inherited from Anotatable

v.value   # is None

v.type_   # == ''

# make a blank one then set attributes
v = Parameter(description=a1)
v.description   # == a1

v.value    # is None

v.type_   # == ''

v.setValue(a2)
v.setType(a3)
v.description   # == a1

v.value   # == a2

v.type_   # == a3

# test equivalence of v.setXxxx(a) and v.xxx = a
a1 = 'test score'
a2 = 98
v = Parameter()
v.description = a1
v.value = a2
v.description   # == a1

v.value   # == a2

# test equals
b1 = ''.join(a1)  # make a new string copy
b2 = a2 + 0  # make a copy
v1 = Parameter(description=b1, value=b2)
v.equals(v1)

v == v1

v1.value = -4
v.equals(v1)   # False

v != v1  # True

"""
Metadata
--------

Creation
"""
a1 = 'age'
a2 = NumericParameter(description='since 2000',
                      value=20, unit='year', type_='integer')
v = MetaData()
v.set(a1, a2)
v.get(a1)   # == a2

# add more parameter
a3 = 'Bob'
v.set(name='name', newParameter=Parameter(a3))
v.get('name').value   # == a3

# access parameters in metadata
v = MetaData()
# a more readable way to set a parameter
v[a1] = a2  # DRM doc case
# a more readable way to get a parameter
v[a1]   # == a2

v.get(a1)   # == a2

v['date'] = Parameter(description='take off at',
                      value=FineTime1.datetimeToFineTime(datetime.now(tz=utcobj)))
# names of all parameters
[n for n in v]   # == [a1, 'date']

print(v.toString())

# remove parameter
v.remove(a1)  # inherited from composite
print(v.size())  # == 1


"""
Product
-------

Creation:
"""
x = Product(description="product example with several datasets",
            instrument="Crystal-Ball", modelName="Mk II")
x.meta['description']  # == "product example with several datasets"

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
x["Spectrum"].toString()

# mandatory properties are also in metadata
# test mandatory BaseProduct properties that are also metadata
x.creator = ""
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


"""
Demo ``toString()`` function. Thevresult should be ::

For more examples see tests/test_dataset.py
"""
print(x.toString())

"""
pal
===

Create a product and a productStorage with a pool registered
"""
# disable debugging messages
logger = logging.getLogger('')
logger.setLevel(logging.WARNING)


# a pool for demonstration will be create here
demopoolpath = '/tmp/demopool'
demopool = 'file://' + demopoolpath
# clean possible data left from previous runs
os.system('rm -rf ' + demopoolpath)

# create a prooduct and save it to a pool
x = Product(description='in store')
# add a tabledataset
s1 = [('energy', [1, 4.4, 5.6], 'eV'), ('freq', [0, 43.2, 2E3], 'Hz')]
x["Spectrum"] = TableDataset(data=s1)
# create a product store
pstore = ProductStorage(pool=demopool)
pstore

# save the product and get a reference
prodref = pstore.save(x)
print(prodref)

# get the urn string
urn = prodref.urn
print(urn)    # urn:file:///tmp/demopool:Product:0

# re-create a product only using the urn

newp = ProductRef(urn).product
# the new and the old one are equal
print(newp == x)   # == True

# the reference can be used in another product
p1 = Product(description='p1')
p2 = Product(description='p2')
# create an empty mapcontext
map1 = MapContext(description='real map1')
# A ProductRef created from a lone product will use a mempool
pref1 = ProductRef(p1)
pref1

# use a productStorage with a pool on disk
pref2 = pstore.save(p2)
pref2

# how many prodrefs do we have? (do not use len() due to classID, version)
map1['refs'].size()   # == 0

len(pref1.parents)   # == 0

len(pref2.parents)   # == 0

# add a ref to the contex. every ref has a name in mapcontext
map1['refs']['prd1'] = pref1
# add the second one
map1['refs']['prd2'] = pref2
# how many prodrefs do we have? (do not use len() due to classID, version)
map1['refs'].size()   # == 2

len(pref2.parents)   # == 1

pref2.parents[0] == map1

pref1.parents[0] == map1

# remove a ref
del map1['refs']['prd1']
# how many prodrefs do we have? (do not use len() due to classID, version)
map1.refs.size()   # == 1

len(pref1.parents)   # == 0

# add ref2 to another map
map2 = MapContext(description='real map2')
map2.refs['also2'] = pref2
map2['refs'].size()   # == 1

# two parents
len(pref2.parents)   # == 2

pref2.parents[1] == map2
