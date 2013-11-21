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
      daemon = True
      user = libra
      group = libra

   Options supported in this section:

   .. option:: daemon

      Run as a daemon. Default is 'True'.

   .. option:: user

      Specifies the user for the process when in daemon mode. Default is the
      current user.

   .. option:: group

      Specifies the group for the process when run in daemon mode.


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

      Enable TCP KEEPALIVE pings. Default is 'False'.

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
