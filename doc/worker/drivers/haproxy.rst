
.. _libra-worker-driver-haproxy:

HAProxy driver
==============

Log archiving
-------------

In order to support log-archiving with haproxy you need to redirect
the rsyslog feed from local0 to a dedicated file

.. note::

    Change the /var/log/haproxy.log to the path you have set in the worker
    section of the config.

::

    cat >/etc/rsyslog.d/10-haproxy.conf<<EOF
    $template Haproxy,"%TIMESTAMP% %msg%\n"
    local0.* -/var/log/haproxy.log;Haproxy
    # don't log anywhere else
    local0.* ~
    EOF