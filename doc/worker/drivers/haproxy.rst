
.. _libra-worker-driver-haproxy:

HAProxy driver
==============

Configuration
-------------

.. option:: --haproxy_logfile <FILE>

   Configure the path for where to put haproxy log.

   .. note::

        See :ref:`libra-worker-driver-haproxy-archiving` for information on
        archiving.

.. option:: --haproxy_service <service>

   The underlying OS Service implementation to use

   Default: ubuntu

.. _libra-worker-driver-haproxy-archiving:

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