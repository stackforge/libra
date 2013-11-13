=============
Worker common
=============

.. _install-worker-sudo:

Sudo
++++

The worker needs to be able to run some commands as root without being
prompted for a password. It is suggested that you run the worker as
the `haproxy` user and `haproxy` group on Ubuntu systems. Then add the
following line to /etc/sudoers.d/haproxy::

::

    echo '%haproxy ALL = NOPASSWD: /usr/sbin/service, /bin/cp, /bin/mv, /bin/rm, /bin/chown' > /etc/sudoers.d/haproxy
    sudo chmod 0440 /etc/sudoers.d/haproxy

The above lets everyone in the *haproxy* group run those commands
as root without being prompted for a password.


.. _install-worker-haproxy:

HAProxy
+++++++

1. Install system packages using apt-get

::

    $ sudo apt-get install haproxy socat

2. Enable it

.. note::

    The Ubuntu default is to have HAProxy disabled. You will need to edit the
    file */etc/default/haproxy* and set *ENABLED* to 1 if you want HAProxy to
    actually start (hint: you do).

