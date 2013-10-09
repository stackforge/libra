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

   .. option:: --gearman_keepalive

      Use TCP KEEPALIVE to the Gearman job server. Not supported on all
      systems.

   .. option:: --gearman_keepcnt <COUNT>

      Maximum number of TCP KEEPALIVE probes to send before killing the
      connection to the Gearman job server.

   .. option:: --gearman_keepidle <SECONDS>

      Seconds of idle time on the Gearman job server connection before
      sending TCP KEEPALIVE probes.

   .. option:: --gearman_keepintvl <SECONDS>

      Seconds between TCP KEEPALIVE probes.

   .. option:: --gearman_ssl_ca <FILE>

      Full path to the file with the CA public key to use when
      connecting to an SSL-enabled Gearman job server. This is used
      to validate the server key.

   .. option:: --gearman_ssl_cert <FILE>

      Full path to the file with the SSL public key to use when
      connecting to an SSL-enabled Gearman job server.

   .. option:: --gearman_ssl_key <FILE>

      Full path to the file with the SSL private key to use when
      connecting to an SSL-enabled Gearman job server.

   .. option:: --haproxy_logfile <FILE>

      Configure the path for where to put haproxy log.

      See :ref:`libra-worker-driver-haproxy` for notes on archiving

   .. option:: -s <SECONDS>, --reconnect_sleep <SECONDS>

      The number of seconds to sleep between job server reconnect attempts
      when no specified job servers are available. Default is 60 seconds.

   .. option:: --server <HOST:PORT>

      Used to specify the Gearman job server hostname and port. This option
      can be used multiple times to specify multiple job servers.

   .. option:: --stats-poll <SECONDS>

      The number of seconds to sleep between statistics polling of the
      load balancer driver. Default is 300 seconds.

   .. option:: --gearman-poll <SECONDS>

      The number of seconds gearman will poll before re-shuffling its
      connections. Default is 1 second.

   .. option:: --syslog

      Send log events to syslog.

   .. option:: --syslog-socket

      Socket to use for the syslog connection. Default is */dev/log*.

   .. option:: --syslog-facility

      Syslog logging facility. Default is *LOCAL7*.

