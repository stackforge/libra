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
       api_server = 10.0.0.1:8889 10.0.0.2:8889
       nodes = 10
       check_interval = 5
       failed_interval = 15
       node_basename = 'libra'

Command Line Options
--------------------
   .. program:: libra_pool_mgm

   .. option:: --api_server <HOST:PORT>

      The hostname/IP and port colon separated pointed to an Admin API server
      for use with the HP REST API driver.  Can be specified multiple times for
      multiple servers

   .. option:: --check_interval <CHECK_INTERVAL>

      How often to check the API server to see if new nodes are needed
      (value is minutes)

   .. option:: --failed_interval <FAILED_INTERVAL>

      How often to check the list of failed node uploads to see if the nodes
      are now in a good state (value is in minutes)

   .. option:: --driver <DRIVER>

      API driver to use. Valid driver options are:

      * *hp_rest* - HP REST API, talks to the HP Cloud API server (based
        on Atlas API)
        This is the default driver.

   .. option:: --datadir <DATADIR>

      The data directory used to store things such as the failed node list.

   .. option:: -n, --nodaemon

      Do not run as a daemon. This option is useful for debugging purposes
      only as the worker is intended to be run as a daemon normally.

   .. option:: --node_basename <NODE_BASENAME>

      A name to prefix the UUID name given to the nodes the pool manager
      generates.

   .. option:: --nodes <NODES>

      The size of the pool of spare nodes the pool manager should keep.

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

