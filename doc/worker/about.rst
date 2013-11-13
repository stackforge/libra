===========
Description
===========

Purpose
-------

A Python-based Gearman worker that handles messages for the Gearman job queue
sharing the same name as the local hostname. The messages that it receives are
JSON objects describing a load balancer, and returns this same JSON object, but
with status fields added to describe the state of the LB.

Configuration File
------------------

It can be easier to give options via a configuration file. See the sample
configuration file etc/sample_libra.cfg for an example and further
documentation. Use the :option:`--config-file <libra_worker --config-file>` option
to specify the configuration file to read.

Running the Worker
------------------

The worker can run in either daemon or non-daemon mode. Daemon mode requires
escalated privileges so that it can behave like a proper daemon. Non-daemon
mode (:option:`--nodaemon <libra_worker --nodaemon>` option) is useful for testing.

Basic commands::

    # Getting help
    $ libra_worker -h

    # Start up as a daemon running as the `haproxy` user and
    # connecting to the local Gearman job server.
    $ sudo libra_worker --user haproxy --group haproxy --server  127.0.0.1:4730

    # Start up with debugging output in non-daemon mode
    $ libra_worker --debug --nodaemon

NOTE: When running the worker in daemon mode, you must make sure that the
directory where the PID file will be (:option:`--pid <libra_worker.py -p>`
option) and the directory where the log files will be written
(:option:`--log-file <libra_worker --log-file>` option) exists and is writable
by the user/group specified with the :option:`--user <libra_worker --user>`
and :option:`--group <libra_worker.py --group>` options.

You can verify that the worker is running by using the sample Gearman
client in the bin/ directory::

    $ bin/client.py

