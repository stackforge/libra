Introduction
============

Libra is a Load Balancer as a Service (LBaaS) system originally designed by
Hewlett-Packard Cloud Services.  It consists of three of the core components
required to get LBaaS working:

* A node pool manager to keep a warm spare pool of load balancers ready
* A node worker to asyncronusly communicate to the API server

It does not (yet) include the API server itself or HAProxy.  The API server is
based on the Atlas API system but communicates to the workers using gearman.

Layout
------

.. image:: libralayout.png

Here you can see that the pool manager spins up the required Nova nodes with
the load balancer image.  It then hands the details of this node over the the
API server.

The client sends an Atlas API request to the API server which in-turn sends the
configuration information to the worker on the load balancer node.  The worker
has a plugin API to speak to multiple load balancer types but is currently
designed to use HAProxy.

The parts of this diagram in orange are provided by the libra codebase.
