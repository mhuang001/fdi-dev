=========================================
**HTTPpool**: HTTP Pool Server and Client
=========================================

.. contents:: Table of Contents
	      :depth: 3




HTTP Pool server provides a RESTful web interface to create, remove, read, and delete data items (usually products) in a pool running on a server. A remote data user uses a HTTPClientPool as an interface.

For developing
==============

Configuration
-------------

Install fdi. Copy the config file over

.. code-block:: shell
		
		cp fdi/pns/config.py ~/.config/pnslocal.py

To customize ``~/.config/pnslocal.py`` modify these according to your system:

.. code-block::

   pnsconfig = dict(logginglevel=logging.DEBUG)
   pnsconfig['baseurl'] = '/v0.9'
   pnsconfig['base_poolpath'] = '/tmp'
   pnsconfig['server_poolpath'] = '/tmp/data'  # For server
   pnsconfig['defaultpool'] = 'default'
   pnsconfig['node'] = {'username': 'foo',
                        'password': 'bar', 'host': '127.0.0.1', 'port': 5000}
   pnsconfig['serveruser'] = 'mh'


Note that above are for both the server and te client in this and the next steps.



Run the Server
--------------

To use the defaults in the config, just

.. code-block:: shell

		make runpoolserver

The server can also be run by:

.. code-block:: shell

		python3 fdi/pns/runflaskserver.py --username=<username> --password=<password> [--ip=<host ip>] [--port=<port>] --server=httppool_server -v


Contents in ``[]``, like ``[--ip=<host ip>] [--port=<port>]`` above, are optional. ``<>`` means you need to substitute with actual information (for example ``--port=<port>`` becomes ``--port=5000``). The username and password are used when making run requests.


Now you can use a client to access it.

.. warning::

   Do not run debugging mode for production use. Password uses plain text for development.

.. note::

   The logging level of the server is set in the config file. The ``-v`` switch to ``runflaskserver`` used above will set the level to ``logging.DEBUG``. Packages ``requests, ``filelock``, and ``urllib3`` are fixed to ``logging.WARN``.


Test and Verify
---------------

To run all tests in one go
!!!!!!!!!!!!!!!!!!!!!!!!!!

.. code-block:: shell

		make testhttp

append ``T='-u <username> -p <password> [-i <host ip>] [-o <port>] [options]'`` if needed.

You can also test step-by-step to pin-point possible problems:

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

3. Standard functional pool test
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

.. code-block:: shell
		
		make test8

		

Learn/Try the APIs and Build the Server
=======================================

The APIs are documented in `fdi/httppool/schema/pools.yml` with OpenAPI 3. Run this to see and try out with Swagger API Docs when the server is running:

.. code-block:: shell

		http://127.0.0.1:5000/apidocs

To build the server, de-reference the YAML file (so Flasgger 0.95 can handle it):

.. code-block:: shell

		make de-ref
		
then run it ``make runpoolserver``

		
For production deployment
=========================

Manually
--------

Install fdi (see :doc:`installation`). Copy the config file over

.. code-block:: shell
		
		cp fdi/pns/config.py ~/.config/pnslocal.py

To customize ``~/.config/pnslocal.py`` modify these according to your system:

.. code-block::

   pnsconfig = dict(logginglevel=logging.DEBUG)
   pnsconfig['baseurl'] = '/v0.9'
   pnsconfig['base_poolpath'] = '/tmp'
   pnsconfig['server_poolpath'] = '/var/www/httppool_server/data'
   pnsconfig['defaultpool'] = 'default'
   pnsconfig['node'] = {'username': 'foo', 'password': 'XXX',
                         'host': '172.17.0.2', 'port': 9884}
   pnsconfig['serveruser'] = 'apache'

where at least the IP needs to be modified if to run a server.

Then refer to these files to install/update wsgi or conf files

*  ``fdi/pns/resources/httppool_server.docker``
*  ``fdi/pns/resources/httppool_server_entrypoint.sh``

   then enable the site and (re)start the server:

.. code-block:: shell

   sudo a2ensite httppool_server.conf
   sudo a2dissite 000-default.conf
   service apache2 --full-restart
  
.. note::
   
   The above are for both the server and the client when running pool functional test (``test6``) locally.


With Pre-made Docker Images
---------------------------


The following are for an ``apache2`` deployment as a ``VirtualHost`` based a Ubuntu docker.


Follow instructuin in :doc:`dockers` to pull or build the ``httppool`` server image. 
 
Launch it:

.. code-block:: shell

		make launch_server [PORT=xxxx]

Test and Verify Deployed Server
-------------------------------

The following is for a deployed docker.

Roughly following te sane steps in `Test and Verify`_ except for the firsrt step.

.. tip::
   
   Actually the first two steps can be skipped if the 3rd is successful.

1. Start
!!!!!!!!

Run a shell inside the server after launching it:

.. code-block:: shell

		make it
		
A ``/bin/bash`` will run and you will be at a shell prompt as the server user (``apache``). Type this to start the server process

.. code-block:: shell

		service apache2 --full-restart

After a few seconds check to make sure there are `apache` processes from

.. code-block:: shell

		ps augx

and you can get error message in JSON by

.. code-block:: shell

		curl -i http://localhost:9885

2. Test Functions in the Docker
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Now run the local tests:
  
* first fdi internal,
* then test6 for server local CRUD,
* test 7 client,
* test8 standard pool functional.


.. code-block:: shell

		cd fdi
		make test
		make test6
		make test7
		make test8

The last three can be run by ``make testhttp``.


3. Test from Outside the Docker
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

in the fdi directory where you built the docker image:

.. code-block:: shell

		make testhttp

Make sure that from where you run the test, your ``~/.config/pnslocal.py`` points to the correct ip and port.

.. tip::
   
   You can watch live logging from nother terminal with:

.. code-block:: shell

		make t

Clean up
--------

Stop and remove the docker by ``make rm_server``.

API Document
============



TBW
