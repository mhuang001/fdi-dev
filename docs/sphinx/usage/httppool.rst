=========================================
**HTTPpool**: HTTP Pool Server and Client
=========================================

.. contents:: Table of Contents
	      :depth: 3



Architecture
============

HTTP Pool server provides a RESTful web interface to create, remove, read, and delete data items (usually products) in a pool running on a server. A remote data user uses a HTTPClientPool as an interface.

For developement
================

Configuration
-------------

Install fdi. Copy the config file over

.. code-block:: shell
		
		cp fdi/pns/config.py ~/.config/pnslocal.py

To customize ``~/.config/pnslocal.py`` modify these according to your system:

.. code-block::

   pnsconfig = dict(logginglevel=logging.DEBUG)
   pnsconfig['baseurl'] = '/v0.6'
   pnsconfig['base_poolpath'] = '/tmp'
   pnsconfig['server_poolpath'] = '/var/www/data'  # For server
   pnsconfig['defaultpool'] = 'pool_default'
   pnsconfig['node'] = {'username': 'foo',
                        'password': 'bar', 'host': '127.0.0.1', 'port': 5000}
   pnsconfig['serveruser'] = 'mh'


Note that above are for both the server and te client in this and the next steps.

Run the Server
--------------

The server can be run by

.. code-block:: shell

		python3 fdi/pns/runflaskserver.py --username=<username> --password=<password> [--ip=<host ip>] [--port=<port>] --server=httppool_server -v


Contents in ``[]``, like ``[--ip=<host ip>] [--port=<port>]`` above, are optional. ``<>`` means you need to substitute with actual information (for example ``--port=<port>`` becomes ``--port=5000``). The username and password are used when making run requests.


To use the defaults in the config, just

.. code-block:: shell

		make runpoolserver

Now you can use a client to access it.

.. warning::

   Do not run debugging mode for production use.

.. note::

   The logging level of the server is set in the config file. The ``-v`` switch to ``runflaskserver`` used above will set the level to ``logging.DEBUG``. Packages ``requests, ``filelock``, and ``urllib3`` are fixed to ``logging.WARN``.


Test and Verify
---------------

To run all tests in one go:

.. code-block:: shell

		make testhttp

append ``T='-u <username> -p <password> [-i <host ip>] [-o <port>] [options]'`` if needed.

Tests can be done step-by-step to pin-point possible problems:

1. Server Unit Test
!!!!!!!!!!!!!!!!!!!

Run this on the server host to verify that internal essential functions of the server work with current configuration.

.. code-block:: shell
		
		make test6


2. Local Server Functional Tests
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

test HTTP Client APIs

.. code-block:: shell
		
		make test7

Standard functional pool test

.. code-block:: shell
		
		make test8

		

For production deployment
=========================


These are for an ``apache2`` deployment as a ``VirtualHost`` in a Ubuntu docker:


Configuration
-------------

Install fdi. Copy the config file over

.. code-block:: shell
		
		cp fdi/pns/config.py ~/.config/pnslocal.py

To customize ``~/.config/pnslocal.py`` modify these according to your system:

.. code-block::

   pnsconfig = dict(logginglevel=logging.DEBUG)
   pnsconfig['baseurl'] = '/v0.6'
   pnsconfig['base_poolpath'] = '/tmp'
   pnsconfig['server_poolpath'] = '/var/www/httppool_server/data'
   pnsconfig['defaultpool'] = 'pool_default'
   pnsconfig['node'] = {'username': 'foo', 'password': 'bar',
                         'host': '217.17.0.9', 'port': 9884}
   pnsconfig['serveruser'] = 'apache'

where the IP is obtainable by ``fdi/pns/resources/httppool_server_entrypoint.sh``.

Note that above are for both the server and te client in this and the next steps.

Run the Server
--------------

The following shows how to build a HTTP Pool docker image.

First make a virtual environment:

.. code-block:: shell

		virtualenv -p python3.6 poolserver
		cd poolserver
		. bin/activate

Then install fdi following instructions in :doc:`installation` , e.g.

.. code-block:: shell

           git clone http://mercury.bao.ac.cn:9006/mh/fdi.git
           cd fdi
	   git checkout develop
	   make install I="[DEV,SERV]"

Now you can make the server docker easily:

.. code-block:: shell

		make build_server

Test and Verify
---------------

After building a server, launch it:

.. code-block:: shell

		make launch_server


1. Start
!!!!!!!!

The Docker will run and you will be at a shell prompt as the server user (``apache``). Type this to start the server process

.. code-block:: shell

		service apache2 --full-restart

After a few seconds check to make sure there are `apache` processes from

.. code-block:: shell

		ps augx

and you can get error message in JSON by

.. code-block:: shell

		curl -i http://localhost:9884

2. Test ine the Docker
!!!!!!!!!!!!!!!!!!!!!!

Now run the local tests::
  first fdi internal,
  then test6 for server local CRUD,
  test 7 client,
  test8 standard pool functional.


.. code-block:: shell

		cd fdi
		make test
		make test6
		make test7
		make test8

The last three can be run by ``make testhttp``.

You can watch the logging action by starting a new shell in the docker by running this in the fdi directory where you built the docker image:

.. code-block:: shell

		make it

run ``make it D='-u 0'`` to become the root. When you are in the docker, run ``tail -f error-ps.log`` while ``make testhttp`` runs.

3. Test from Outside
!!!!!!!!!!!!!!!!!!!!

in the fdi directory where you built the docker image:

.. code-block:: shell

		make testhttp

Clean up
--------

Stop and remove the docker by ``make rm_server``.

Resources
=========

TBW
