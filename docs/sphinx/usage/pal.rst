=============================
**PAL**: Product Access Layer
=============================

.. contents:: Table of Contents
	      :depth: 3


Product Access Layer allows data stored logical "pools" to be accessed with light weight product refernces by data processers, data storage, and data consumers. A data product can include a context built with references of relevant data. A ``ProductStorage`` interface is provided to handle saving/retrieving/querying data in registered pools.



Rationale
=========

In a data processing pipeline or network of processing nodes, data products are generated within a context which may include input data, reference data, and auxiliary data of many kind. It is often needed to have relevant context recorded with a product. However the context could have a large size so including their actual data as metadata of the product is often impractical.

Once FDI data are generated they can have a reference through which they can be accessed. The size of such references are typically less than a few hundred bytes, like a URL. In the product context only data references are recorded.

This package provides ``MapContext``, ``ProductRef``, ``Urn``, ``ProductStorage``, ``ProductPool``, and ``Query`` classes (simplified but mostly API-compatible with `Herschel Common Science System v15.0`_) for the storing, retrieving, tagging, and context creating of data product modeled in the dataset package.

.. _Herschel Common Science System v15.0: http://herschel.esac.esa.int/hcss-doc-15.0/load/sg/html/Sadm.Pal.html

Definitions
===========

URN
---

.. currentmodule:: fdi.pal.urn

.. note:: The following is from :class:`Urn`
   
.. include:: ../../../fdi/pal/urn.py
   :start-after: About_URN
   :end-before: """

.. note:: The following is from :func:`parse_poolurl`

.. include:: ../../../fdi/pal/urn.py
   :start-after: About_poolURL
   :end-before: """
		
	   
ProductRef
----------

This class not only holds the URN of the product it references to, but also records who ( the _parents_) are keeping this reference.

ProductStorage
--------------

A centralized access place for saving/loading/querying/deleting data organized in conceptual pools. One gets a ProductRef when saving data.

ProductPool
-----------

An place where products can be saved, with a reference for the saved product generated. The product can be retrieved with the reference. Pools based on different media or networking mechanism can be implemented. Multiple pools can be registered in a
ProductStorage front-end where users can do the saving, loading, querying etc. so that the pools are collectively form a larger logical storage.

The reference LocalPool is shown in the following YAML-like schematic:

.. code-block::  yaml
   
   Pool:!!dict
          _classes:!!odict
              product0_class_name:!!dict
                      currentSN:!!int #the serial number of the latest added prod to the pool
                             sn:!!list
                                 - serial number of a prod
                                 - serial number of a prod
                                 - ...
              product1_class_name:
              ...
          _urns:!!odict
              urn0:!!odict
                      meta:!!MetaData #prod.meta
                      tags:!!list
                            - $tag
                            - $tag
                            - ...
              urn1:!!odict
	      ...
          _tags:!!odict
              urns:!!list
                   - $urn
                   - $urn
                   - ...

	  urn0:!!serialized product
	  urn1:!!serialized product
	  ...

Examples (from :doc:`quickstart` page):

.. include:: quickstart.rst
   :start-after: Product Pool and Product References
   :end-before: Context -- a Product with References



Context and MapContext
----------------------

Context is a Product that holds a set of :class:`ProductRef` s that accessible by keys. The keys are strings for MapContext which usually maps names to product references.


Examples (from :doc:`quickstart` page):

.. include:: quickstart.rst
   :start-after: Context -- a Product with References
   :end-before: Query a Storage to get saved Products

	  
Query
-----

One can  make queries to a ProductStorage and get back a list of references to products that satisfy search chriteria. Queries can be constructed using Python predicate expressions about a product and its metadata, or a function that returns True or False.

Examples (from :doc:`quickstart` page):

.. include:: quickstart.rst
   :start-after: Query a Storage to get saved Products
   :end-before: END of examples

			  

run tests
=========

To test PAL functionalities based on local (JSON) pool and memory pool, run in the same directory:

.. code-block:: shell

		make test2

To test functionalities based on http client pool, in one terminal run

.. code-block:: shell

		make runpoolserver

run

.. code-block:: shell

		make testhttp

examine output.

		
Design
======

Packages

.. image:: ../_static/packages_pal.png

Classes

.. image:: ../_static/classes_pal.png

