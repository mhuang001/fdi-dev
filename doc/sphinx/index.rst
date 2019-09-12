.. spdc documentation master file, created by
   sphinx-quickstart on Sun Aug 18 13:59:34 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

==================================================
 Self-describing Portable Dataset Container (SPDC)
==================================================

Features
========

With SPDC one can package data set into **modular** Data Products with annotation (description and units) and meta data (data about data). By combining arrays or tables of Products one can define highly complex structures.

**Access APIs** of the components of 'SPDCs' are convenient, making it easier for **scripting and data mining**.

All levels of SPDC Products and their component (datasets or metadata) are portable (**serializable**) in human-friendly standard format, allowing machine data processors on different platforms to re-construct or parse SPDC. Even a human with a web browser can understand the data.

Most SPDC Products and components implement **event sender and listener interfaces**, allowing **scalable data-driven** processing pipelines to be constructed.

Reference SPDC storage pool (file based and partially implemented memory based) are provided for data **storage** and for all persistent data to be referenced to with **URNs** (Universal Resource Names).

'Context' type of SPDCs are provided so that references of SPDCs can become components, enabling SPDCs to encapsulate rich, deep, **sophisticated, and accessible contextual information**, yet remain light weight.

On the data processor end, an HTML **server** with **RESTful APIs** is provided to exchange SPDC data, especially suitable for **Docker containers** running Linux. There are a lot of legacy software, or software only runs on a specific combination of OS type, version, language, and library. These software could be highly expensive to replace but need to be run side-by-side with new software to form an integral data processing pipeline, or, often, a network of inter-linked "nodes" of  processing tasks, instead of a "line". Docker containers are often the perfect solution to insulate software with incompatible dependencies. SPDC allows such processing tasks to run in the Processing Node Server's memory space, in a daemon process, or in the OS, receiving input and delivering output through a 'delivery man' protocol, in a docker, or a normal server.

SPDC Python packages
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


