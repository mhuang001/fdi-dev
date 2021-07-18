=======
Dockers
=======

.. role:: rh(raw)
	  :format: html

.. tabularcolumns:: |p{20em}|p{40em}|p{40em}|

The following dockers are available:

+-------------------+------------------------------+-----------------------------------------------------+
|**Name**           |fdi                           |httppool                                             |
+-------------------+------------------------------+-----------------------------------------------------+
|**Description**    |linux with fdi tested and     |Apache HTTPPool server, tested                       |
|                   |ready to run.                 |and started.                                         |
|                   |                              |                                                     |
+-------------------+------------------------------+-----------------------------------------------------+
|**Base**           |Ubuntu 18.04                  |fdi                                                  |
+-------------------+------------------------------+-----------------------------------------------------+
|**Installed**      |Package and DEV, SERV         |Package and DEV, SERV                                |
|                   |dependencies.                 |dependencies.                                        |
+-------------------+------------------------------+-----------------------------------------------------+
|**In-docker User** |``fdi``                       |``apache``(Convenience links in                      |
|                   |                              |home dir.)                                           |
+-------------------+------------------------------+-----------------------------------------------------+
|**Pull**           |``docker pull mhastro/fdi``   |``docker pull mhastro/httppool``                     |
|                   |                              |                                                     |
+-------------------+------------------------------+-----------------------------------------------------+
|**Build**          |``make build_docker``         |``make build_server``                                |
|                   |                              |                                                     |
+-------------------+------------------------------+-----------------------------------------------------+
|**Launch**         |``make launch_docker``        |``make launch_server``                               |
|                   |                              |                                                     |
+-------------------+------------------------------+-----------------------------------------------------+
|**Entrypoint**     | ``dockerfile_entrypoint.sh`` |``fdi/pns/resources/httppool_server_entrypoint_2.sh``|
+-------------------+------------------------------+-----------------------------------------------------+
|**Ports**          |\--                           |9884                                                 |
+-------------------+------------------------------+-----------------------------------------------------+

Run the ``make`` commands in the package root directory of fdi. A file named ``.secret`` is needed by the build and launch commands. This is an example::

  HOST_PORT=9884
  HOST_USER=...
  HOST_PASS=...
  MQ_HOST=123.45.67.89
  MQ_PORT=9876
  MQ_USER=...
  MQ_PASS=...

Server credentials are set during start up, when ``pnslocal.py`` config file is loaded.

More convenience commands:

Login the latest built running container:

.. code-block:: shell

	make it

Stop the latest built running container:

.. code-block:: shell

	make rm_docker

Remove the latest built running container and image:

.. code-block:: shell

	make rm_dockeri

