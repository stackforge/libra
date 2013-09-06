Pool Manager Configuration
==========================

These options are specific to the pool manager in addition to the
:doc:`common options </config>`.

Configuration File
------------------

   The ``[mgm]`` section is specific to the libra_pool_mgm utility. Below is an
   example:

   .. code-block:: ini

       [mgm]
       pid = /var/run/libra/libra_mgm.pid
       logfile = /var/log/libra/libra_mgm.log
       datadir = /etc/libra/
       nova_auth_url = https://region-a.geo-1.identity.hpcloudsvc.com:35357/v2.0/
       nova_user = username
       nova_pass = password
       nova_tenant = tenant
       nova_region = region
       nova_keyname = default
       nova_secgroup = default
       nova_image = 12345
       nova_image_size = standard.medium
       gearman=127.0.0.1:4730
       node_basename = 'libra'

Command Line Options
--------------------
   .. program:: libra_pool_mgm

   .. option:: --datadir <DATADIR>

      The data directory used to store things such as the failed node list.

   .. option:: -n, --nodaemon

      Do not run as a daemon. This option is useful for debugging purposes
      only as the worker is intended to be run as a daemon normally.

   .. option:: --node_basename <NODE_BASENAME>

      A name to prefix the UUID name given to the nodes the pool manager
      generates.

   .. option:: --nova_auth_url <NOVA_AUTH_URL>

      The URL used to authenticate for the Nova API

   .. option:: --nova_user <NOVA_USER>

      The username to authenticate for the Nova API

   .. option:: --nova_pass <NOVA_PASS>

      The password to authenticate for the Nova API

   .. option:: --nova_tenant <NOVA_TENANT>

      The tenant to use for the Nova API

   .. option:: --nova_region <NOVA_REGION>

      The region to use for the Nova API

   .. option:: --nova_keyname <NOVA_KEYNAME>

      The key name to use when spinning up nodes in the Nova API

   .. option:: --nova_secgroup <NOVA_SECGROUP>

      The security group to use when spinning up nodes in the Nova API

   .. option:: --nova_image <NOVA_IMAGE>

      The image ID or name to use on new nodes spun up in the Nova API

   .. option:: --nova_image_size <NOVA_IMAGE_SIZE>

      The flavor ID (image size ID) or name to use for new nodes spun up in
      the Nova API

   .. option:: --gearman_ssl_ca <PATH>

      The path for the Gearman SSL Certificate Authority.

   .. option:: --gearman_ssl_cert <PATH>

      The path for the Gearman SSL certificate.

   .. option:: --gearman_ssl_key <PATH>

      The path for the Gearman SSL key.

   .. option:: --gearman <HOST:PORT>

      Used to specify the Gearman job server hostname and port. This option
      can be used multiple times to specify multiple job servers

