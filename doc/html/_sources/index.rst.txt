.. spdc documentation master file, created by
   sphinx-quickstart on Sun Aug 18 13:59:34 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

==================================================
 Self-describing Portable Dataset Container (SPDC)
==================================================

SPDC is a 'container' written in Python for packing different types of data together, and letting the container take care of inter-platform compatibility, serialisation, persistence, and data object referencing that enables lazy-loading. The word 'container' in the name is more closely associated that is 'shipping container' instead of 'docker container'.

Features
========

With SPDC one can pack data of different format into **modular** Data Products, together with annotation (description and units) and meta data (data about data). One can associate groups, arrays, or tables of Products using basic data structures such as sets, sequences (Python ``lists``), mappings (Python ``dict``), or custom-made classes. SPDC accomodates nested and highly complex structures.

**Access APIs** of the components of 'SPDCs' are convenient, making it easier for **scripting and data mining** directly 'on SPDCs'

All levels of SPDC Products and their component (datasets or metadata) are portable (**serializable**) in human-friendly standard format (JSON implemented), allowing machine data processors on different platforms to parse, access internal components, or re-construct a SPDC. Even a human with a web browser can understand the data.

Most SPDC Products and components implement **event sender and listener interfaces**, allowing **scalable data-driven** processing pipelines to be constructed.

SPDC storage 'pools' (file based and implemented memory based) are provided as references for 1) data **storage** and, 2) for all persistent data to be referenced to with **URNs** (Universal Resource Names).

*Context* type of SPDCs are provided so that references of SPDCs can become components, enabling SPDCs to encapsulate rich, deep, **sophisticated, and accessible contextual data**, yet remain light weight.

For data processors, an HTML **server** with **RESTful APIs** is implemented (named Processing Node Server, PNS) to exchange SPDC data, especially suitable for **Docker containers** running Linux. There are a lot of legacy software, or software only runs on a specific combination of OS type, version, language, and library. These software could be highly expensive to replace but need to be run side-by-side with new software to form an integral data processing pipeline, as "nodes" of  processing tasks. Docker containers are often the perfect solution to insulate software with incompatible dependencies. SPDC allows such processing tasks to run in the PNS memory space, in a daemon process, or in the OS, receiving input and delivering output through a 'delivery man' protocol.

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


