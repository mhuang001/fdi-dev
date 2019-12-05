============
Install SPDC
============


.. toctree::
   :maxdepth: 2
   :caption: Contents:

for developers
==============

.. code-block:: shell

		SPDCINSTDIR=/tmp   # change this to your installation dir
		cd $SPDCINSTDIR
		git clone ssh://git@mercury.bao.ac.cn:9005/mh/spdc.git
		cd spdc
		pip3 install -r requirements.txt
		pip3 install -e .


.. code-block:: shell
		
		mkdir ~/svom
		cd ~/svom
		cp $SPDCINSTDIR/spdc/install .
		nano install [do some editing if needed]
		. ./install


for users
=========

.. code-block:: shell
		
		cd /tmp
		git clone http://mercury.bao.ac.cn:9006/mh/spdc.git
		cd spdc
		pip3 install -e .

to install in /tmp.
