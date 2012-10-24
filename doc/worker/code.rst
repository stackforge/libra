Code Walkthrough
================

Here we'll highlight some of the more important code aspects.

Gearman Task
------------
.. py:module:: libra.worker.worker

.. py:function:: lbaas_task(worker, job)

   This is the function executed by the Gearman worker for each message
   retrieved from a Gearman job server.

Server Class
------------

.. py:module:: libra.worker.worker

.. py:class:: Server(logger, servers, reconnect_sleep)

   This class encapsulates the server activity once it starts in either
   daemon or non-daemon mode and all configuration options are read.

   .. py:method:: main()

      The one and only method in the class and represents the primary
      function of the program. The Gearman worker is started in this method,
      which then executes the :py:func:`~lbaas_task` function for each message.
      It does not exit unless the worker itself exits.

      If all Gearman job servers become unavailable, the worker would
      normally exit. This method identifies that situation and periodically
      attempts to restart the worker in an endless loop.

LBaaSController Class
---------------------

.. py:module:: libra.worker.controller

.. py:class:: LBaaSController(logger, driver, json_msg)

   This class is used by the :py:func:`~libra.worker.worker.lbaas_task` function drive the
   Gearman message handling.

   .. py:method:: run()

      This is the only method that should be called directly. It parses the
      JSON message given during object instantiation and determines the action
      to perform based on the contents. It returns another JSON message that
      should then be returned to the Gearman client.

LoadBalancerDriver Class
------------------------

.. py:module:: libra.worker.drivers

.. py:class:: LoadBalancerDriver

   This defines the API for interacting with various load balancing
   appliances. Drivers for these appliances should inherit from this
   class and implement the relevant API methods that it can support.
   `This is an abstract class and is not meant to be instantiated directly.`

   Generally, an appliance driver should queue up any configuration changes
   made via these API calls until the :py:meth:`create` method is called.
   The :py:meth:`suspend`, :py:meth:`enable`, and :py:meth:`delete` methods
   should take immediate action.

   .. py:method:: init()

   .. py:method:: add_server(host, port)

   .. py:method:: set_protocol(protocol, port)

   .. py:method:: set_algorithm(algorithm)

   .. py:method:: create()

   .. py:method:: suspend()

   .. py:method:: enable()

   .. py:method:: delete()

Known Load Balancer Drivers Dictionary
--------------------------------------

.. py:module:: libra.worker.drivers

.. py:data:: known_drivers

   This is the dictionary that maps values for the :option:`--driver` option
   to a class implementing the driver :py:class:`~LoadBalancerDriver` API
   for that appliance. After implementing a new driver class, you simply add
   a new entry to this dictionary to plug in the new driver.

Relationship Diagram
--------------------

Below is a conceptual diagram that shows the basic relationships between
the items described above::

  +-------------+     JSON request      +-------------------+
  |   Gearman   | --------------------> |                   |
  |   worker    |                       |  LBaaSController  |
  |   task      | <-------------------- |                   |
  +-------------+     JSON response     +-------------------+
                                           |            ^
                                           |            |
                                 API call  |            | (Optional Exception)
                                           |            |
                                           V            |
                                        +----------------------+
                                        |                      |
                                        |  LoadBalancerDriver  |
                                        |                      |
                                        +----------------------+

The steps shown above are:

.. py:module:: libra.worker

* The Gearman worker task is run when the worker receives a message from the
  Gearman job server (not represented above).
* This task then uses the :py:class:`~controller.LBaaSController` to process
  the message that it received.
* Based on the contents of the message, the controller then makes the relevant
  driver API calls using the :py:class:`~drivers.LoadBalancerDriver` driver
  that was selected via the :option:`--driver` option.
* The driver executes the API call. If the driver encounters an error during
  execution, an exception is thrown that should be handled by the
  :py:class:`~controller.LBaaSController` object. Otherwise, nothing is
  returned, indicating success.
* The :py:class:`~controller.LBaaSController` object then creates a response
  message and returns this message back to the Gearman worker task.
* The Gearman worker task sends the response message back through the Gearman
  job server to the originating client (no represented above).