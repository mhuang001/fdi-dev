======================================
**dataset**: Model for Data Containers
======================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


Rationale
=========

Data products  produced by data processing procedures are meant to be read, underatood, and used by others. Many people tend to store data with no note of meaning attached to those data. Without attached explanation, it is difficult for other people to fully understand or use correctly a collection of numbers. It could be difficult for even the data producer to recall the exact meaning of the numbers after a while. When someone receives a data 'product', besides dataets, one would expect explanation informaion associated with the product. 

FDI implements a data product container scheme so that not only description and other metadata (data about data) are always attached to the "payload" data, but also that your data can have its context data attached as light weight references. One can organize scalar, vector, array, table types of data in the form of sequences, mappings, with nesting and referencing.

FDI is meant to be a small open-source package. Data stored in FDI ojects are easily accessible with Python API and are exported (serialized and stored by default) in cross-platform, human-readable JSON format. There are heavier formats (e..g. HDF5) and packages (e.g. iRODS) for similar goals. FDI's data model was originally inspired by  `Herschel Common Software System (v15)  products <https://www.cosmos.esa.int/web/herschel/data-products-overview/>`_, taking other  requirements of scientific observation and data processing into account. The APIs are kept as compatible with HCSS (written in Java, and in Jython for scripting) as possible.


Data Containers
===============

Product
-------

A product has
   * zero or more datasets: defining well described data entities (say images, tables, spectra etc...). 
   * accompanying meta data -- required information such as who created this product, what does the data reflect (say instrument) and so on; possible additional meta data specific to that particular product type. A number of built-in Parameters can be specified in ``fdi/dataset/resourcese`` in YAML format. A helper utility ``yaml2python`` can be run using ``make py`` to generate test-ready Python code of product class module containing the built-ins.
   * history of this product: how was this data created.

Dataset
-------

Three types of datasets are implemented to store potentially any hierarchical data as a dataset.
Like a product, all datasets may have meta data, with the distinction that the meta data of a dataset is related to that particular dataset only.

:array dataset: a dataset containing array data (say a data vector, array, cube etc...) and may have a unit and a typecode for efficient storing.
:table dataset: a dataset containing a collection of columns with column header as the key. Each column contains array dataset. All columns have the same number of rows.
:composite dataset: a dataset containing a collection of datasets. This allows arbitrary complex structures, as a child dataset within a composite dataset may be a composite dataset itself and so on...

Metadata and Parameters
-----------------------

:Metadata: data about data. Defined as a collection of named Parameters. Often a parameter shows a property. So a parameter in the metadata of a dataset or product is often called a property.

:Parameter: scalar or vector variable with attributes. 
	    This package provides the following parameter types:

   * *Parameter*: Contains a value, description, type, validity specification, and default value. Value, default, and type are type-bound in metadata.ParameterTypes. If requested, a Parameter can check its value or a given value with the validity specification, which can be a combination of descrete values, ranges, and bit-masked values.
   * *NumericParameter*: Contains a number with a unit and a typecode besides those of Parameter.
   * *DateParameter*: Same as Parameter except taking a FineTime date-time date as the value, and Python datetime.format as the typecode.
   * *StringParameter*: Same as Parameter except taking a string as the value, and 'B' (for byte unsigned) as the default typecode.


History
-------

The history is a lightweight mechanism to record the origin of this product or changes made to this product. Lightweight means, that the Product data itself does not  records changes, but external parties can attach additional information to the Product which reflects the changes.

The sole purpose of the history interface of a Product is to allow notably pipeline tasks (as defined by the pipeline framework) to record what they have done to generate and/or modify a Product. 

Serializability
---------------

In order to transfer data across the network between heterogeneous nodes data needs to be serializable.
JSON format is used considering to transfer serialized data for its wide adoption, availability of tools, ease to use with Python, and simplicity.



run tests
=========

In the install directory:

.. code-block:: shell

		make test1
		make test2
		make test3
		make test5

You can test sub-package ``dataset``, ``pal``, *pns server self-test only*, and ``utils`` with ``test1``, ``test2``, ``test3``, and ``test5`` respectively.


Design
======

Packages

.. image:: ../_static/packages_dataset.png

Classes

.. image:: ../_static/classes_dataset.png

.. inheritance-diagram:: fdi
