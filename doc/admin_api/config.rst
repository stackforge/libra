Admin API Configuration
=======================

These options are specific to the Admin API in addition to the
:doc:`common options </config>`.

Configuration File
------------------

   The ``[admin_api]`` section is specific to the libra_admin_api utility.
   Below is an example:

   .. code-block:: ini

      [admin_api]
      db_section=mysql1
      ssl_certfile=/opt/server.crt
      ssl_keyfile=/opt/server.key
      gearman=127.0.0.1:4730

      [mysql1]
      host=localhost
      port=3306
      username=root
      password=
      schema=lbaas
      ssl_cert=/opt/mysql_cert.crt
      ssl_key=/opt/mysql_key.key
      ssl_ca=/opt/mysql_ca.ca

Command Line Options
--------------------
   .. program:: libra_admin_api

   .. option:: --host <IP ADDRESS>

      The IP address to bind the frontend to, default is 0.0.0.0

   .. option:: --port <PORT NUMBER>

      The port number to listen on, default is 8889

   .. option:: --db_sections <SECTIONNAME>

      Config file sections that describe the MySQL servers.  This option can
      be specified multiple times for Galera or NDB clusters.

   .. option:: --ssl_certfile <PATH>

      The path for the SSL certificate file to be used for frontend of the API
      server

   .. option:: --ssl_keyfile <PATH>

      The path for the SSL key file to be used for the frontend of the API
      server

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

   .. option:: --gearman_ssl_ca <PATH>

      The path for the Gearman SSL Certificate Authority.

   .. option:: --gearman_ssl_cert <PATH>

      The path for the Gearman SSL certificate.

   .. option:: --gearman_ssl_key <PATH>

      The path for the Gearman SSL key.

   .. option:: --gearman <HOST:PORT>

      Used to specify the Gearman job server hostname and port. This option
      can be used multiple times to specify multiple job servers

   .. option:: --stats_driver <DRIVER LIST>

      The drivers to be used for alerting.  This option can be used multiple
      times to specift multiple drivers.

   .. option:: --stats_ping_timeout <PING_INTERVAL>

      How often to run a ping check of load balancers (in seconds), default 60

   .. option:: --stats_poll_timer <POLL_INTERVAL>

      How long to wait until we consider the initial ping check failed and
      send a second ping. Default is 5 seconds.

   .. option:: --stats_poll_timeout_retry <POLL_INTERVAL>

      How long to wait until we consider the second and final ping check
      failed. Default is 30 seconds.

   .. option:: --number_of_servers <NUMBER_OF_SERVER>

      The number of Admin API servers in the system.
      Used to calculate which Admin API server should stats ping next

   .. option:: --server_id <SERVER_ID>

      The server ID of this server,  used to calculate which Admin API
      server should stats ping next (start at 0)

   .. option:: --datadog_api_key <KEY>

      The API key to be used for the datadog driver

   .. option:: --datadog_app_key <KEY>

      The Application key to be used for the datadog driver

   .. option:: --datadog_message_tail <TEXT>

      Some text to add at the end of an alerting message such as a list of
      users to alert (using @user@email.com format), used for the datadog
      driver.

   .. option:: --datadog_tags <TAGS>

      A list of tags to be used for the datadog driver

   .. option:: --node_pool_size <SIZE>

      The number of hot spare load balancer devices to keep in the pool,
      default 10

   .. option:: --vip_pool_size <SIZE>

      The number of hot spare floating IPs to keep in the pool, default 10

   .. option:: --expire_days <DAYS>

      The number of days before DELETED load balancers are purged from the
      database.  The purge is run every 24 hours.  Purge is not run if no
      value is provided.
