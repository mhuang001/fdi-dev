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


