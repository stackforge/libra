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

   .. option:: --db_secions <SECTIONNAME>

      Config file sections that describe the MySQL servers.  This option can
      be specified multiple times for Galera or NDB clusters.

   .. option:: --ssl_certfile <PATH>

      The path for the SSL certificate file to be used for frontend of the API
      server

   .. option:: --ssl_keyfile <PATH>

      The path for the SSL key file to be used for the frontend of the API
      server

