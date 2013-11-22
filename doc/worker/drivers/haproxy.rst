
.. _libra-worker-driver-haproxy:

HAProxy driver
==============

Configuration File
------------------

   The ``[worker:haproxy]`` section is read by the HAProxy driver.

   .. code-block:: ini

      [worker:haproxy]
      service = ubuntu
      logfile = /var/log/haproxy.log

   Options supported in this section:

   .. option:: logfile

      Path where HAProxy will store its logs. Note that this file is not
      created by the worker, but rather by the haproxy process itself. Its
      contents will be delivered in response to an ARCHIVE request from the
      API server.

      .. note::

        See :ref:`libra-worker-driver-haproxy-archiving` for information on
        archiving.

   .. option:: statsfile

       Location of the HAProxy statistics cache file. This file needs to be
       placed in a location where the worker has write access and where it
       will not be deleted by external processes (so don't place it in /tmp).
       This is used to deliver usage reports to the API server in response to
       a STATS requests.

   .. option:: service

       The underlying OS Service implementation to use. Default is 'ubuntu'.

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
