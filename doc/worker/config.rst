Configuration
=============

Options can be specified either via the command line, or with a configuration
file, or both.

Configuration File Format
-------------------------

Command Line Options
--------------------

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

   .. option:: -s <SECONDS>

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

