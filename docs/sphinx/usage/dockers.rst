=======
Dockers
=======

.. role:: rh(raw)
	  :format: html

.. contents:: Table of Contents
	      :depth: 3


Specifications
==============
		   
.. tabularcolumns:: |p{15em}|p{40em}|p{40em}|

The following pre-made docker images are available:

+-------------------+-----------------------------+-----------------------------------------------------+
|     **Name**      |fdi                          |httppool                                             |
+-------------------+-----------------------------+-----------------------------------------------------+
|  **Description**  |linux with fdi tested and    |Apache HTTPPool server, tested                       |
|                   |ready to run.                |and started.                                         |
|                   |                             |                                                     |
+-------------------+-----------------------------+-----------------------------------------------------+
|     **Base**      |Ubuntu 18.04 (~268MB         |fdi (~271MB compressed)                              |
|                   |compressed)                  |                                                     |
+-------------------+-----------------------------+-----------------------------------------------------+
|   **Installed**   |Package and DEV, SERV        |Package and DEV, SERV                                |
|                   |dependencies.                |dependencies.                                        |
+-------------------+-----------------------------+-----------------------------------------------------+
|**User in docker** |``fdi``                      |``apache``(Convenience links in                      |
|                   |                             |home dir.)                                           |
+-------------------+-----------------------------+-----------------------------------------------------+
|     **Pull**      |``docker pull mhastro/fdi``  |``docker pull mhastro/httppool``                     |
|                   |                             |                                                     |
+-------------------+-----------------------------+-----------------------------------------------------+
|     **Build**     |``make build_docker``        |``make build_server``                                |
|                   |                             |                                                     |
+-------------------+-----------------------------+-----------------------------------------------------+
|    **Launch**     |``make launch_docker``       |``make launch_server``                               |
|                   |                             |                                                     |
+-------------------+-----------------------------+-----------------------------------------------------+
|  **Entrypoint**   |``dockerfile_entrypoint.sh`` |``fdi/pns/resources/httppool_server_entrypoint_2.sh``|
+-------------------+-----------------------------+-----------------------------------------------------+
|     **Ports**     |\--                          |9884                                                 |
+-------------------+-----------------------------+-----------------------------------------------------+

Run the ``make`` commands in the package root directory of fdi.

Configure
=========

A file named ``.secret`` is needed by the build and launch commands. This is an example ``.secret``::

  HOST_PORT=9884
  HOST_USER=...
  HOST_PASS=...
  MQ_HOST=123.45.67.89
  MQ_PORT=9876
  MQ_USER=...
  MQ_PASS=...

Server credentials are set during server start up, when ``pnslocal.py`` config file is loaded. ``pnslocal.py`` and other configuration files are updated by the Entrypoint files (see the table above) when the docker starts. The Entrypoint files uses environment variables, which are set by the command line with ``--env-file`` so that sensitive information are not left on the command line.

More convenience commands
=========================

Login the latest built running container:

.. code-block:: shell

	make it

Stop the latest built running container:

.. code-block:: shell

	make rm_docker

Remove the latest built running container and image:

.. code-block:: shell

	make rm_dockeri

Watch ``/var/log/apache2/error-ps.log`` inside the ``httppool`` docker updating (after launching):

.. code-block:: shell

	make t

.. tip::
   
   If you see error of log file not found, you are running the ``fdi`` docker by mistake. Only the pool server docker has the log.
   
Make the images locally
=======================

The following shows how to build the docker images yourself.

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
	   make install EXT="[DEV,SERV]"

Modify ``docker_entrypoint.sh`` if needed.

Now you can make the ``fdi`` docker easily:

.. code-block:: shell

		make build_docker

To build ``httppool`` image, modify the ``FROM`` line in ``fdi/pns/resources/httppool_server_2.docker`` to delete ``mhastro/``.

Modify ``fdi/pns/resources/httppool_server_entrypoint.sh`` if needed.

Make the ``httppool`` image

.. code-block:: shell

		make build_server

