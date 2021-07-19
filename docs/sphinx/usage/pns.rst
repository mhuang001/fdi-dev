===========================================
**PNS**: Processing Node Server
===========================================


.. contents:: Table of Contents
	      :depth: 3

Rationale
=========

Many data processing pipelines need to run software that only runs on a specific combination of OS type, version, language, and library. These software could be impractical to replace or modify but need to be run side-by-side with software of incompatible environments/formats to form an integral data processing pipeline, each software being a "node" to perform a  processing task. Docker containers are often the perfect solution to run software with incompatible dependencies.

PNS installed on a Docker container or a normal server allows such processing tasks to run in the PNS memory space, in a daemon process, or as an OS process receiving input and delivering output through a 'delivery man' protocol.

This Web API Server for a data processing pipeline/network node provides interfaces to configure the data processing task software (PTS) in a processing node, to make a run request, to deliver necessary input data, and to read results, all via web APIs.

The following commands are run from the fdi directory from installation.

Basic Configuration
===================

When running Flask server, the host IP is ``127.0.0.1`` and port number ``5000`` by default. They are configurable in ``pnsconfig.py``. Default configuration can be overridden by ``~/.config/pnslocal.py``. Copy ``pnsconfig.py`` to ``~/.config/pnslocal.py``

.. code-block:: shell
		
		cp fdi/pns/config.py ~/.config/pnslocal.py

and customize ``~/.config/pnslocal.py``.

When in developement mode, select ``dev`` to run local server. The ``serveruser`` should be the name of the user of web server, usually your username if you run ``make runserver``. This is the default if ``dev`` is selected.

For production deployment choose ``servertest`` or ``external``. Set ``serveruser`` depending which web server (e.g. ``'apache'``).

The ``ptsuser`` is usually the user required by the processing software. It is set to ``serveruser`` by default. ``ptsuser`` must have write previlige to read and write ``inputdir`` and ``outputdir``, which are owned by ``serveruser`` with mode ``o0775``.

On the server side (or on your computer which can be both the server and the client) edit ``Makefile`` by changing the value of varible ``PNSDIR`` in ``Makefile`` the pnshome directory if you do not want the default (``~/pns``).

Then run the deployment command

.. code-block:: shell

		make installpns

to create the pns home directory and copy the demo PTS script set.

Run the FLASK Server
====================

Edit ``~/.config/pnslocal.py`` if needed. Then

.. code-block:: shell

		python3 fdi/pns/runflaskserver.py --username=<username> --password=<password> [--ip=<host ip>] [--port=<port>]

Contents in ``[]``, like ``[--ip=<host ip>] [--port=<port>]`` above, are optional.

``<>`` means you need to substitute with actual information (for example ``--port=<port>`` becomes ``--port=5000``).

Or you can run

.. code-block:: shell

		python3 fdi/pns/runflaskserver.py -u <username> -p <password> [-i <host ip>] [-o <port>]

in debugging mode:

.. code-block:: shell

		python3 fdi/pns/runflaskserver.py --username=foo --password=bar -v

or just

.. code-block:: shell

		make runserver

to use the defaults. 

Do not run debugging mode for production use.

The username and password are used when making run requests.

.. note::

   The logging level of the server is set in the config file. The ``-v`` switch to ``runflaskserver`` used above will set the level to ``logging.DEBUG``. Packages ``requests, ``filelock``, and ``urllib3`` are fixed to ``logging.WARN``.


Test and Verify Installation
============================


To run all tests in one go:

.. code-block:: shell

		make test3 [T='-u <username> -p <password> [-i <host ip>] [-o <port>] [options]']

Tests can be done step-by-step to pin-point possible problems:

1. Server Unit Test
===================

Run this on the server host to verify that internal essential functions of the server work with current configuration. This runs without needing starting the server:

.. code-block:: shell

		make test4

2. Local Flask Server Functional Tests
======================================

In ``~/.config/pnslocal.py`` (see above for installation and customization), set ``dev=True`` and make sure the IP is local (``127.0.0.1``). Start the server fresh in one terminal (see above) and in another terminal (on the server host) run the following:

2a: test GET initPTS script to see if reading the init script back works:

.. code-block:: shell
		
		make test3 T='getinit'

2b: test PUT initialization test:

.. code-block:: shell

		make test3 T='-k putinittest'

2c1: If the test passes, you can Run all tests in one go:

.. code-block:: shell
		
		make test3

2c2: Or keep on individual tests...


test POST In-server processing

.. code-block:: shell
		
		make test3 T='-k _post'

test POST PTS processing

.. code-block:: shell
		
		make test3 T='-k _run'

test DELETE Clean-up the server by removing the input and output dirs

.. code-block:: shell
		
		make test3 T='-k deleteclean'

Now is a good time to ...

3. Get public access APIs and information
=========================================

Suppose the server address and port are ``127.0.0.1`` and ``5000``, respectively:

Run the Flask server in a terminal (see above) and open this in a browser. The up-to-date URL is displayed in the server stating message:

http://127.0.0.1:5000/v0.6/

An online API documentation page similar to below is shown.

.. code-block:: json

		{
		"APIs": {
		"DELETE": [
		{
		"URL": "http://127.0.0.1:5000/v0.6/clean", 
		"description": " Removing traces of past runnings the Processing Task Software.\n    "
		}
		], 
		"GET": [
		{
		"URL": "http://127.0.0.1:5000/v0.6/init", 
		"description": "the initPTS file"
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/config", 
		"description": "the configPTS file"
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/run", 
		"description": "the file running PTS"
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/clean", 
		"description": "the cleanPTS file"
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/input", 
		"description": " returns names and contents of all files in the dir, 'None' if dir not existing. "
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/output", 
		"description": " returns names and contents of all files in the dir, 'None' if dir not existing. "
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/pnsconfig", 
		"description": "PNS configuration"
		}
		], 
		"POST": [
		{
		"URL": "http://127.0.0.1:5000/v0.6/calc", 
		"description": " generates result product directly using data on PNS.\n    "
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/testcalc", 
		"description": " generate post test product.\n    put the 1st input (see maketestdata in test_all.py)\n    parameter to metadata\n    and 2nd to the product's dataset\n    "
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/echo", 
		"description": "Echo"
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/run", 
		"description": " Generates a product by running script defined in the config under 'run'. Execution on the server host is in the pnshome directory and run result and status are returned.\n    "
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/testrun", 
		"description": "  Run 'runPTS' for testing, and as an example.\n    "
		}
		], 
		"PUT": [
		{
		"URL": "http://127.0.0.1:5000/v0.6/init", 
		"description": " Initialize the Processing Task Software by running the init script defined in the config. Execution on the server host is in the pnshome directory and run result and status are returned. If input/output directories cannot be created with serveruser as owner, Error401 will be given.\n    "
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/config", 
		"description": " Configure the Processing Task Software by running the config script. Ref init PTS.\n    "
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/pnsconf", 
		"description": " Configure the PNS itself by replacing the pnsconfig var\n    "
		}, 
		{
		"URL": "http://127.0.0.1:5000/v0.6/inittest", 
		"description": "     Renames the 'init' 'config' 'run' 'clean' scripts to \"*.save\" and points it to the '.ori' scripts.\n    "
		}
		]
		}, 
		"timestamp": 1566130779.0208821
		}

Continue with tests...
	
4. Run tests from a remote client
=================================

Install pns on a remote host, configure IP and port, then run the tests above. This proves that the server and the client have connection and fire wall configured correctly.


Run the local tests with Apache
===============================

Set dev=False in ~/.config/pnslocal.py (see above) and set the IP and port.
Suppose the server is on CentOS. Edit pns/resources/pns.conf according to local setup, then


.. code-block:: shell
		
		cp pns/resources/pns.conf /etc/httpd/conf.d 
		systemctl restart httpd
		systemctl status http -l

then run the above with correct IP and port (edit ~/.config/pnslocal.py or specifying in command line). Start the server and run all the tests:

.. code-block::
   
   make test3


PTS Configuration
=================

To run a PTS shell script instead of the 'hello' demo, change the ```run``` parameter in the config file, e.g. to run the script named ``runPTS.vvpp``

.. code-block::
   
   run=[join(h, 'runPTS.vvpp'), ''],

restart the server. run

.. code-block::
   
   make test4

PTS API
=======
TBW

Return on Common Errors
=======================

400

.. code-block::
   
   {'error': 'Bad request.', 'timestamp': ts}

401

.. code-block::
   
   {'error': 'Unauthorized. Authentication needed to modify.', 'timestamp': ts}

404

.. code-block::
   
   {'error': 'Not found.', 'timestamp': ts}

409

.. code-block::
   
   {'error': 'Conflict. Updating.', 'timestamp': ts}



Resources
---------

TBW
