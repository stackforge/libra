.. _architecture-production:

=======================
Production Architecture
=======================

See information for each component for more information.

* :ref:`libra-pool-mgm` - A node pool manager to keep a warm spare pool of load balancers ready
* :ref:`libra-worker` - A node worker to asynchronously communicate to the API server
* :ref:`libra-api` - A customer API server
* :ref:`libra-admin-api` - An administrative API server

High level overview
-------------------

* Some cloud or virtualization system.
* User and/or Tenant with required privileges / resources.
* Ubuntu 12.04 Precise x86_64 image for :term:`instance`.
* HAProxy for LoadBalancers.
* Gearman for Libra service communication.
* MySQL Galera Multi-master cluster for HA databases.

Think of each service as a :term:`instance`, for each service or :term:`instance`
running services we create 1 pr :term:`az`.


Diagram
-------
In the case below the setup is

* 1 gearman :term:`instance` pr :term:`az`.
* 1 MySQL Galera :term:`instance` pr :term:`az`.
* n+ workers running HAProxy accross multiple pr :term:`az`

.. image:: /img/production.png
