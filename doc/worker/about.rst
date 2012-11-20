Description
===========

Purpose
-------

A Python-based Gearman worker that handles work for the job queue named
'lbaas-HOSTNAME'. It receives JSON data describing a load balancer, and
returns this same JSON object, but with status fields added to describe
the state of the LB.

Installation
------------

Installing the Required Tools
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You must have Python setuptools installed. On Ubuntu::

    $ sudo apt-get install python-setuptools

Now you may install the Libra toolset::

    $ sudo python setup.py install

The worker also needs some packages installed in order to be used with
HAProxy. The commands below will install them on Ubuntu::

    $ sudo apt-get install haproxy
    $ sudo apt-get install socat

The Ubuntu default is to have HAProxy disabled. You will need to edit the
file */etc/default/haproxy* and set *ENABLED* to 1 if you want HAProxy to
actually start (hint: you do).

Edit /etc/sudoers
^^^^^^^^^^^^^^^^^

The worker needs to be able to run some commands as root without being
prompted for a password. It is suggested that you run the worker as
the `haproxy` user and `haproxy` group on Ubuntu systems. Then add the
following line to /etc/sudoers::

    %haproxy ALL = NOPASSWD: /usr/sbin/service, /bin/cp, /bin/mv, /bin/rm, /usr/bin/socat

The above lets everyone in the *haproxy* group run those commands
as root without being prompted for a password.

Configuration File
------------------

It can be easier to give options via a configuration file. See the sample
configuration file etc/sample_libra.cfg for an example and further
documentation. Use the :option:`--config <libra_worker.py -c>` option
to specify the configuration file to read.

Running the Worker
------------------

The worker can run in either daemon or non-daemon mode. Daemon mode requires
escalated privileges so that it can behave like a proper daemon. Non-daemon
mode (:option:`--nodaemon <libra_worker.py -n>` option) is useful for testing.

Basic commands::

    # Getting help
    $ libra_worker -h

    # Start up as a daemon running as the `haproxy` user and
    # connecting to the local Gearman job server.
    $ sudo libra_worker --user haproxy --group haproxy --server 127.0.0.1:4730

    # Start up with debugging output in non-daemon mode
    $ libra_worker --debug --nodaemon

NOTE: When running the worker in daemon mode, you must make sure that the
directory where the PID file will be (:option:`--pid <libra_worker.py -p>`
option) and the directory where the log files will be written
(:option:`--logfile <libra_worker.py -l>` option) exists and is writable
by the user/group specified with the :option:`--user <libra_worker.py --user>`
and :option:`--group <libra_worker.py --group>` options. Also, the
Python module used to start the daemon process does not like it when the PID
file already exists at startup.

    **IF THE WORKER IMMEDIATELY EXITS WHEN STARTED IN DAEMON MODE, AND NO ERROR
    MESSAGES ARE IN THE LOG, ONE OF THESE REASONS IS THE MOST LIKELY CAUSE!**

You can verify that the worker is running by using the sample Gearman
client in the bin/ directory::

    $ bin/client.py

