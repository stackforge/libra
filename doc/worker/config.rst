Worker Configuration
====================

These options are specific to the worker in addition to the
:doc:`common options </config>`.

Configuration File
------------------

   The ``[worker]`` section is specific to the libra_worker utility. Below
   is an example:

   .. code-block:: ini

      [worker]
      driver = haproxy
      pid = /var/run/libra/libra_worker.pid

   The ``[worker:haproxy]`` section is read by the HAProxy driver.

   .. code-block:: ini

      [worker:haproxy]
      service = ubuntu
      logfile = /var/log/haproxy.log

Configuration Options
---------------------
   .. program:: libra_worker

   .. option:: driver <DRIVER>

      Load balancer driver to use. Valid driver options are:

      * *haproxy* - `HAProxy <http://haproxy.1wt.eu>`_ software load balancer.
        This is the default driver.

   .. option:: pid <FILE>

      Location for the process PID file.

Command Line Options
--------------------

   Some options can be specified via the command line. Run with the
   -h or --help option for a full listing.
