Configuration of Services
=========================

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
      nodaemon = false
      syslog = true
      syslog-socket = /dev/log
      syslog-facility = local7
      debug = true
      pid = /var/run/libra_tool.pid
      logfile = /var/log/libra/libra_tool.log
      user = libra
      group = libra

   The options listed above are common to all libra applications so can either
   be used in the ``[global]`` section or in an application's individual
   section.

Common Command Line Options
---------------------------
   These command line options are common to all libra utilities

   .. option:: -c <FILE>, --config <FILE>

      Load options from the specified configuration file. Command line
      options will take precedence over any options specified in the
      configuration file.

   .. option:: -d, --debug

      Enable debugging output.

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

   .. option:: --syslog

      Send log events to syslog.

   .. option:: --syslog-socket

      Socket to use for the syslog connection. Default is */dev/log*.

   .. option:: --syslog-facility

      Syslog logging facility. Default is *LOCAL7*.

   .. option:: --user <USER>

      Specifies the user for the process when in daemon mode. Default is the
      current user.

   .. option:: -v, --verbose

      Enable verbose output. Normally, only errors are logged. This enables
      additional logging, but not as much as the :option:`-d` option.

