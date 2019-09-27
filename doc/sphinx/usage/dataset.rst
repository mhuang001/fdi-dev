=====================================
**dataset**: Model for Data Container
=====================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


Rationale
=========

A data processing task produces data products that are meant to be shared by other people. When someone receives a data 'products' s/he woud expect explanation informaion associated the product.

Many people tend to store data with no meaning attached to them. Without attach meaning of the collection of numbers, it is difficult for other people to fully understand the data. It could be difficult for even the data producer to recall the exact meaning of the numbers after a while.

This package implements a data product modeled after `Herschel Common Software System (v15)  products <https://www.cosmos.esa.int/web/herschel/data-products-overview/>`_, taking other  requirements of scientific observation and data processing into account. The APIs are kept as compatible with HCSS (written in Java, and in Jython for scripting) as possible, so that HCSS could be re-used with SPDC.


Definitions
===========

Product
-------

A product has
   * zero or more datasets: defining well described data entities (say images, tables, spectra etc...). 
   * history of this product: how was this data created, 
   * accompanying meta data -- required information such as who created this product, what does the data reflect (say instrument) and so on; possible additional meta data specific to that particular product type.

Dataset
-------

Three types of datasets are implemented to store potentially any data as a dataset.
Like a product, all datasets may have meta data, with the distinction that the meta data of a dataset is related to that particular dataset only.

:array dataset: a dataset containing array data (say a data vector, array, cube etc...) and may have a unit. 
:table dataset: a dataset containing a collection of columns. Each column contains array data (say a data vector, array, cube etc...) and may have a unit. All columns have the same number of rows. Together they make up the table. 
:composite dataset: a dataset containing a collection of datasets. This allows arbitrary complex structures, as a child dataset within a composite dataset may be a composite dataset itself and so on...

Metadata and Parameters
-----------------------

:Meta data: data about data. Defined as a collection of parameters. 

:Parameter: named scalar variables. 
	    This package provides the following parameter types:

   * _Parameter_: Contains an arbitrary value and no unit
   * _NumericParameter_: Contains a number with possibly a unit

Apart from the value of a parameter you can ask it for its description and -if it is a numeric parameter- for its unit as well. 

History
-------

The history is a lightweight mechanism to record the origin of this product or changes made to this product. Lightweight means, that the Product data itself does not  records changes, but external parties can attach additional information to the Product which reflects the changes.

The sole purpose of the history interface of a Product is to allow notably pipeline tasks (as defined by the pipeline framework) to record what they have done to generate and/or modify a Product. 

Serializability
---------------

In order to transfer data across the network between heterogeneous nodes data needs to be serializable.
JSON format is being considered to transfer serialized data for its wide adoption, availability of tools, ease to use with Python, and simplicity.

run tests
=========

In the install directory:

.. code-block:: shell

		./test 1

Design
======

Packages

.. image:: ../_static/packages_dataset.png

Classes

.. image:: ../_static/classes_dataset.png

Examples
========

ArrayDataset
------------

	
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

>>> # data access
... 
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
# make a 4-D array of 0's
   
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

.. code-block::
   
   from dataset.dataset import TableDataset

   a1 = [dict(name='col1', unit='keV', column=[1, 4.4, 5.4E3]),
   dict(name='col2', unit='cnt', column=[0, 43.2, 2E3])
   ]
   v = TableDataset(data=a1)
   
   >>> v.getColumnName(0)
   'col1'
   >>> v.getValueAt(rowIndex=1, columnIndex=1)
   43.2
   >>> v.setValueAt(aValue=42, rowIndex=1, columnIndex=1)
   >>> v.getValueAt(rowIndex=1, columnIndex=1)
   42

Metadata and Parameter
----------------------

.. code-block::

   from dataset.metadata import Parameter, NumericParameter, MetaData

   a1 = 'parameter_1'
   a2 = Parameter(description='test param', value=534)
   v = MetaData(description='my metadata')
   v[a1] = a2
   v['more'] = NumericParameter(description='another param', value=2.3, unit='sec')
   >>> print(v)
   MetaData[my metadata, parameter_1 = Parameter{ description = "test param", value = 534, type = int}, more = NumericParameter{ description = "another param", value = "2.3", unit = "sec", type = "float"}, ]
   >>> print(v.description) 
   my metadata
   >>> print(v['more'])
   NumericParameter{ description = "another param", value = "2.3", unit = "sec", type = "float"}
   >>> v['parameter_1'].value
   534


Product
-------

.. code-block::
   
   from dataset.product import Product
   from dataset.dataset import ArrayDataset, TableDataset

   x = Product(description="This is my product example",  instrument="MyFavourite", modelName="Flight")
   # ways to add datasets
   i0 = 6
   i1 = [[1, 2, 3], [4, 5, i0], [7, 8, 9]]
   image = ArrayDataset(data=i1, unit='magV', description='image 1')
   s1 = [dict(name='col1', unit='keV', column=[1, 4.4, 5.4E3]),
   dict(name='col2', unit='cnt', column=[0, 43.2, 2E3])]
   spec = TableDataset(data=s1)
   x["RawImage"] = image
   >>> print( x.sets["RawImage"].data[1][2] )                  # should be i0
   0
   x.set('QualityImage', 'aQualityImage')   # diff syntax same function as above
   x.sets["Spectrum"] = spec
   >>> x["Spectrum"].getValueAt(columnIndex=1, rowIndex=0)   # should be 0
   0

For more examples see tests/test_dataset.py

