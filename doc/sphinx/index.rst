=========
ADASS2019
=========

Abstract
========


SPDC is a 'container' package written in Python for packing different types of data together, and letting the container take care of inter-platform compatibility, serialisation, persistence, and data object referencing that enables lazy-loading. The word 'container' in the name is more closely associated that is 'shipping container' instead of 'docker container'.

With SPDC one can pack data of different format into **modular** Data Products, together with annotation (description and units) and meta data (data about data). One can associate groups, arrays, or tables of Products using basic data structures such as sets, sequences (Python ``list``), mappings (Python ``dict``), or custom-made classes. SPDC accomodates nested and highly complex structures.

**Access APIs** of the components of 'SPDCs' are convenient, making it easier for **scripting and data mining** directly 'on SPDCs'.

All levels of SPDC Products and their component (datasets or metadata) are portable (**serializable**) in human-friendly standard format (JSON implemented), allowing machine data processors on different platforms to parse, access internal components, or re-construct a SPDC. Even a human with a web browser can understand the data.

The ``toString()`` method of major containers classes outputs nicely formated text representation of complex data to help converting SPDC to ASCII.

Most SPDC Products and components implement **event sender and listener interfaces**, enabling **scalable data-driven** processing pipelines.

SPDC storage 'pools' (file based and implemented memory based) are provided as references for 1) data **storage** and, 2) for all persistent data to be referenced to with **URNs** (Universal Resource Names).

*Context* type of SPDCs are provided so that references of SPDCs can become components, enabling SPDCs to encapsulate rich, deep, **sophisticated, and accessible contextual data**, yet remain light weight.

For data processors, an HTML **server** with **RESTful APIs** is implemented (named Processing Node Server, PNS) to interface data processing modules. PNS is especially suitable for **Docker containers** in pipelines mixing **legacy software** or software of incompatible environments to form an integral data processing pipeline.



**dataset**: Model for Data Container
-------------------------------------


A data processing task produces data products that are meant to be shared by other people. When someone receives a data 'products' s/he woud expect explanation informaion associated the product.

Many people tend to store data with no meaning attached to them. Without attach meaning of the collection of numbers, it is difficult for other people to fully understand the data. It could be difficult for even the data producer to recall the exact meaning of the numbers after a while.

This package implements a data product modeled after `Herschel Common Software System (v15)  products <https://www.cosmos.esa.int/web/herschel/data-products-overview/>`_, taking other  requirements of scientific observation and data processing into account. The APIs are kept as compatible with HCSS (written in Java, and in Jython for scripting) as possible.


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

**pal**: Product Access Layer
=============================

Product Access Layer allows data stored logical "pools" to be accessed with light weight product refernces by data processers, data storage, and data consumers. A data product can include a context built with references of relevant data. A ProductStorage interface is provided to handle saving/retrieving/querying data in registered pools.


In a data processing pipeline or network of processing nodes, data products are generated within a context which may include input data, reference data, and auxiliary data of many kind. It is often needed to have relevant context recorded with a product. However the context could have a large size so including them as metadata of the product is often impractical.

Because once data are generated they can have a reference through which they can be accessed. The size of such references are typically less than a few hundred bytes, like a URL. In the product context only data references are recorded.

This package provides MapContext, ProductRef, Urn, ProductStorage classes (simplified but mostly API-compatible with `Herschel Common Science System v15.0`_) for the storing, retrieving, tagging, and context creating of data product modeled in the dataset package.

.. _Herschel Common Science System v15.0: http://herschel.esac.esa.int/hcss-doc-15.0/load/sg/html/Sadm.Pal.html


URN
---

The Universial Resource Name (URN) string has this format::

  urn:poolname:resourceclass:serialnumber

where

:resourceclass: fully qualified class name of the resource (product)
:poolname: scheme + ``://`` + place + directory
:scheme: ``file``, ``mem``, ``http`` ... etc
:place: ``192.168.5.6:8080``, ``c:``, an empty string ... etc
:directory:
     * for ``file`` scheme: ``/`` + name + ``/`` + name + ... + ``/`` + name
     * for ``mem`` scheme: ``/`` + name + ... + ``/`` + process_ID
:serialnumber:
     * for ``file`` scheme: internal index. str(int).
     * for ``mem`` scheme: python object id. str(int).

ProductRef
----------

This class not only holds the URN of the product it references to, but also records who ( the _parents_) are keeping this reference.

Context and MapContext
----------------------

Context is a Product that holds a set of ``productRef`` s that accessible by keys. The keys are strings for MapContext which usually maps names to product references.

ProductStorage
--------------

A centralized access place for saving/loading/querying/deleting data organized in conceptual pools. One gets a ProductRef when saving data.

ProductPool
-----------

An place where products can be saved, with a reference for the saved product generated. The product can be retrieved with the reference. Pools based on different media or networking mechanism can be implemented. Multiple pools can be registered in a
ProductStorage front-end where users can do the saving, loading, querying etc. so that the pools are collectively form a larger logical storage.


**pns**: Processing Node Server
===============================


Many data processing pipelines need to run software that only runs on a specific combination of OS type, version, language, and library. These software could be impractical to replace or modify but need to be run side-by-side with software of incompatible environments/formats to form an integral data processing pipeline, each software being a "node" to perform a  processing task. Docker containers are often the perfect solution to run software with incompatible dependencies.

PNS installed on a Docker container or a normal server allows such processing tasks to run in the PNS memory space, in a daemon process, or as an OS process receiving input and delivering output through a 'delivery man' protocol.

This Web API Server for a data processing pipeline/network node provides interfaces to configure the data processing task software (PTS) in a processing node, to make a run request, to deliver necessary input data, and to read results, all via web APIs.


Suppose the server address and port are ``127.0.0.1`` and ``5000``, respectively:

Run the Flask server in a terminal (see above) and open this in a browser:

http://127.0.0.1:5000/v0.6/

An online API documentation page similar to below is shown.

.. code-block:: json

		{
		"APIs": {
		"DELETE": [
		{
		"URL": "http://127.0.0.1:5000/v0.6/clean", 
		"description": " Removing traces of past runnings the Processing Task Software.\n    "
		}
		], 
		"GET": [
		{
		"URL": "http://127.0.0.1:5000/v0.6/init", 
		"description": "the initPTS file"
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/config", 
		"description": "the configPTS file"
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/run", 
		"description": "the file running PTS"
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/clean", 
		"description": "the cleanPTS file"
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/input", 
		"description": " returns names and contents of all files in the dir, 'None' if dir not existing. "
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/output", 
		"description": " returns names and contents of all files in the dir, 'None' if dir not existing. "
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/pnsconfig", 
		"description": "PNS configuration"
		}
		], 
		"POST": [
		{
		"URL": "http://127.0.0.1:5000/v0.6/calc", 
		"description": " generates result product directly using data on PNS.\n    "
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/testcalc", 
		"description": " generate post test product.\n    put the 1st input (see maketestdata in test_all.py)\n    parameter to metadata\n    and 2nd to the product's dataset\n    "
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/echo", 
		"description": "Echo"
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/run", 
		"description": " Generates a product by running script defined in the config under 'run'. Execution on the server host is in the pnshome directory and run result and status are returned.\n    "
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/testrun", 
		"description": "  Run 'runPTS' for testing, and as an example.\n    "
		}
		], 
		"PUT": [
		{
		"URL": "http://127.0.0.1:5000/v0.6/init", 
		"description": " Initialize the Processing Task Software by running the init script defined in the config. Execution on the server host is in the pnshome directory and run result and status are returned. If input/output directories cannot be created with serveruser as owner, Error401 will be given.\n    "
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/config", 
		"description": " Configure the Processing Task Software by running the config script. Ref init PTS.\n    "
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/pnsconf", 
		"description": " Configure the PNS itself by replacing the pnsconfig var\n    "
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/inittest", 
		"description": "     Renames the 'init' 'config' 'run' 'clean' scripts to \"*.save\" and points it to the '.ori' scripts.\n    "
		}
		]
		}, 
		"timestamp": 1566130779.0208821
		}

