Configuration of Node Pool Manager and Worker
=============================================

Options can be specified either via the command line, or with a configuration
file, or both. Options given on the command line will override any options
set in the configuration file.

Configuration File Format
-------------------------
   The configuration file is in `INI format
   <http://en.wikipedia.org/wiki/INI_file>`_. Options are expressed in one of
   two forms::

      key = value
      key : value

   Some key points to note:

   * Boolean options should be given either a value of `true` or `false`.
   * Some options can contain multiple values (see 'server' option in the
     ``[worker]`` section).
   * If an option has both a short-form and long-form (e.g., ``-d`` and
     ``--debug``), then you should use the long-form name in the configuration
     file.
   * Unknown sections are ignored. This allows all Libra utilities to share
     the same configuration file, if desired.

Global Section
^^^^^^^^^^^^^^

   The ``[global]`` section contains options common to the various Libra
   utilities (worker, mgm, etc). This section is read before any other
   section, so values may be overridden by the other sections:

   .. code-block:: ini

      [global]
      verbose = true

Worker Section
^^^^^^^^^^^^^^

   The ``[worker]`` section is specific to the libra_worker utility. Below
   is an example:

   .. code-block:: ini

      [worker]
      user = haproxy
      group = haproxy
      driver = haproxy
      reconnect_sleep = 60
      server = 10.0.0.1:8080 10.0.0.2:8080
      pid = /var/run/libra/libra_worker.pid
      logfile = /var/log/libra/libra_worker.log

Pool Manager Section
^^^^^^^^^^^^^^^^^^^^^

   The ``[mgm]`` section is specific to the libra_pool_mgm utility. Below is an
   example:

   .. code-block:: ini

       [mgm]
       pid = /var/run/libra/libra_mgm.pid
       logfile = /var/log/libra/libra_mgm.log
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
       node_basename = 'libra'


Worker Command Line Options
---------------------------
   .. program:: libra_worker.py

   .. option:: -c <FILE>, --config <FILE>

      Load options from the specified configuration file. Command line
      options will take precedence over any options specified in the
      configuration file.

   .. option:: -d, --debug

      Enable debugging output.

   .. option:: --driver <DRIVER>

      Load balancer driver to use. Valid driver options are:

      * *haproxy* - `HAProxy <http://haproxy.1wt.eu>`_ software load balancer.
        This is the default driver.

   .. option:: --group <GROUP>

      Specifies the group for the process when run in daemon mode.

   .. option:: -h, --help

      Show the help message and quit.

   .. option:: -l <FILE>, --logfile <FILE>

      Name of the log file. When running in daemon mode, the default log
      file is */var/log/libra/libra_worker.log*. When not in daemon mode,
      logging will go to STDOUT unless a log file is specified.

   .. option:: -n, --nodaemon

      Do not run as a daemon. This option is useful for debugging purposes
      only as the worker is intended to be run as a daemon normally.

   .. option:: -p <PID>, --pid <PID>

      Name of the PID file to use. Default is:
      */var/run/libra/libra_worker.pid*

   .. option:: -s <SECONDS>, --reconnect_sleep <SECONDS>

      The number of seconds to sleep between job server reconnect attempts
      when no specified job servers are available. Default is 60 seconds.

   .. option:: --server <HOST:PORT>

      Used to specify the Gearman job server hostname and port. This option
      can be used multiple times to specify multiple job servers.

   .. option:: --user <USER>

      Specifies the user for the process when in daemon mode. Default is the
      current user.

   .. option:: -v, --verbose

      Enable verbose output. Normally, only errors are logged. This enables
      additional logging, but not as much as the :option:`-d` option.

   .. option:: --stats-poll <SECONDS>

      The number of seconds to sleep between statistics polling of the
      load balancer driver. Default is 300 seconds.

Pool Manager Command Line Options
---------------------------------
   .. program:: libra_pool_mgm.py

   .. option:: --api_server <HOST:PORT>

      The hostname/IP and port colon separated for use with the HP REST API
      driver.  Can be specified multiple times for multiple servers

   .. option:: -c <FILE>, --config <FILE>

      Load options from the specified configuration file. Command line
      options will take precedence over any options specified in the
      configuration file.

   .. option:: --check_interval <CHECK_INTERVAL>

      How often to check the API server to see if noew nodes are needed
      (in value is minutes)

   .. option:: -d, --debug

      Enable debugging output.

   .. option:: --driver <DRIVER>

      API driver to use. Valid driver options are:

      * *hp_rest* - HP REST API, talks to the HP Cloud API server (based
        on Atlas API)
        This is the default driver.

   .. option:: --group <GROUP>

      Specifies the group for the process when run in daemon mode.

   .. option:: -h, --help

      Show the help message and quit.

   .. option:: -l <FILE>, --logfile <FILE>

      Name of the log file. When running in daemon mode, the default log
      file is */var/log/libra/libra_worker.log*. When not in daemon mode,
      logging will go to STDOUT unless a log file is specified.

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

   .. option:: -p <PID>, --pid <PID>

      Name of the PID file to use. Default is:
      */var/run/libra/libra_worker.pid*

   .. option:: --user <USER>

      Specifies the user for the process when in daemon mode. Default is the
      current user.

   .. option:: -v, --verbose

      Enable verbose output. Normally, only errors are logged. This enables
      additional logging, but not as much as the :option:`-d` option.


