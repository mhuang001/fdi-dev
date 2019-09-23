============
Install SPDC
============


.. toctree::
   :maxdepth: 2
   :caption: Contents:

for developers
==============

.. code-block:: shell

		cd /tmp
		git clone ssh://git@mercury.bao.ac.cn:9005/mh/spdc.git
		cd spdc
		pip3 install -e .



.. code-block:: shell
		
		mkdir ~/svom
		cd ~/svom
		cp /tmp/spdc/install .
		nano install [do some editing if needed]
		. ./install

Install the dependencies if needed ((python 3.6, Flask, pytest ...)

for users
=========

.. code-block:: shell
		
		cd /tmp
		git clone http://mercury.bao.ac.cn:9006/mh/spdc.git
		cd spdc
		pip3 install -e .

to install in /tmp.
