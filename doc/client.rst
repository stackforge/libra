Libra Client
============

Synopsis
--------

:program:`libra_client.py` [:ref:`OPTIONS <libra_client-options>`] [:ref:`COMMAND <libra_client-commands>`]

Description
-----------

:program:`libra_client.py` is a utility designed to communicate with Atlas API
based Load Balancer as a Service systems.

.. _libra_client-options:

Global Options
--------------

.. program:: libra_client.py

.. option:: --help, -h

   Show help message and exit

.. option:: --os_auth_url <auth-url>

   The OpenStack authentication URL

.. option:: --os_username <auth-user-name>

   The user name to use for authentication

.. option:: --os_password <auth-password>

   The password to use for authentication

.. option:: --os_tenant_name <auth-tenant-name>

   The tenant to authenticate to

.. option:: --os_region_name <region-name>

   The region the load balancer is located

.. _libra_client-commands:

Client Commands
---------------

======= ==================
Command Required Parameter
======= ==================
list    None
create  loadbalancerID
modify  loadbalancerID
status  loadbalancerID
======= ==================

.. program:: libra_client.py create

create
^^^^^^

Create a load balancer

.. option:: --name <name>

   The name of the node to be created

.. option:: --port <port>

   The port the load balancer will listen on

.. option:: --protocol <protocol>

   The protocol type for the load balancer (HTTP or TCP)

.. option:: --node <ip:port>

   The IP and port for a load balancer node (can be used multiple times)

.. option:: --vip <vip>

   The virtual IP ID of an existing load balancer to attach to

.. program:: libra_client.py modify

modify
^^^^^^

Update a load balancer's configuration

.. option:: --name <name>

   A new name for the load balancer

.. option:: --algorithm <algorithm>

   A new algorithm for the load balancer

.. program:: libra_client.py list

list
^^^^

List all load balancers

.. program:: libra_client.py status

status
^^^^^^

Get the status of a single load balancer
