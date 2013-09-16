API Configuration
=================

These options are specific to the API in addition to the
:doc:`common options </config>`.

Configuration File
------------------

   The ``[api]`` section is specific to the libra_api utility.  Below is an
   example:

   .. code-block:: ini

      [api]
      db_sections=mysql1
      gearman=127.0.0.1:4730
      keystone_module=keystoneclient.middleware.auth_token:AuthProtocol
      swift_basepath=lbaaslogs
      swift_endpoint=https://host.com:443/v1/
      ssl_certfile=/opt/certfile.crt
      ssl_keyfile=/opt/keyfile.key

      [mysql1]
      host=localhost
      port=3306
      username=root
      password=
      schema=lbaas
      ssl_cert=/opt/mysql_cert.crt
      ssl_key=/opt/mysql_key.key
      ssl_ca=/opt/mysql_ca.ca

   In addition to this any options that are specific to the given keystone
   module should be stored in the ``[keystone]`` section.

Command Line Options
--------------------
   .. program:: libra_api

   .. option:: --host <IP ADDRESS>

      The IP address to bind the frontend to, default is 0.0.0.0

   .. option:: --port <PORT NUMBER>

      The port number to listen on, default is 443

   .. option:: --disable_keystone

      Do not use keystone authentication, for testing purposes only

   .. option:: --db_secions <SECTIONNAME>

      Config file sections that describe the MySQL servers.  This option can
      be specified multiple times for Galera or NDB clusters.

   .. option:: --gearman <HOST:POST>

      Used to specify the Gearman job server hostname and port. This option
      can be used multiple times to specify multiple job servers.

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

      The path for the Gearman SSL Certificate Authority

   .. option:: --gearman_ssl_cert <PATH>

      The path for the Gearman SSL certificate

   .. option:: --gearman_ssl_key <PATH>

      The path for the Gearman SSL key

   .. option:: --keystone_module <MODULE:CLASS>

      A colon separated module and class to use as the keystone authentication
      module.  The class should be compatible with keystone's AuthProtocol
      class.

   .. option:: --swift_basepath <CONTAINER>

      The default container to be used for customer log uploads.

   .. option:: --swift_endpoint <URL>

      The default endpoint for swift.  The user's tenant ID will automatically
      be appended to this unless overridden at the log archive request.

   .. option:: --ssl_certfile <PATH>

      The path for the SSL certificate file to be used for frontend of the API
      server

   .. option:: --ssl_keyfile <PATH>

      The path for the SSL key file to be used for the frontend of the API
      server

   .. option:: --ip_filters <FILTERS>

      A mask of IP addresses to filter for backend nodes in the form
      xxx.xxx.xxx.xxx/yy

      Any backend node IP address supplied which falls outside these filters
      will result in an error for the create or node add functions.
      This option can be specified multiple times.
