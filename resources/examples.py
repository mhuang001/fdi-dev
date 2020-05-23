from fdi.dataset.dataset import ArrayDataset

a1 = [1, 4.4, 5.4E3, -22, 0xa2]      # a 1D array of data
v = ArrayDataset(data=a1, unit='ev', description='5 elements')
v

pass  # data access
v[2]

v.unit

v.unit = 'm'
v.unit

# iteration

for m in v:
    print(m)

[m**3 for m in v if m > 0 and m < 40]

pass  # slice

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
from fdi.dataset.dataset import TableDataset
a1 = [dict(name='col1', unit='eV', column=[1, 4.4, 5.4E3]),
      dict(name='col2', unit='cnt', column=[0, 43.2, 2E3])
      ]
v = TableDataset(data=a1)

pass  # many other ways to create a TableDataset

v3 = TableDataset(data=[('col1', [1, 4.4, 5.4E3], 'eV'),
                        ('col2', [0, 43.2, 2E3], 'cnt')])
v == v3


pass  # quick and dirty

pass  # quick and dirty. data are list of lists without names or units
a5 = [[1, 4.4, 5.4E3], [0, 43.2, 2E3]]
v5 = TableDataset(data=a5)
[c.data for c in v5.data.values()]    # a5
v5['col1'][0]    # 1
v5['col2'][1]    # 43.2

pass  # add, set, and replace columns
pass  # column set / get
u
= TableDataset()
c1 = Column([1, 4], 'sec')
u.addColumn('col3', c1)
u.columnCount        # 1

pass  # for non-existing names set is addColum.
c2 = Column([2, 3], 'eu')
u['col4'] = c2
u['col4'][0]    # 2

u.columnCount        # 2

pass  # replace column for existing names
c3 = Column([5, 7], 'j')
u['col4'] = c3
u['col4'][0]    # c3.data[0]

pass  # addRow
u.rowCount    # 2

cc = copy.deepcopy(c1)
c33, c44 = 3.3, 4.4
cc.append(c33)
u.addRow({'col4': c44, 'col3': c33})
u.rowCount    # 3

u['col3']    # cc

pass  # removeRow
u.removeRow(u.rowCount - 1)    # [c33, c44]
u.rowCount    # 2


pass        # access

pass  # unit access
print(u['col4'].unit)  # == 'j'

pass  # with indexOf
print(u.indexOf('col3'))  # == u.indexOf(c)

print(u.indexOf(c))


pass  # set cell value
u.setValueAt(aValue=42, rowIndex=1, columnIndex=1)
print(u.getValueAt(rowIndex=1, columnIndex=1))    # 42

pass  # syntax ``in``
[c for c in u]  # list of column names ['col1', 'col2']

pass   # run this to see ``toString()``

from fdi.dataset.dataset import TableDataset
ELECTRON_VOLTS = 'eV'
SECONDS = 'sec'
t = [x * 1.0 for x in range(10)]
e = [2 * x + 100 for x in t]
pass # creating a table dataset to hold the quantified data
x = TableDataset(description="Example table")
x["Time"] = Column(data=t, unit=SECONDS)
x["Energy"] = Column(data=e, unit=ELECTRON_VOLTS)
ts = x.toString()
print(ts)

'''the output is::

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
'''

'''
Metadata and Parameter
----------------------

Creation


pass  # creation

v = MetaData()
a1 = 'foo'
a2 = Parameter(description='test param', value=900)
v.set(a1, a2)
print(v)
MetaData['foo']

access

pass  # set parameter with several syntaxes
a3 = 'more'
v.set(name=a1, newParameter=a3)
print(v[a1])  # == a3
more

a4 = NumericParameter(description='another param',
                      value=2.3, unit='sec')
v[a3] = a4
print(v)
MetaData['foo', 'more']
v.toString()
'MetaData{[more = NumericParameter{ description = "another param", value = "2.3", unit = "sec", type = ""}, ], listeners = []}'

pass  # remove parameter
v.remove(a1)  # inherited from composite
'more'
print(v.size())  # == 1
1


Product
-------

Creation:


x = Product(description="product example with several datasets",
            instrument="Crystal-Ball", modelName="Mk II")

print(x.meta['description'])  # == "product example with several datasets"
product example with several datasets

print(x.instrument)  # == "Crystal-Ball"
Crystal-Ball

pass  # ways to add datasets
i0 = 6
i1 = [[1, 2, 3], [4, 5, i0], [7, 8, 9]]
i2 = 'ev'                 # unit
i3 = 'image1'  # description
image = ArrayDataset(data=i1, unit=i2, description=i3)

x["RawImage"] = image
print(x["RawImage"].data)  # [1][2] == i0
[[1, 2, 3], [4, 5, 6], [7, 8, 9]]

pass  # no unit or description. different syntax but same function as above
x.set('QualityImage', ArrayDataset(
    [[0.1, 0.5, 0.7], [4e3, 6e7, 8], [-2, 0, 3.1]]))
print(x["QualityImage"].unit)  # is None
None

pass  # add a tabledataset
s1 = [('col1', [1, 4.4, 5.4E3], 'eV'),
      ('col2', [0, 43.2, 2E3], 'cnt')]
x["Spectrum"] = TableDataset(data=s1)

pass  # mandatory properties are also in metadata
x.creator = "Me, myself and I"
print(x.creator)  # == "Me, myself and I"
Me, myself and I
pass  # This is also changed
print(x.meta["creator"])  # == "Me, myself and I"
Me, myself and I

``toString()`` function::

    # Product
    # description = "product example with several datasets"
    # meta = MetaData{[description = product example with several datasets, creator = Me, myself and I, creationDate = 2000-01-01T00:00:00.000000 TAI(0), instrument = Crystal-Ball, startDate = , endDate = , rootCause = UNKNOWN, modelName = Mk II, type = UNKNOWN, mission = SVOM, ], listeners = [Product 7696577608224 "product example with several datasets", ]}
    # History
    # description = "UNKNOWN"
    # meta = MetaData{[], listeners = []}
    # data =

    # data =

    # [ RawImage ]
    # ArrayDataset
    # description = "image1"
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

    0.1 4000.0 - 2
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
== =

Create a product and a productStorage with a pool registered


pass  # disable debugging messages
logger = logging.getLogger('')
logger.setLevel(logging.WARNING)


pass  # a pool for demonstration will be create here
demopoolpath = '/tmp/demopool'
demopool = 'file://' + demopoolpath
pass  # clean possible data left from previous runs
os.system('rm -rf ' + demopoolpath)
0

create a prooduct and save it to a pool

x = Product(description='in store')
pass  # add a tabledataset
s1 = [('energy', [1, 4.4, 5.6], 'eV'), ('freq', [0, 43.2, 2E3], 'Hz')]
x["Spectrum"] = TableDataset(data=s1)
pass  # create a product store
pstore = ProductStorage(pool=demopool)

pass  # save the product and get a reference
prodref = pstore.save(x)
print(prodref)
ProductRef{ProductURN = urn: file: // /tmp/demopool: Product: 0, meta = MetaData['description', 'creator', 'creationDate', 'instrument', 'startDate', 'endDate', 'rootCause', 'modelName', 'type', 'mission']}

the reference can be used in another product

pass  # create an empty mapcontext
mc = MapContext()
pass  # put the ref in the context.
pass  # The manual has this syntax mc.refs.put('xprod', prodref)
pass  # but I like this for doing the same thing:
mc['refs']['very-useful'] = prodref
pass  # get the urn string
urn = prodref.urn
print(urn)
urn: file: // /tmp/demopool: Product: 0

re-create a product only using the urn

newp = ProductRef(urn).product
pass  # the new and the old one are equal
print(newp == x)
True


x = BaseProduct(description="This is my product example")
pass  # print(x.__dict__)
pass  # print(x.meta.toString())
pass  # pdb.set_trace()
assert x.meta['description'].value == "This is my product example"
assert x.description == "This is my product example"
assert x.meta['type'].value == x.__class__.__qualname__
pass  # ways to add datasets
i0 = 6
i1 = [[1, 2, 3], [4, 5, i0], [7, 8, 9]]
i2 = 'ev'                 # unit
i3 = 'img1'  # description
image = ArrayDataset(data=i1, unit=i2, description=i3)

x["RawImage"] = image
assert x["RawImage"].data[1][2] == i0
pass  # no unit or description. diff syntax same function as above
x.set('QualityImage', ArrayDataset(
    [[0.1, 0.5, 0.7], [4e3, 6e7, 8], [-2, 0, 3.1]]))
assert x["QualityImage"].unit is None
pass  # add a tabledataset
s1 = [('col1', [1, 4.4, 5.4E3], 'eV'),
      ('col2', [0, 43.2, 2E3], 'cnt')
      ]
spec = TableDataset(data=s1)
x["Spectrum"] = spec
assert x["Spectrum"].getValueAt(columnIndex=1, rowIndex=0) == 0
'''
