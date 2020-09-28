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
		
		cd /tmp
		git clone http://mercury.bao.ac.cn:9006/mh/fdi.git
		cd fdi
		pip3 install -e .

to install in /tmp.
