FDI helps data producers and processors to build connections into isolated heterogeneous datasets. to assemble, organize, and integrate data into self-describing, modular, hierarchical, persistent, referenceable ``Products``, whose component datasets keep their own characteristicss and are easily accessible.

FDI provides scripting-friendly  APIs  and 
tools to define custom Products and generating Python class files. An integrated Product takes care of inter-platform compatibility, string representation, serialisation to simple exchange format, persistence to disk or server, and carrying references of other Products, enabling context-building and lazy-loading.

FDI's base data model is defined in package ``dataset``. Persistent data
access, referencing, and Universal Resource Names are defined in package
``pal``. A reference RESTful API server designed to communicate with a data
processing server/docker using the data model, and a reference data store (``pool``) server is in package ``pns``.

Install/Uninstall

For Users
=========

To install (It is a good idea to add ``--user`` at the end or to use a virtualenv to avoid disturbing Python setup.)

.. code-block:: shell

   python3 -m pip install http://mercury.bao.ac.cn:9006/mh/fdi/-/archive/v1.0.1/fdi-v1.0.1.tar.gz

If you want to install the ``develop`` branch:

.. code-block:: shell

   python3 -m pip install git+http://mercury.bao.ac.cn:9006/mh/fdi.git@develop
   
To uninstall:

.. code-block:: shell

           python3 -m pip uninstall fdi


For Developers and Admins
=========================

To install (It is a good idea to add ``--user`` at the end or to use a virtualenv to avoid disturbing Python setup.)

.. code-block:: shell

           FDIINSTDIR=/tmp   # change this to your installation dir
           cd $FDIINSTDIR
           git clone ssh://git@mercury.bao.ac.cn:9005/mh/fdi.git@develop
           cd fdi
           python3 -m pip install -e .[DEV]

If you want to install the ``master`` branch, remove the ``@develop`` part above..   
	   
To test your installation:

.. code-block:: shell

           make test

.. tip::

   To pass command-line arguments to ``pytest`` do, for example,
   
   .. code-block:: shell
		   
		make test T='-k Bas'

   to test ``BaseProduct`` in sub-package ``dataset``.

To generate ``baseproduct.py`` and ``product.py`` from YAML schema files in
``fdi/dataset/resources``:

.. code-block:: shell

           make py

Modify/Generate Documents
-------------------------

If you plan to compile documents in the ``doc`` directory, generate diagrams, API files, or HTML pages, run (in that order, respectively):

.. code-block:: shell

           make doc_plots
           make doc_api
           make doc_html

.. note:: Read-the-docs makes web pages from sources in ``doc/sphinx`` in the repository. Locally generated HTML pages are not on RTD or in the repository. The API files and plots, however need to go to the repo.
	   
Run Servers
-----------

If you plan to run the ``pns`` and/or the http pool server locally,
install the dependencies:

.. code-block:: shell

           python3 -m pip install -e .[SERV]
	   make installpns

To test your ``pns`` servers installation, in one window, run:

.. code-block:: shell

           make runserver

in another window run:

.. code-block:: shell

           make testpns

To test your ``httppool`` servers installation, in one window, run:

.. code-block:: shell

           make runpoolserver

in another window run:

.. code-block:: shell

           make testhttppool

For more examples see ``tests/test_*.py``

Read more on package introduction, description, quick start, and API
documents on `readthedocs.io <https://fdi.readthedocs.io/en/latest/>`__.

