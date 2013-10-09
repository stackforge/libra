.. _libra-worker-driver:

Drivers
=======

The driver is the part of the Worker which is responsible for doing actions
towards the underlying service like HAProxy or other.

It's a plugin based python class that has a generic API for configuring up
:term:`device`.

LoadBalancerDriver Class
------------------------

See Drivers for driver documentation

.. py:module:: libra.worker.drivers

.. py:class:: LoadBalancerDriver

   This defines the API for interacting with various load balancing
   appliances. Drivers for these appliances should inherit from this
   class and implement the relevant API methods that it can support.
   `This is an abstract class and is not meant to be instantiated directly.`

   Generally, an appliance driver should queue up any configuration changes
   made via these API calls until the :py:meth:`create` method is called.
   The :py:meth:`suspend`, :py:meth:`enable`, :py:meth:`delete`,
   :py:meth:`get_stats()` and :py:meth:`archive` methods should take
   immediate action.

   .. py:method:: init()

   .. py:method:: add_server(host, port)

   .. py:method:: set_protocol(protocol, port)

   .. py:method:: set_algorithm(algorithm)

   .. py:method:: create()

   .. py:method:: suspend()

   .. py:method:: enable()

   .. py:method:: delete()

   .. py:method:: get_stats()

   .. py:method:: archive()

Known Load Balancer Drivers Dictionary
--------------------------------------

.. py:data:: known_drivers

   This is the dictionary that maps values for the
   :option:`--driver <libra_worker.py --driver>` option
   to a class implementing the driver :py:class:`~LoadBalancerDriver` API
   for that appliance. After implementing a new driver class, you simply add
   a new entry to this dictionary to plug in the new driver.

.. note::

    See below for driver specific documentation

.. toctree::
  :maxdepth: 2
  :glob:

  drivers/*