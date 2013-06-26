Statsd Configuration
====================

These options are specific to statsd in addition to the
:doc:`common options </config>`.

Configuration File
------------------

   The ``[statsd]`` section is specific to the libra_statsd utility.  Below is
   an example:

   .. code-block:: ini

      [statsd]
      

Command Line Options
--------------------
   .. program:: libra_statsd

   .. option:: --api_server <HOST:PORT>

      The hostname/IP and port colon separated for use with the HP REST API
      driver.  Can be specified multiple times for multiple servers.  This
      option is also used for the hp_rest alerting driver.

   .. option:: --gearman_ssl_ca <PATH>

      The path for the Gearman SSL Certificate Authority.

   .. option:: --gearman_ssl_cert <PATH>

      The path for the Gearman SSL certificate.

   .. option:: --gearman_ssl_key <PATH>

      The path for the Gearman SSL key.

   .. option:: --server <HOST:PORT>

      Used to specify the Gearman job server hostname and port. This option
      can be used multiple times to specify multiple job servers

   .. option:: --driver <DRIVER LIST>

      The drivers to be used for alerting.  This option can be used multiple
      times to specift multiple drivers.

   .. option:: --ping_interval <PING_INTERVAL>

      How often to run a ping check of load balancers (in seconds), default 60

   .. option:: --poll_interval <POLL_INTERVAL>

      How long to wait until we consider the initial ping check failed and
      send a second ping. Default is 5 seconds.

   .. option:: --poll_interval_retry <POLL_INTERVAL>

      How long to wait until we consider the second and final ping check
      failed. Default is 30 seconds.

   .. option:: --repair_interval <REPAIR_INTERVAL>

      How often to run a check to see if damaged load balancers had been
      repaired (in seconds), default 180

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


