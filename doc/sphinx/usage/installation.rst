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

Or if you have a tar file, e.g. /tmp/spdc.tar and /tmp/vvpp.tar, do something like


.. code-block:: shell
		
		mkdir ~/svom
		cd ~/svom
		nano install [do some editing if needed]
		./install

Install the dependencies if needed ((python 3.6, Flask, pytest ...)

for users
=========

.. code-block:: shell
		
		cd /tmp
		git clone http://mercury.bao.ac.cn:9006/mh/spdc.git
		cd spdc
		pip3 install -e .

to install in /tmp.
