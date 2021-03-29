
Flexible Dataset Integrator (FDI) helps data producers and processors to build connections into isolated heterogeneous datasets. to assemble, organize, and integrate data into self-describing, modular, hierarchical, persistent, referenceable ``Products``, whose component datasets keep their own characteristicss and are easily accessible.

FDI provides scripting-friendly  APIs  and 
tools to define custom Products and generating Python class files. An integrated Product takes care of inter-platform compatibility, string representation, serialisation to simple exchange format, persistence to disk or server, and carrying references of other Products, enabling context-building and lazy-loading.

FDI's base data model is defined in sub-package ``dataset``. Persistent data
access using storage pools, referencing, and Universal Resource Names, and referencie-carrying product Context, are defined in sub-package ``pal``. A reference RESTful API server designed to communicate with a data processing server/docker using the data model, and a reference HTTP pool server are in sub-package ``pns``.

Install/Uninstall
-----------------
.. image:: pipeline.svg
   :target: http://mercury.bao.ac.cn:9006/mh/fdi/badges/master/index.html

<a href="http://mercury.bao.ac.cn:9006/mh/fdi/-/commits/master"><img alt="pipeline status" src="http://mercury.bao.ac.cn:9006/mh/fdi/badges/master/pipeline.svg" /></a>

.. tip::

   It is a good idea to add ``--user`` at the end or to use a virtualenv to avoid disturbing your system Python setup.

For Users
=========

If you need to use fdi, install from PyPI:

.. code-block:: shell

   python3 -m pip install fdi

or from git repo:

.. code-block:: shell

   python3 -m pip install http://mercury.bao.ac.cn:9006/mh/fdi/-/archive/master/fdi-master.tar.gz

If you want to install the ``develop`` and server dependencies:

.. code-block:: shell

   python3 -m pip install fdi[DEV,SERV]
   
or

.. code-block:: shell

   python3 -m pip install http://mercury.bao.ac.cn:9006/mh/fdi/-/archive/develop/fdi-develop.tar.gz#egg=fdi[DEV,SERV]
   
To uninstall:

.. code-block:: shell

           python3 -m pip uninstall fdi


For Developers and Admins (or Those who are Not Sure which to Choose)
=====================================================================

To install
----------

.. code-block:: shell

           FDIINSTDIR=/tmp   # change this to your installation dir
           cd $FDIINSTDIR
           git clone ssh://git@mercury.bao.ac.cn:9005/mh/fdi.git
           cd fdi
	   git checkout develop
	   make install I="[DEV,SERV]"
	   
If you want to install the ``master`` branch, remove the ``git checkout develop`` line above.
	   
To test your installation
-------------------------

.. code-block:: shell

           make test

.. tip::

   To pass command-line arguments to ``pytest`` do, for example,
   
   .. code-block:: shell
		   
		make test T='-k Bas'

   to test ``BaseProduct``.


To Generate Python Product Source Code
--------------------------------------

Re-generate ``baseproduct.py`` and ``product.py`` from YAML schema files in
``fdi/dataset/resources``:

.. code-block:: shell

           make py


Modify/Generate Documents
-------------------------

If you plan to compile documents in the ``docs`` directory, generate diagrams, API files, or HTML pages, run (in that order, respectively):

.. code-block:: shell

           make docs_plots
           make docs_api
           make docs_html

The generated HTML page is at ``docs/html/index.html``.

.. note:: https://readthedocs.io makes web pages from sources in ``docs/sphinx`` in the repository. Locally generated HTML pages are not on RTD or in the repository. The API files and plots, however, are in ``api`` and ``_static`` sub-directpries, respectively.
	   
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

For More
--------

For more  examples see ``tests/test_*.py``.

Read more on package introduction, description, quick start, and API
documents on `readthedocs.io <https://fdi.readthedocs.io/en/latest/>`__.

