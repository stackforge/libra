Admin API REST Inteface (v2)
============================

Introduction
------------
This is the new Admin API interface for the LBaaS system.  It will allow the engineers as well as support teams to perform basic tasks on the LBaaS system without direct access using Salt, SSH or MySQL.  It can also be used to automate tasks such as monitoring overall system health.

Authentication & Security
-------------------------
Authentication will be performed in a similar way to the main API server, via. keystone to anyone registered to our service.  There will be, however, one crucial addition.  The database will contain a list of tenant IDs that can actually use the Admin API, anyone else will get a 401 response.  This will also have two levels of access for now we will call 'staff' (USER) and 'administrators' (ADMIN).  In addition to this the Admin API's port will be restricted to users on a VPN.

Since this is an Admin API all actions should be well logged along with the tenantID of the user who actioned them.

API Sections
------------
The Admin API will initially be divided into three distinct sections, Devices, LoadBalancers and Status.  Once we have per-customer defined limits a new section should be added to support that.  In the table below the following conventions are used:

{baseURI} - the endpoint address/IP for the Admin API server

{ver} - The version number (1.0 already exists as a system Admin API, 2.0 shall be the first version)

{lbID} - The load balancer ID

{deviceID} - The device ID

+---------------+----------------------------------+--------+---------------------------------------------+
| Resource      | Operation                        | Method | Path                                        |
+===============+==================================+========+=============================================+
| Devices       | Get a list of devices            | GET    | {baseURI}/{ver}/devices                     |
+---------------+----------------------------------+--------+---------------------------------------------+
| Devices       | Get a single device              | GET    | {baseURI}/{ver}/devices/{deviceID}          |
+---------------+----------------------------------+--------+---------------------------------------------+
| Devices       | Get a device version             | GET    | {baseURI}/{ver}/devices/{deviceID}/discover |
+---------------+----------------------------------+--------+---------------------------------------------+
| Devices       | Deletes a device                 | DELETE | {baseURI}/{ver}/devices/{deviceID}          |
+---------------+----------------------------------+--------+---------------------------------------------+
| LoadBalancers | Get a list of load balancers     | GET    | {baseURI}/{ver}/loadbalancers               |
+---------------+----------------------------------+--------+---------------------------------------------+
| LoadBalancers | Gets a single load balancer      | GET    | {baseURI}/{ver}/loadbalancers/{lbID}        |
+---------------+----------------------------------+--------+---------------------------------------------+
| LoadBalancers | Delete a single load balancer    | DELETE | {baseURI}/{ver}/loadbalancers/{lbID}        |
+---------------+----------------------------------+--------+---------------------------------------------+
| Status        | Get a pool status                | GET    | {baseURI}/{ver}/status/pool                 |
+---------------+----------------------------------+--------+---------------------------------------------+
| Status        | Get the counters                 | GET    | {baseURI}/{ver}/status/counters             |
+---------------+----------------------------------+--------+---------------------------------------------+
| Status        | Get a service status             | GET    | {baseURI}/{ver}/status/service              |
+---------------+----------------------------------+--------+---------------------------------------------+
| Status        | Get the global service limits    | GET    | {baseURI}/{ver}/status/limits               |
+---------------+----------------------------------+--------+---------------------------------------------+
| Status        | Change the global service limits | PUT    | {baseURI}/{ver}/status/limits               |
+---------------+----------------------------------+--------+---------------------------------------------+
| User          | Get a list of Admin API users    | GET    | {baseURI}/{ver}/user                        |
+---------------+----------------------------------+--------+---------------------------------------------+
| User          | Get an Admin API user            | GET    | {baseURI}/{ver}/user/{tenantID}             |
+---------------+----------------------------------+--------+---------------------------------------------+
| User          | Delete an Admin API user         | DELETE | {baseURI}/{ver}/user/{tenantID}             |
+---------------+----------------------------------+--------+---------------------------------------------+
| User          | Add an Admin API user            | POST   | {baseURI}/{ver}/user                        |
+---------------+----------------------------------+--------+---------------------------------------------+
| User          | Modify an Admin API user         | PUT    | {baseURI}/{ver}/user/{tenantID}             |
+---------------+----------------------------------+--------+---------------------------------------------+

Get a list of devices
---------------------
This will be used to get either a whole list of devices or a filtered list given certain criteria.  A future expansion to this would be to add pagination support.

Request type
^^^^^^^^^^^^
GET

Path
^^^^
/2.0/devices

Access
^^^^^^
It should be available to both 'staff' and 'administrators'.

Response codes
^^^^^^^^^^^^^^
Success: 200

Failure: 400 (Bad request), 500 (Service error)

Query parameters supported
^^^^^^^^^^^^^^^^^^^^^^^^^^
* status - A specified status type to filter by such as 'OFFLINE', 'ONLINE' or 'ERROR'
* name - A specified device name (in a future version we could accept wildcards)
* ip - A specified device ip address (in a future version we could accept ranges)
* vip - A specified floating ip address (in a future version we could accept ranges)

Response Example
^^^^^^^^^^^^^^^^

.. code-block:: json

   {"devices": [
       {
           "id": 123,
           "name": "7908c1f2-1bce-11e3-bcd3-fa163e9790b4",
           "status": "OFFLINE",
           "ip": "15.125.30.123",
           "vip": null,
           "created": "2013-05-12 12:13:54",
           "updated": "2013-06-02 14:21:31"
       }
   ]}

Get a single device
-------------------
This will be used to get details of a single device specified by its ID.  This will contain additional information such as load balancers attached to a given device.

Request type
^^^^^^^^^^^^
GET

Path
^^^^
/2.0/devices/{id}

Access
^^^^^^
It should be available to both 'staff' and 'administrators'.

Response codes
^^^^^^^^^^^^^^
Success: 200

Failure: 400 (Bad request), 500 (Service error), 404 (Not found)

Query parameters supported
^^^^^^^^^^^^^^^^^^^^^^^^^^
Not applicable

Response Example
^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "id": 123,
       "name": "7908c1f2-1bce-11e3-bcd3-fa163e9790b4",
       "status": "ONLINE",
       "ip": "15.125.30.123",
       "vip": "15.125.50.45",
       "created": "2013-05-12 12:13:54",
       "updated": "2013-06-02 14:21:31",
       "loadBalancers": [
           {
               "id": 5263
           }
       ]
   }

Get a device version
--------------------
This will be used to send a DISCOVER gearman message to a given device's worker and get its version response.

Request type
^^^^^^^^^^^^
GET

Path
^^^^
/2.0/devices/{id}/discover

Access
^^^^^^
It should be available to both 'staff' and 'administrators'.

Response codes
^^^^^^^^^^^^^^
Success: 200

Failure: 400 (Bad request), 500 (Service error), 404 (Not found)

Query parameters supported
^^^^^^^^^^^^^^^^^^^^^^^^^^
Not applicable

Response Example
^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "id": 123,
       "version": "1.0",
       "release": "1.0.alpha.3.gca84083"
   }

Delete a device
---------------
This will be used to delete a device, if the device has load balancers attached these will be moved to a new device.  Typically this could be used for worker upgrades, going through each device rebuilding it using a a pool with newer workers.  If there are no load balancers attached it should just mark the device for deletion, in this scenario a 204 with empty body will be returned.

Request type
^^^^^^^^^^^^
DELETE

Path
^^^^
/2.0/devices/{id}

Access
^^^^^^
It should be available to 'administrators' only.

Response codes
^^^^^^^^^^^^^^
Success: 200 or 204

Failure: 400 (Bad request), 500 (Service error), 404 (Not found)

Query parameters supported
^^^^^^^^^^^^^^^^^^^^^^^^^^
Not applicable

Response Example
^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "oldId": 123,
       "newId": 148
   }

Get a list of LoadBalancers
---------------------------
This will be used to get a list of all load balancers or a filtered list using given criteria.  A future expansion to this would be to add pagination support.

Request type
^^^^^^^^^^^^
GET

Path
^^^^
/2.0/loadbalancers

Access
^^^^^^
It should be available to both 'staff' and 'administrators'.

Response codes
^^^^^^^^^^^^^^
Success: 200

Failure: 400 (Bad request), 500 (Service error)

Query parameters supported
^^^^^^^^^^^^^^^^^^^^^^^^^^
* status - A specified status type to filter by such as 'ACTIVE', 'DEGRADED' or 'ERROR'
* tenant - The tenant/project ID for a given customer
* name - A specified device name (in a future version we could accept wildcards)
* ip - A specified device ip address (in a future version we could accept ranges)
* vip - A specified floating ip address (in a future version we could accept ranges)

Response Example
^^^^^^^^^^^^^^^^

.. code-block:: json

   {"loadBalancers": [
       {
           "id": 4561,
           "name": "my load balancer",
           "status": "ACTIVE",
           "tenant": 8637027649,
           "vip": "15.125.30.123",
           "protocol": "HTTP",
           "algorithm": "ROUND_ROBIN",
           "port": 80,
           "created": "2013-05-12 12:13:54",
           "updated": "2013-06-02 14:21:31"
       }
   ]}

Get a single LoadBalancer
-------------------------
This will be used to get details of a single load balancer specified by its ID.  This will contain additional information such as nodes attached to the load balancer and which device is used.

Request type
^^^^^^^^^^^^
GET

Path
^^^^
/2.0/loadbalancers/{id}

Access
^^^^^^
It should be available to both 'staff' and 'administrators'.

Response codes
^^^^^^^^^^^^^^
Success: 200

Failure: 400 (Bad request), 500 (Service error), 404 (Not found)

Query parameters supported
^^^^^^^^^^^^^^^^^^^^^^^^^^
Not applicable

Response Example
^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "id": 4561,
       "name": "my load balancer",
       "status": "ACTIVE",
       "tenant": 8637027649,
       "vip": "15.125.30.123",
       "protocol": "HTTP",
       "algorithm": "ROUND_ROBIN",
       "port": 80,
       "device": 123,
       "created": "2013-05-12 12:13:54",
       "updated": "2013-06-02 14:21:31",
       "nodes": [
           {
               "ip": "15.185.23.157",
               "port": 80,
               "weight": 1,
               "enabled": true,
               "status": "ONLINE"
           }
       ],
       "monitor": {
           "type": "HTTP",
           "delay": "30",
           "timeout": "30",
           "attemptsBeforeDeactivation": "2",
           "path": "/healthcheck"
       }
   }

Delete a single LoadBalancer (NOT IMPLEMENTED!)
-----------------------------------------------
This will be used to delete a single load balancer in the same way a given user would.

Request type
^^^^^^^^^^^^
DELETE

Path
^^^^
/2.0/loadbalancers/{id}

Access
^^^^^^
It should be available to 'administrators' only.

Response codes
^^^^^^^^^^^^^^
Success: 204

Failure: 400 (Bad request), 500 (Service error), 404 (Not found)

Query parameters supported
^^^^^^^^^^^^^^^^^^^^^^^^^^
Not applicable

Get pool status
---------------
This is used to get an overview of the current status of the load balancer pool

Request type
^^^^^^^^^^^^
GET

Path
^^^^
/2.0/status/pool

Access
^^^^^^
It should be available to both 'staff' and 'administrators'.

Response codes
^^^^^^^^^^^^^^
Success: 200

Failure: 400 (Bad request), 500 (Service error)

Query parameters supported
^^^^^^^^^^^^^^^^^^^^^^^^^^
Not applicable

Response Example
^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "devices": {
           "used": 325,
           "available": 50,
           "error": 3,
           "pendingDelete": 2
       },
       "vips": {
           "used": 325,
           "available": 15,
           "bad" 2
       }
   }

Get counters
------------
This is used to get the current counters from the API server.  There is no reset for this at the moment so this is from the first installation of a version of the API supporting counters.

Request type
^^^^^^^^^^^^
GET

Path
^^^^
/2.0/status/counters

Access
^^^^^^
It should be available to both 'staff' and 'administrators'.

Response codes
^^^^^^^^^^^^^^
Success: 200

Failure: 400 (Bad request), 500 (Service error)

Response example
^^^^^^^^^^^^^^^^

.. code-block:: json

   [
       {
           "name": "loadbalancers_rebuild",
           "value": 10
       },
       {
           "name": "loadbalancers_error",
           "value": 0
       }
   ]

Get service status
------------------
This is used to get the health of vital service components.  It will initially test all MySQL and Gearman servers to see if they are online.

Request type
^^^^^^^^^^^^
GET

Path
^^^^
/2.0/status/service

Access
^^^^^^
It should be available to both 'staff' and 'administrators'.

Response codes
^^^^^^^^^^^^^^
Success: 200

Failure: 400 (Bad request), 500 (Service error)

Response example
^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "mysql": [
           {
               "ip": "15.185.14.125",
               "status": "ONLINE"
           }
       ],
       "gearman": [
           {
               "ip": "15.185.14.75",
               "status": "OFFLINE"
           }
       ]
   }

Get global service limits
-------------------------
This is used to get the defined global limits (executed per-tenant) of the service.

Request type
^^^^^^^^^^^^
GET

Path
^^^^
/2.0/status/limits

Access
^^^^^^
It should be available to both 'staff' and 'administrators'.

Response codes
^^^^^^^^^^^^^^
Success: 200

Failure: 400 (Bad request), 500 (Service error)

Response example
^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "maxLoadBalancerNameLength": 128,
       "maxVIPsPerLoadBalancer": 1,
       "maxNodesPerLoadBalancer": 50,
       "maxLoadBalancers": 20
   }

Change global service limits
----------------------------
This is used to modify the global limits of the service.  It can be used to modify maxLoadBalancerNameLength, maxVIPsPerLoadBalancer, maxNodesPerLoadBalancer and/or maxLoadBalancers.

Request type
^^^^^^^^^^^^
PUT

Path
^^^^
/2.0/status/limits

Access
^^^^^^
It should be available to 'administrators' only.

Request body example
^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "maxNodesPerLoadBalancer": 75
   }

Response codes
^^^^^^^^^^^^^^
Success: 204

Failure: 400 (Bad request), 500 (Service error)

List Admin API users
--------------------
This is used to get a list of users for the admin API with their access levels, USER (referred to as staff in this document) or ADMIN

Request type
^^^^^^^^^^^^
GET

Path
^^^^
/2.0/user

Access
^^^^^^
It should be available to 'administrators' only.

Response codes
^^^^^^^^^^^^^^
Success: 200

Failure: 400 (Bad request), 500 (Service error)

Response example
^^^^^^^^^^^^^^^^

.. code-block:: json

   [
       {
           "tenant": "123456",
           "level": "USER"
       },
       {
           "tenant": "654321",
           "level": "ADMIN"
       }
   ]

Get an Admin API user
---------------------
This is used to get a single user for the admin API with their access levels, USER (referred to as staff in this document) or ADMIN

Request type
^^^^^^^^^^^^
GET

Path
^^^^
/2.0/user/{tenantID}

Access
^^^^^^
It should be available to 'administrators' only.

Response codes
^^^^^^^^^^^^^^
Success: 200

Failure: 400 (Bad request), 500 (Service error)

Response example
^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "tenant": "123456",
       "level": "USER"
   }

Delete an Admin API user
------------------------
This is used to delete a single user for the admin API with their access levels, USER (referred to as staff in this document) or ADMIN

Request type
^^^^^^^^^^^^
DELETE

Path
^^^^
/2.0/user/{tenantID}

Access
^^^^^^
It should be available to 'administrators' only.

Response codes
^^^^^^^^^^^^^^
Success: 204

Failure: 400 (Bad request), 500 (Service error)

Add an Admin API user
---------------------
This is used to add a single user for the admin API with their access levels, USER (referred to as staff in this document) or ADMIN

Request type
^^^^^^^^^^^^
POST

Path
^^^^
/2.0/user

Access
^^^^^^
It should be available to 'administrators' only.

Request body example
^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "tenant": 654321,
       "level": "ADMIN"
   }

Response codes
^^^^^^^^^^^^^^
Success: 200

Failure: 400 (Bad request), 500 (Service error)

Modify an Admin API user
------------------------
This is used to modify a single user for the admin API with their access levels, USER (referred to as staff in this document) or ADMIN

Request type
^^^^^^^^^^^^
POST

Path
^^^^
/2.0/user/{tenantID}

Access
^^^^^^
It should be available to 'administrators' only.

Request body example
^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "level": "ADMIN"
   }

Response codes
^^^^^^^^^^^^^^
Success: 200

Failure: 400 (Bad request), 500 (Service error)
