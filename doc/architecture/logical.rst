====================
Logical architecture
====================

See information for each component for more information.

* :ref:`libra-pool-mgm` - A node pool manager to keep a warm spare pool of load balancers ready
* :ref:`libra-worker` - A node worker to asynchronously communicate to the API server
* :ref:`libra-api` - A customer API server
* :ref:`libra-admin-api` - An administrative API server

The API server is based on a modified version of the `Atlas API specification
<https://wiki.openstack.org/wiki/Atlas-LB>`_.

High level overview
-------------------

.. image:: /img/libralayout.png

Here you can see that the pool manager spins up the required Nova nodes with
the load balancer image.  It then hands the details of these nodes over to the
Admin API server.

The client sends an API request to the API server, which in turn sends the
configuration information to the worker on the load balancer node.  The worker
has a plugin system to speak to multiple load balancer types but is currently
designed to use HAProxy.

The statsd monitoring system routinely probes the workers and can alert on as
well as disable faulty nodes.

The parts of this diagram in orange are provided by the Libra codebase.
