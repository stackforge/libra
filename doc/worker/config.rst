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
      reconnect_sleep = 60
      server = 10.0.0.1:8080 10.0.0.2:8080

Command Line Options
--------------------
   .. program:: libra_worker

   .. option:: --driver <DRIVER>

      Load balancer driver to use. Valid driver options are:

      * *haproxy* - `HAProxy <http://haproxy.1wt.eu>`_ software load balancer.
        This is the default driver.

   .. option:: -s <SECONDS>, --reconnect_sleep <SECONDS>

      The number of seconds to sleep between job server reconnect attempts
      when no specified job servers are available. Default is 60 seconds.

   .. option:: --server <HOST:PORT>

      Used to specify the Gearman job server hostname and port. This option
      can be used multiple times to specify multiple job servers.

   .. option:: --syslog

      Send log events to syslog.

   .. option:: --syslog-socket

      Socket to use for the syslog connection. Default is */dev/log*.

   .. option:: --syslog-facility

      Syslog logging facility. Default is *LOCAL7*.

   .. option:: --stats-poll <SECONDS>

      The number of seconds to sleep between statistics polling of the
      load balancer driver. Default is 300 seconds.

