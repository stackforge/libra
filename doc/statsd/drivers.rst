Statsd Drivers
==============

Introduction
------------

Statsd has a small driver API to be used for alerting.  Multiple drivers can
be loaded at the same time to alert in multiple places.

Design
------

The base class called ``AlertDriver`` is used to create new drivers.  These
will be supplied ``self.logger`` to use for logging and ``self.args`` which
contains the arguments supplied to statsd.  Drivers using this need to
supply two functions:

.. py:class:: AlertDriver

   .. py:method:: send_alert(message, device_id)

      :param message: A message with details of the failure
      :param device_id: The ID of the device that has failed

   .. py:method:: send_repair(message, device_id)

      :param message: A message with details of the recovered load balancer
      :param device_id: The ID of the device that has been recovered


.. py:data:: known_drivers

   This is the dictionary that maps values for the
   :option:`--driver <libra_statsd.py --driver>` option
   to a class implementing the driver :py:class:`~AlertDriver` API
   for the statsd server. After implementing a new driver class, you simply add
   a new entry to this dictionary to make it a selectable option.

Dummy Driver
------------

This driver is used for simple testing/debugging.  It echos the message details
into statsd's log file.

Datadog Driver
--------------

The Datadog driver uses the Datadog API to send alerts into the Datadog event
stream.  Alerts are sent as 'ERROR' and repairs as 'SUCCESS'.

HP REST Driver
--------------

This sends messages to the HP REST API server to mark nodes as ERROR/ONLINE.


