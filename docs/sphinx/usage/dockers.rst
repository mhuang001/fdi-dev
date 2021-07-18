=======
Dockers
=======

.. role:: rh(raw)
	  :format: html

.. tabularcolumns:: |p{5em}|p{6em}|p{5em}|p{6em}|p{6em}|p{6em}|p{6em}|p{6em}|p{5em}|

The following dockers are available:

+--------+-----------------+--------+------------------------+-----------------------+------------------+--------------+---------------+---------+
|**Name**|**Description**  |**Base**|**Installed**           |**In-docker User**     |**Pull**          | **Build**    |**Launch**     |**Ports**|
+--------+-----------------+--------+------------------------+-----------------------+------------------+--------------+---------------+---------+
|fdi     |linux with fdi   |Ubuntu  |Package and DEV, SERV   |``fdi``                |``docker pull     |``make        |``make         |\--      |
|        |tested :rh:`<br  |:rh:`<br|:rh:`<br />`            |                       |mhastro/fdi``     |build_docker``|launch_docker``|         |
|        |/>` and ready to |/>`     |dependencies.           |                       |                  |              |               |         |
|        |run.             |18.04   |                        |                       |                  |              |               |         |
+--------+-----------------+--------+------------------------+-----------------------+------------------+--------------+---------------+---------+
|httppool|Apache HTTPPool  |fdi     |Package and DEV, SERV   |``apache`` :rh:`<br />`|``docker pull     |``make        |``make         |9884     |
|        |server, :rh:`<br |        |:rh:`<br />`            |(Convenience links     |mhastro/httppool``|build_server``|launch_server``|         |
|        |/>` tested and   |        |dependencies.           |:rh:`<br />` in home   |                  |              |               |         |
|        |started.         |        |                        |dir.)                  |                  |              |               |         |
|        |                 |        |                        |                       |                  |              |               |         |
+--------+-----------------+--------+------------------------+-----------------------+------------------+--------------+---------------+---------+


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

