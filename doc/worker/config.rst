Configuration
=============

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

   .. option:: -h, --help

      Show the help message and quit.

   .. option:: -n, --nodaemon

      Do not run as a daemon. This option is useful for debugging purposes
      only as the worker is intended to be run as a daemon normally.

   .. option:: -v, --verbose

      Enable verbose output. Normally, only errors are logged. This enables
      additional logging, but not as much as the :option:`-d` option.

