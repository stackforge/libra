.. _configuration:

=============
Configuration
=============

Configuration of Services
=========================

Configuration File Format
-------------------------
   Libra uses the `Oslo configuration library <https://wiki.openstack.org/wiki/Oslo/Config>`_
   so its format is similar to other OpenStack programs.

DEFAULT Section
^^^^^^^^^^^^^^^

   The ``[DEFAULT]`` section contains generic options common to the various
   Libra utilities (worker, mgm, etc).

   .. code-block:: ini

      [DEFAULT]
      daemon = true
      user = libra
      group = libra
      verbose = false
      debug = false
      billing_enable = false
      notification_driver = []
      default_notification_level = INFO
      default_publisher_id = None
      host = localhost
      kombu_ssl_version =
      kombu_ssl_keyfile =
      kombu_ssl_certfile =
      kombu_ssl_ca_certs =
      rabbit_use_ssl = false
      rabbit_userid = guest
      rabbit_password = guest
      rabbit_host = localhost
      rabbit_port = 5672
      rabbit_hosts = []
      rabbit_virtual_host = / 
      rabbit_retry_interval = 1
      rabbit_retry_backoff = 2
      rabbit_max_retries = 0
      rabbit_ha_queues = false
      control_exchange = openstack
      amqp_durable_queues = false

   Options supported in this section:

   .. option:: daemon

      Run as a daemon. Default is 'true'.

   .. option:: user

      Specifies the user for the process when in daemon mode. Default is the
      current user.

   .. option:: group

      Specifies the group for the process when run in daemon mode.

   .. option:: verbose

      Prints more verbose output. Sets logging level to INFO from WARNING

   .. option:: debug

      Prints debug output. Sets logging level to DEBUG from WARNING

   .. option:: billing_enable

      Enables the sending of billing information to a rabbitMQ host. It sends
      create and delete loadbalancer messages as well as exists and usage 
      messages on a periodic, configurable basis. See admin_api config.

   .. option:: notification_driver

      Driver or drivers to handle sending notifications for metering / billing.
      For instance, the openstack rpc driver is 
      openstack.common.notifier.rpc_notifier.

   .. option:: default_notification_level

      Default notification level for outgoing notifications

   .. option:: default_publisher_id

      Default publisher_id for outgoing notifications

   .. option:: host

      Default host name to use in notifications. Will use default_publisher_id
      or gethostname() if not set.

   .. option:: host

      Default host name to use in notifications. Will use default_publisher_id
      or gethostname() if not set.

   .. option:: kombu_ssl_version

      SSL version to use (valid only if SSL enabled). valid values are TLSv1,
      SSLv23 and SSLv3. SSLv2 may be available on some distributions

   .. option:: kombu_ssl_keyfile

      SSL key file (valid only if SSL enabled)

   .. option:: kombu_ssl_certfile

      SSL cert file (valid only if SSL enabled)

   .. option:: kombu_ssl_ca_certs

      SSL certification authority file (valid only if SSL enabled)

   .. option:: rabbit_use_ssl

      Connect over SSL for RabbitMQ

   .. option:: rabbit_userid

      The RabbitMQ userid

   .. option:: rabbit_password

      The RabbitMQ password

   .. option:: rabbit_host

      The RabbitMQ broker address where a single node is used

   .. option:: rabbit_port

      The RabbitMQ broker port where a single node is used

   .. option:: rabbit_hosts

      RabbitMQ HA cluster host:port pairs

   .. option:: rabbit_virtual_host

      The RabbitMQ virtual host

   .. option:: rabbit_retry_interval

      How frequently to retry connecting with RabbitMQ

   .. option:: rabbit_retry_backoff

      How long to backoff for between retries when connecting to RabbitMQ

   .. option:: rabbit_max_retries

      Maximum retries with trying to connect to RabbitMQ (the default of 0
      implies an infinite retry count)

   .. option:: rabbit_ha_queues

      Use H/A queues in RabbitMQ (x-ha-policy: all). You need to wipe RabbitMQ
      database when changing this option.

   .. option:: control_exchange

      AMQP exchange to connect to if using RabbitMQ or Qpid

   .. option:: amqp_durable_queues

      Use durable queues in amqp.

Gearman Section
^^^^^^^^^^^^^^^

   The ``[gearman]`` section contains options specific to connecting to
   a Gearman job server. All of the Libra utilities will read this section
   since each connects to Gearman.

   In order to support SSL connections, it is required that all three SSL
   related options be supplied. Also, the user owning the process must be
   able to read all SSL files.

   .. code-block:: ini

      [gearman]
      servers = 10.0.0.1:4730, 10.0.0.2:4730
      poll = 1
      ssl_ca = /etc/ssl/gearman.ca
      ssl_cert = /etc/ssl/gearman.cert
      ssl_key = /etc/ssl/gearman.key

   Options supported in this section:

   .. option:: keepalive

      Enable TCP KEEPALIVE pings. Default is 'false'.

   .. option:: keepcnt

      Max KEEPALIVE probes to send before killing connection.

   .. option:: keepidle

      Seconds of idle time before sending KEEPALIVE probes.

   .. option:: keepintvl

      Seconds between TCP KEEPALIVE probes.

   .. option:: poll

      Gearman worker polling timeout. Default is 1.

   .. option:: reconnect_sleep

      Seconds to sleep between job server reconnects. Default is 60.

   .. option:: servers

      Comma-separated list of Gearman job servers and port in HOST:PORT format.

   .. option:: ssl_ca

      Gearman SSL certificate authority.

   .. option:: ssl_cert

      Gearman SSL certificate.

   .. option:: ssl_key

      Gearman SSL key.
