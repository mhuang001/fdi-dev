======================================================
**Data Containers**: Data sets and Meta data
======================================================


.. contents:: Table of Contents
	      :depth: 3


Rationale
=========

Data products  produced by data processing procedures are meant to be read, underatood, and used by others. Many people tend to store data with no note of meaning attached to those data. Without attached explanation, it is difficult for other people to fully understand or use correctly a collection of numbers. It could be difficult for even the data producer to recall the exact meaning of the numbers after a while. When someone receives a data 'product', besides dataets, one would expect explanation informaion associated with the product. 

FDI implements a data product container scheme so that not only description and other metadata (data about data) are always attached to the "payload" data, but also that your data can have its context data attached as light weight references. One can organize scalar, vector, array, table types of data in the form of sequences, mappings, with nesting and referencing.

FDI is meant to be a small open-source package. Data stored in FDI ojects are easily accessible with Python API and are exported (serialized and stored by default) in cross-platform, human-readable JSON format. There are heavier formats (e..g. HDF5) and packages (e.g. iRODS) for similar goals. FDI's data model was originally inspired by  `Herschel Common Software System (v15)  products <https://www.cosmos.esa.int/web/herschel/data-products-overview/>`_, taking other  requirements of scientific observation and data processing into account. The APIs are kept as compatible with HCSS (written in Java, and in Jython for scripting) as possible.


Data Containers
===============

Dataset
-------

Three types of datasets are implemented to store potentially any hierarchical data as a dataset.
Like a product, all datasets may have meta data, with the distinction that the meta data of a dataset is related to that particular dataset only.

:array dataset: a dataset containing array data (say a data vector, array, cube etc...) and may have a unit and a typecode for efficient storing.

Examples (from :doc:`quickstart` page):

.. include:: quickstart.rst
   :start-after: ArrayDataset -- sequence of data in the same unit and format
   :end-before: TableDataset -- a set of named Columns and their metadata

:table dataset: a dataset containing a collection of columns with column header as the key. Each column contains array dataset. All columns have the same number of rows.

Examples (from :doc:`quickstart` page):

.. include:: quickstart.rst
   :start-after: TableDataset -- a set of named Columns and their metadata
   :end-before: Metadata and Parameter - Parameter


:composite dataset: a dataset containing a collection of datasets. This allows arbitrary complex structures, as a child dataset within a composite dataset may be a composite dataset itself and so on...

			     
Meta data and Parameters
------------------------

FDI datasets and products not only contain data, but also their metadata -- data about the "payload" data. Metadata is defined as a collection of named Parameters.

Often a parameter shows a property. So a parameter in the metadata of a dataset or product is often called a property.
	   
:Parameter: scalar or vector variable with attributes. 
	    There are the following parameter types:

   * *Parameter*: Types are defined in :attr:`metadata.ParameterTypes`. If requested, a Parameter can check its value or a given value with the validity specification, which can be a combination of descrete values, ranges, and bit-masked values.
   * *NumericParameter*
   * *DateParameter*
   * *StringParameter*

+-------------------+--------------------------+------------------------------+
|**Parameter class**|   **parameter value**    |   **parameter attributes**   |
+-------------------+--------------------------+------------------------------+
|Parameter          |typed objects             |description, type, validity   |
|                   |                          |descriptor, and default value |
+-------------------+--------------------------+------------------------------+
|NumericParameter   |a number (scalar), a      |all above plus a unit and a   |
|                   |:class:`Vector2D` (2D), a |typecode                      |
|                   |:class:`Vector` (3D), or a|                              |
|                   |:class:`Quaternion` (4D)  |                              |
+-------------------+--------------------------+------------------------------+
|DateParameter      |:class:`FineTime`         |Same as Parameter, `type` is  |
|                   |date-time                 |'finetime', Python            |
|                   |                          |:attribute:`datetime.format`  |
|                   |                          |string as the default         |
|                   |                          |`typecode`.                   |
+-------------------+--------------------------+------------------------------+
|StringParameter    |:class:`String`           |Same as Parameter, `type` is  |
|                   |                          |'string', 'B' (for byte       |
|                   |                          |unsigned) as the default      |
|                   |                          |`typecode`                    |
+-------------------+--------------------------+------------------------------+


Examples (from :doc:`quickstart` page):

.. include:: quickstart.rst
   :start-after: Metadata and Parameter - Parameter
   :end-before: Metadata and Parameter - Metadata

:Metadata: class manages parameters for datasets and products.

Examples (from :doc:`quickstart` page):

.. include:: quickstart.rst
   :start-after: Metadata and Parameter - Metadata
   :end-before: Product with metadata and datasets

run tests
=========

You can test sub-package ``dataset`` and ``utils`` with ``test1`` and ``test5`` respectively.

In the install directory:

.. code-block:: shell

		make test1
		make test5

``test3`` is for *pns server self-test only*

Design
======

Packages

.. image:: ../_static/packages_dataset.png

Classes

.. image:: ../_static/classes_dataset.png

.. inheritance-diagram:: fdi
