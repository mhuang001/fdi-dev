=============================
**pal**: Product Access Layer
=============================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


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

The Universial Resource Name (URN) string has this format::

  urn:``poolname``:``resourcetype``:``serialnumber``

where

:poolname: Also called poolID, a (optionally path-like) string. Its format should follow that of a directory name, without leading or trailing ``/``.
:resourcetype: (fully qualified) class name of the resource (usually Product)
:serialnumber: internal index.

The ``poolname`` in a URN is a label. Although pool providers could use '/' in it to introduce internal heirachy. The ``PoolURL`` is used to give practical information of a pool. It is a local set-up detail that is supposed to be hidden from pool users. The format::

  ``schme``://``place````poolpath``/``poolname``

:scheme: Implementation protocol including ``file`` for :class:`LocalPool`, ``mem`` for :class:`MemPool`, ``http``, ``https`` for :class:`HttpclientPool`.
:place: IP:port such as``192.168.5.6:8080`` for ``http`` and ``https`` schemes, or an empty string for ``file`` and ``mem`` schemes.
:poolpath: The full path where the pool is stored, can have API version.  :meth:`ProductPool.transformpath` is used to map it further.
:poolname: same as in URN

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

	  
Query
-----

One can  make queries to a ProductStorage and get back a list of references to products that satisfy search chriteria. Queries can be constructed using Python predicate expressions about a product and its metadata, or a function that returns True or False.

run tests
=========

in the same directory:

.. code-block:: shell

		make test2


Design
======

Packages

.. image:: ../_static/packages_pal.png

Classes

.. image:: ../_static/classes_pal.png

