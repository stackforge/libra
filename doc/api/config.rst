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
      db_host=localhost
      db_user=root
      db_pass=
      db_schema=lbaas
      gearman=127.0.0.1:4730
      keystone_module=keystoneclient.middleware.auth_token:AuthProtocol
      swift_basepath=lbaaslogs
      swift_endpoint=https://host.com:443/v1/
      ssl_certfile=/opt/certfile.crt
      ssl_keyfile=/opt/keyfile.key

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

   .. option:: --db_host <HOSTNAME>

      The host name for the MySQL database server

   .. option:: --db_port <PORT>

      The port number for the MySQL database server

   .. option:: --db_user <USERNAME>

      The username for the MySQL database server

   .. option:: --db_pass <PASSWORD>

      The password for the MySQL database server

   .. option:: --db_schema <SCHEMA>
      
      The schema containing the LBaaS tables in the MySQL database server

   .. option:: --db_ssl

      Enable MySQL SSL support

   .. option:: --db_ssl_cert <CERTIFICATE PATH>

      The path for the MySQL SSL certificate

   .. option:: --db_ssl_key <KEY PATH>

      The path for the MySQL SSL key

   .. option:: --db_ssl_ca <CA PATH>

      The path for the MySQL SSL Certificate Authority

   .. option:: --gearman <HOST:POST>

      Used to specify the Gearman job server hostname and port. This option
      can be used multiple times to specify multiple job servers.

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
