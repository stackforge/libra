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
      db_host=localhost
      db_user=root
      db_pass=
      db_schema=lbaas
      ssl_certfile=/opt/server.crt
      ssl_keyfile=/opt/server.key

Command Line Options
--------------------
   .. program:: libra_admin_api

   .. option:: --host <IP ADDRESS>

      The IP address to bind the frontend to, default is 0.0.0.0

   .. option:: --port <PORT NUMBER>

      The port number to listen on, default is 8889

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

   .. option:: --ssl_certfile <PATH>

      The path for the SSL certificate file to be used for frontend of the API
      server

   .. option:: --ssl_keyfile <PATH>

      The path for the SSL key file to be used for the frontend of the API
      server

