Dockers
=======

.. tabularcolumns:: |p{5em}|p{6em}|p{5em}|p{6em}|p{6em}|p{6em}|p{6em}|p{6em}|p{5em}|

The following dockers are available:


+--------+-----------------+--------+----------------+---------------+------------------+--------------+---------------+---------+
|**Name**|**Description**  |**Base**|**Installed**   |**User**       |**Pull**          | **Build**    |**Launch**     |**Ports**|
+--------+-----------------+--------+----------------+---------------+------------------+--------------+---------------+---------+
|fdi     |linux with fdi   |Ubuntu  |Package and DEV,|``fdi``        |``docker pull     |``make        |``make         |-        |
|        |tested and ready |18.04   |SERV            |               |mhastro/fdi``     |build_docker``|launch_docker``|         |
|        |to run.          |        |dependencies.   |               |                  |              |               |         |
+--------+-----------------+--------+----------------+---------------+------------------+--------------+---------------+---------+
|httppool|Apache HTTPPool  |Ubuntu  |Package and DEV,|``apache``     |``docker pull     |``make        |``make         |9884     |
|        |server, tested   |18.04   |SERV            |(Convenience   |mhastro/httppool``|build_server``|launch_server``|         |
|        |and started.     |        |dependencies.   |links in home  |                  |              |               |         |
|        |                 |        |                |dir.)          |                  |              |               |         |
+--------+-----------------+--------+----------------+---------------+------------------+--------------+---------------+---------+

Login the latest built running container:

.. code-block:: shell

	make it

Stop the latest built running container:

.. code-block:: shell

	make rm_docker

Remove the latest built running container and image:

.. code-block:: shell

	make rm_dockeri

