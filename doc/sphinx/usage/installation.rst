============
Install FDI
============


.. toctree::
   :maxdepth: 2
   :caption: Contents:

for developers
==============

.. code-block:: shell

		FDIINSTDIR=/tmp   # change this to your installation dir
		cd $FDIINSTDIR
		git clone ssh://git@mercury.bao.ac.cn:9005/mh/fdi.git
		cd fdi
		pip3 install -e .

for users
=========



.. code-block:: shell
		
		pip3 install git+http://mercury.bao.ac.cn:9006/mh/fdi.git


If you plan to compile documentations (using Sphinx), you need to run install with extra dependencies:

.. code-block:: shell
		
		make install_with_DOC


To uninstall:

.. code-block:: shell
		
		make uninstall


To generate ``baseproduct.py`` and ``product.py`` from schema in ``fdi/dataset/resources``:

.. code-block:: shell
		
		make py

run tests
=========

In the install directory:

.. code-block:: shell

		make test1
		make test2
		make test3

You can only test sub-package ``dataset``, ``pal``, and *pns server self-test only*, with ``test1``, ``test2``, ``test3``, respectively.

To run full test, run this in one window in the install dir:

.. code-block:: shell

		make installpns
		make runserver

(if the server fails to run, see the ``pns`` chapter), then in another window, run

.. code-block:: shell

		make test


.. tip::

   To pass command-line arguments to ``pytest`` do, for example,
   
   .. code-block:: shell
		   
		make test T='-k Bas'

   to test ``BaseProduct`` in sub-package ``dataset``.


