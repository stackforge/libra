LBaaS Device API
================

Description
-----------

The LBaaS service provides two classes of APIs including a tenant facing
API and admin API. The admin API is designed for internal usage to allow
administration of the LBaaS service itself. As part of this, the *Device
API* allows for managing devices which are the actual load balancer
devices used by LBaaS.

API Overview
------------

The device API is not visible to tenants thus it is designed to operate
on its own HTTPS port which is configurable. The device API only
supports a JSON resource representation for reading and writing. The API
is designed as a RESTful API including support of CRUD operations for
creating, reading, updating and deleting devices.

Base URL and port
^^^^^^^^^^^^^^^^^

All device API calls run on the same TCP port and require HTTPS for
access. The specific HTTPS port and certificate are configurable by the
LBaaS service and will comply with the Cloud security requirements
including the certificate signing. The API is version'ed such that all
calls are prefixed with a version URI. For example,

``https://lbaas-service:8889/v1/devices/...``

would access the LBaaS system hosted on lbaas-service, using HTTPS on
port 8889 using version 1 of the API.

Exceptions
^^^^^^^^^^

As a RESTful service, the device API can return standard HTTP status
codes with each request including success and error codes mentioned
below. In the event a non 200 series status is returned, a JSON
formatted error body is provided with additional details. The format of
the JSON error body is as follows:

*Example of a bad request JSON error response body*

::

    {
       "message":"Bad Request",
       "details":"device name : lbaas-10.5.251.48 already exists",
       "code":400
    }

Base URI
^^^^^^^^

All LBaaS Device API calls have a common base URI defined as follows:

``<baseURI> = https://<lbaas-system-addr>:<lbaas-device-port>/v1``

-  *lbaas-system-addr* is the system name / address where the LBaaS API
   service is running.

-  *lbaas-device-port* is the TCP port in which the device service is
   listening for HTTPS REST requests.

-  */v1/devices* will prefix all REST calls.

Device Data Model
^^^^^^^^^^^^^^^^^

Device REST calls allow reading and writing device resources represented
in JSON. The data model for devices is defined as follows:

id
^^

*id* is an integer representing a unique id for the device. *id* is
created by the LBaaS service when devices are created. *id* is used to
reference devices as the REST collection id.

updated
^^^^^^^

*updated* is a text string representing the last time this device
resource was updated.

created
^^^^^^^

*created* is a text string representing when the device was created.

status
^^^^^^

*status* is a text string representing the status of the device as
reported by the device to the LBaaS service ( this is done through the
gearman client / worker interface ). Status values can be 'OFFLINE',
'ONLINE', 'ERROR'.

address
^^^^^^^

*address* is the IPv4 or IPV6 address of the device. This is the adress
which will be used as the loadbalancer's address used by the customer.
Note, this should be a Nova floating IP address for usage with HAProxy
on Nova.

name
^^^^

*name* is the name of the device which is used internally by LBaaS as
the gearman worker name. Each device name is specified by the pool
manager and must be unique for each device. The format of the name is
``lbaas-<version>-<id>`` where ``<version>`` is the gearman worker
version e.g. *v1* and ``<id>`` is a unique UUID for the name.

loadbalancer
^^^^^^^^^^^^

*loadbalancer* are references to logical loadbalancers who are using
this device. This is a list of one or more integers. An empty or zero
value denotes that this device is not used and is free. Note, if the
device is not in use, it has no customer loadbalancer config and is in a
'OFFLINE' state.

type
^^^^

*type* is a text string describing the type of device. Currently only
'HAProxy' is supported.

Example of a single device
^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    {
        "id":1,
        "updated":"Mon 2012.10.29 at 07:21:48 PM UTC",
        "created":"Mon 2012.10.29 at 07:21:48 PM UTC",  
        "status":"OFFLINE",
        "address":"15.185.96.125",
        "name":"lbaas-v1-067e6162-3b6f-4ae2-a171-2470b63dff00",
        "loadbalancer":0,
        "type":"HAProxy"
    }

Operations
==========

Get all Devices
---------------

Get all devices currently defined.

::

    GET <baseURI>/devices

Return Status
^^^^^^^^^^^^^

200 on success, 500 for internal error

Example
^^^^^^^

::

    curl -k https://15.185.107.220:8889/v1/devices

Response:

::

    {
        "devices":[
            {
                "id":1,
                "updated":"Mon 2012.10.29 at 07:21:48 PM UTC",
                "created":"Mon 2012.10.29 at 07:21:48 PM UTC",
                "status":"OFFLINE",
                "address":"15.185.96.125",
                "name":"lbaas-v1-067e6162-3b6f-4ae2-a171-2470b63dff00",
                "loadbalancer":0,
                "type":"HAProxy"
            }
        ]
    }

Get a Device
------------

Get a specific device.

::

    GET <baseURI>/devices/{deviceId}

Return Status
^^^^^^^^^^^^^

200 on success, 404 not found, 500 for internal error

Example
^^^^^^^

::

    curl -k https://15.185.107.220:8889/v1/devices/1

Response:

::

    {
        "id":1,
        "updated":"Mon 2012.10.29 at 07:21:48 PM UTC",
        "created":"Mon 2012.10.29 at 07:21:48 PM UTC",
        "status":"OFFLINE",
        "address":"15.185.96.125",
        "name":"lbaas-v1-067e6162-3b6f-4ae2-a171-2470b63dff00",
        "loadbalancer":0,
        "type":"HAProxy"
    }

Create a Device
---------------

Create a new device will register an already deployed device with the
LBaaS service. In order to do so, LBaaS will need to know its name and
address. Returned will be the new device including its *id*.

::

    POST <baseURI>/devices

Return Status
^^^^^^^^^^^^^

200 on success, 400 bad request, 500 for internal error

Request Body
^^^^^^^^^^^^

A JSON request body is required for this request.

::

    {
        "name": "lbaas-v1-067e6162-3b6f-4ae2-a171-2470b63dff00",
        "address": "15.185.96.125"
    }

Example
^^^^^^^

::

    curl -X POST -H "Content-type:application/json" --data-binary "@device.json" -k https://15.185.107.220:8889/v1/devices

Response:

::

    {
        "id":1,
        "updated":"Mon 2012.10.29 at 07:21:48 PM UTC",
        "created":"Mon 2012.10.29 at 07:21:48 PM UTC",
        "status":"OFFLINE",
        "address":"15.185.96.125",
        "name":"lbaas-v1-067e6162-3b6f-4ae2-a171-2470b63dff00",
        "loadbalancer":0,
        "type":"HAProxy"
    }

Delete a Device
---------------

Delete a device will delete a device from the LBaaS service. Note, this
call can be dangerous and effect a customers load balancer if it is in
use. *please use this call with extreme caution!*.

::

    DELETE <baseURI>/devices/{deviceId}

Return Status
^^^^^^^^^^^^^

204 on success, 400 bad request, 500 for internal error

Example
^^^^^^^

::

    curl -X DELETE -k https://15.185.107.220:8889/v1/devices/1

Update a Device
---------------

Update a device allows changing the address or name of a device. No
other fields can be changed and will be ignored.

::

    PUT <baseURI>/devices/{deviceId}

Return Status
^^^^^^^^^^^^^

200 on success, 400 bad request, 500 for internal error

Request Body
^^^^^^^^^^^^

A JSON request body is required for this request.

::

    {
        "name": "lbaas-v1-067e6162-3b6f-4ae2-a171-2470b63dff00",
        "address": "15.185.96.125"
    }

Example
^^^^^^^

::

    curl -X PUT -H "Content-type:application/json" --data-binary "@device.json" -k https://15.185.107.220:8889/v1/devices/1

Response:

::

    {
        "id":1,
        "updated":"Mon 2012.10.29 at 07:21:48 PM UTC",
        "created":"Mon 2012.10.29 at 07:21:48 PM UTC",
        "status":"OFFLINE",
        "address":"15.185.96.125",
        "name":"lbaas-v1-067e6162-3b6f-4ae2-a171-2470b63dff00",
        "loadbalancer":0,
        "type":"HAProxy"
    }

Get Usage of Devices
--------------------

This call allows obtaining usage summary information for all devices.

::

    GET <baseURI>/devices/usage

Return Status
^^^^^^^^^^^^^

200 on success, 500 for internal error

Example
^^^^^^^

::

    curl -k https://15.185.107.220:8889/v1/devices/usage

Response:

::

    {
        "total": 100,
        "free" : 50,
        "taken": 50
    }

