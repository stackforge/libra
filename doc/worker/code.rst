Code Walkthrough
================

Here we'll highlight some of the more important code aspects.

Gearman Worker Thread
---------------------
.. py:module:: libra.worker.worker

.. py:function:: config_thread(logger, driver, servers, reconnect_sleep)

   This function encapsulates the functionality for the Gearman worker thread
   that will be started by the :py:class:`~libra.worker.main.EventServer`
   class. It should never exit.

   This function connects to the Gearman job server(s) and runs the Gearman
   worker task, which itself is another function that is called for each
   message retrieved from the Gearman job servers.

   If all Gearman job servers become unavailable, the worker would
   normally exit. This function identifies that situation and periodically
   attempts to restart the worker in an endless loop.


EventServer Class
-----------------

.. py:module:: libra.worker.main

.. py:class:: EventServer(logger)

   This class encapsulates the server activity once it starts in either
   daemon or non-daemon mode and all configuration options are read. It
   uses the `eventlet <http://eventlet.net/doc/>`_ Python module to start
   tasks that it will be supplied.

   .. py:method:: main(tasks)

      The one and only method in the class and represents the primary
      function of the program. A list of functions and their parameters
      is supplied as the only argument. Each function will be started in
      its own Green Thread.


LBaaSController Class
---------------------

.. py:module:: libra.worker.controller

.. py:class:: LBaaSController(logger, driver, json_msg)

   This class is used by the Gearman task started within the worker thread
   (the :py:func:`~libra.worker.worker.config_thread` function) to drive the
   Gearman message handling.

   .. py:method:: run()

      This is the only method that should be called directly. It parses the
      JSON message given during object instantiation and determines the action
      to perform based on the contents. It returns another JSON message that
      should then be returned to the Gearman client.

LBaaSDriver Class
-----------------

See :ref:`libra-worker-driver` for information


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

* The Gearman worker task used in the worker thread (see the
  :py:func:`~worker.config_thread` function), is run when the worker
  receives a message from the Gearman job server (not represented above).
* This task then uses the :py:class:`~controller.LBaaSController` to process
  the message that it received.
* Based on the contents of the message, the controller then makes the relevant
  driver API calls using the :py:class:`~drivers.LoadBalancerDriver` driver
  that was selected via the :option:`--driver <libra_worker.py --driver>`
  option.
* The driver executes the API call. If the driver encounters an error during
  execution, an exception is thrown that should be handled by the
  :py:class:`~controller.LBaaSController` object. Otherwise, nothing is
  returned, indicating success.
* The :py:class:`~controller.LBaaSController` object then creates a response
  message and returns this message back to the Gearman worker task.
* The Gearman worker task sends the response message back through the Gearman
  job server to the originating client (not represented above).
