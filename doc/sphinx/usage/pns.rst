===========================================
pns: Processing Network Node Web API Server
===========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Thhis Web API Server for a data processing pipeline/network node provides interfaces to make a run request to and read results from a processing task in a processing node via web APIs.

The following commands are run from the spdc directory from installation.

Basic Configuration
===================

When running Flask server, the host IP is 0.0.0.0 and port number 5000 by default. They are configurable in pnsconfig.py. Default configuration can be overrided by ~/local.py. Copy pnsconfig.py to ~/local.py

.. code-block:: shell
		
		cp pns/pnsconfig.py ~/local.py

and edit to make local changes. Especially set dev to True to run local server.

On the server side (or on your computer which can be both the server and the client) edit the pnshome directory $PDIR if needed and run the deployment script

.. code-block:: shell

		pns/installpns
		
Run the FLASK Server
================

Edit local.py if needed. Then

.. code-block:: shell

		python3.6 pns/runflaskserver.py --username=<username> --password=<password> [--ip=<host ip>] [--port=<port>]

or

.. code-block:: shell

		python3.6 pns/runflaskserver.py -u <username> -p <password> [-i <host ip>] [-o <port>]

in debugging mode:

.. code-block:: shell

		python3.6 pns/runflaskserver.py --username=foo --password=bar -v

or just

.. code-block:: shell

		./startserver

to use the defaults.

Do not run debugging mode for production use.

The username and password are used when making run requests.

Test and Verify Installation
============================


To run all tests in one go:

.. code-block:: shell

		./test 3 [-u <username> -p <password> [-i <host ip>] [-o <port>]] [options]

Tests can be done step-by-step to help pin-point problems:

1. Server Unit Test, run on the server host. without needing starting the server:

.. code-block:: shell

		./test 4

2. Local Flask Server Functional Tests

In ~/local.py (in pns/pnsconfig.py if you have not made local.py), set dev=True and make sure the IP is local (0.0.0.0 or 127.0.0.1). Start the server fresh in one terminal (see above) and in another terminal (on the server host) run the following:

test GET initPTS script to see if reading the init script back works:

.. code-block:: shell
		
		./test 3 getinit

test PUT initialization test:

.. code-block:: shell

		./test 3 -k putinittest

If the test passes, you can Run all tests in one go:

.. code-block:: shell
		
		./test 3

Or keep on individual tests...


test POST In-server processing

.. code-block:: shell
		
		./test 3 -k _post

test POST PTS processing

.. code-block:: shell
		
		./test 3 -k _run

test DELETE Clean-up the server by removing the input and output dirs

.. code-block:: shell
		
		./test 3 -k deleteclean

Now is a good time to ...

Get public access APIs and information
======================================

Suppose the server address and port are 127.0.0.1 and 5000, respectively:

Run the Flask server in a terminal (see above) and open this in a browser:

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

Contonue with tests...
		
Run tests from a remote client
==============================

Install pns on a remote host, configure IP and port, then run the tests above. This proves that the server and the client have connection and fire wall configured correctly.


Run the local tests with Apache
===============================

Set dev=False in ~/local.py (see above) and set the IP and port.
Suppose the server is on CentOS. Edit pns/resources/pns.conf according to local setup, then


.. code-block:: shell
		
		cp pns/resources/pns.conf /etc/httpd/conf.d 
		systemctl restart httpd
		systemctl status http -l

then run the above with correct IP and port (edit ~/local.py or specifying in command line).

PTS Configuration
=================

To run a PTS shell script instead of the 'hello' demo, change the ```run``` parameter in the config file


PTS API
=======


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
