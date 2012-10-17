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
      which then executes the :py:func:`lbaas_task` function for each message.
      It does not exit unless the worker itself exits.

      If all Gearman job servers become unavailable, the worker would
      normally exit. This method identifies that situation and periodically
      attempts to restart the worker in an endless loop.