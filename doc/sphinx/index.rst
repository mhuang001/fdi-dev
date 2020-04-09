.. fdi documentation master file, created by
   sphinx-quickstart on Sun Aug 18 13:59:34 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

==================================================
 Flexible Dataset Integrator (FDI)
==================================================

FDI, known as SPDC before is written in Python for integrating different types of data, and letting the integrated product take care of inter-platform compatibility, serialisation, persistence, and data object referencing that enables lazy-loading.

Features
========

With FDI one can pack data of different format into **modular** Data Products, together with annotation (description and units) and meta data (data about data). One can associate groups, arrays, or tables of Products using basic data structures such as sets, sequences (Python ``list``), mappings (Python ``dict``), or custom-made classes. FDI accomodates nested and highly complex structures.

**Access APIs** of the components of 'FDIs' are convenient, making it easier for **scripting and data mining** directly 'on FDIs'.

All levels of FDI Products and their component (datasets or metadata) are portable (**serializable**) in human-friendly standard format (JSON implemented), allowing machine data processors on different platforms to parse, access internal components, or re-construct a FDI. Even a human with a web browser can understand the data.

The ``toString()`` method of major containers classes outputs nicely formated text representation of complex data to help converting FDI to ASCII.

Most FDI Products and components implement **event sender and listener interfaces**, allowing **scalable data-driven** processing pipelines to be constructed.

FDI storage 'pools' (file based and implemented memory based) are provided as references for 1) data **storage** and, 2) for all persistent data to be referenced to with **URNs** (Universal Resource Names).

*Context* type of FDIs are provided so that references of FDIs can become components, enabling FDIs to encapsulate rich, deep, **sophisticated, and accessible contextual data**, yet remain light weight.

For data processors, an HTML **server** with **RESTful APIs** is implemented (named Processing Node Server, PNS) to interface data processing modules. PNS is especially suitable for **Docker containers** in pipelines mixing **legacy software** or software of incompatible environments to form an integral data processing pipeline.


FDI Python packages
====================

-  The base data model is defined in package :doc:`dataset <usage/dataset>`.

-  Persistent data access, referencing, and Universal Resource Names are defined in package :doc:`pal <usage/pal>`.

-  A reference REST API server designed to communicate with a data processing docker using the data model is in package  :doc:`pns <usage/pns>`.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage/installation
   usage/dataset
   usage/pal
   usage/pns
   usage/quickstart
   
API Document
============

.. toctree::

   api/api
   
.. image:: _static/packages_dataset+pal.png

	   

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


