
==========
Change Log
==========

BETA0
=====

1.6.0 2021-06-10
----------------
http pool docker stablising; MetaDataParameter; messag queue;

1.5.0 2021-04-27
-----------------
httppool server API 0.7 python API path.

1.4.0 2021-04-17
-----------------
HttpClient pool not caching HK and with /api. ManagedPool. serial write0-through. 

1.3.0 2021-04-06
-----------------
Product pipeline dev support and pool improvements. Dockerize httpool with update.

1.2.0 2021-03-10
-----------------
array.array hashed and seriaalized. performance tuned ref vtse. docs improvements.

1.1.0 2021-02-20
-----------------
Packaging improvements. Use __getstate__ for serialization, hashing and comparison.

1.0 2021-01-17
-----------------
TableDataset numeric indexing, slicing, vLookUp. Basic performance enhancing. Parameter.split()

1.0rc9 2020-12-27
-----------------
YAML schema v1.4; ClassID->_STID; pInfo->zInfo; product subclassing sorted. MapContext sorted. y2p handles parents better. Context rule.

1.0rc8 2020-12-13
-----------------
DataType refactoring. YAML schema v1.3. Product builtin parameter properrties.

1.0rc7 2020-11-30
-----------------
ClassID changed to _STID: Serialization Type ID. toString() improvements.


1.0rc6 2020-11-23
-----------------

[DEV] [SERV]. monokaimod. quickstart and many other doc improvements

1.0rc5 2020-10-26
-----------------

Place info removed from URN.

1.0rc4 2020-10-10
-----------------

HTTP pool server an client integration.

1.0rc3 2020-09-23
-----------------

Lots of toString improvements. Tabulate-based array and table presentation.

1.0rc2 2020-09-10
-----------------

Document updates. Better presentation APIs. DOC as extras. Contex refctoring.

1.0rc1 2020-08-30
-----------------

Parameters support type, default, valid, typecode, and have a new type : DateParameter. YAML 1.1 have attrbutes accordingly, with correct default types. New ODict is serialisable.

1.0rc 2020-08-17
----------------

YAML v1.0 with datasets and metadata description unified and multiple inheriting. Revision of header keywords. and table sceme. Improvement of yaml2python and a custom moule loader. ProductInfo becomes a module object. Runs with FSC products.

0.20 2020-08-04
----------------

YAML v0.6 switch version and schema. multiple YAML files enabled by -y semantic change. remove version in serializableClassID.

0.19 2020-06-19
----------------

Product parammeter definition YAML schema v0.5 with valid format. v0.19

0.18c 2020-06-07
----------------

Names of lock directory and default pool have username to allow multi users to run fdi on the same machine.

0.18b 2020-06-05
---------------

Full classname in urn. Updated documentation.

0.18a 2020-06-04
---------------

remove duplicate 'description' key in YAML prod def (v0.4).

0.18 2020-06-04
---------------

Query. Parameter value comparison.

0.17 2020-05-10
---------------

Release to wider group of beta users, with a product-building package.

0.16 2020-05-10
---------------

pns uses user classes. config file relocates to ~/.config/pnslocal.py. 'fits_keyword'.

0.15 2020-05-01
---------------

Add Makefile to consolidate various commands, .readthdocs.yml for RTD. Sort out productInfo in Products.

0.14 2020-04-28
---------------

yaml2python configures product built-in meta attributes with YAML.


0.13 2020-04-21
---------------

refactor Product to have BaseProduct and info. Enforce configured types in Parameter. Enfore Parameter-only in metadata.

ALPHA1 SPDC
===========

0.12 2020-04-09
---------------

rename spdc to fdi

0.11 2020-04-04
---------------

parents for ProductRef, mempool, pal test improvements

0.10 2020-01-07
---------------

dataset is compatible with python 2.7

0.9 2019-12-25
--------------

Refactor to make spdc top-level package, instead of dataset, pal, pns

0.8 2019-09-15
--------------

Improved toString() for datasets. PAL refactoring.

0.7 2019-08-27
--------------

documentation with sphinx. vvpp docker works. release to FSC.

0.6 2019-08-17
--------------

listener, mem: URN, deserializable list

0.5 2019-08-11
--------------

Projects merged.

*ALPHA0*

=======
dataset
=======
0.1 2019-04-16
--------------

Prototype. Initial check-in.

0.2 2019-06-14
--------------

Supports pns v0.3

0.3 2019-07-04
--------------

ODict and refactoring

0.4 2019-07-24
--------------

Add Product Access Layer support

===
pns
===

Processing Node API Server Change Log
=======================================

0.1 2019-05-13
--------------

Prototype. Initial check-in.

0.2 2019-06-06
--------------

run by production web server

0.3 2019-06-14
--------------

run 'hello' shell script on server side with input and output

0.4 2019-06-27
--------------

REST compliance with PUT, new GET, DELETE. Improved serverside unit test.

===
pal
===
	
Change Log
==========

0.1 2019-07-24
--------------

Prototype. Initial check-in.

