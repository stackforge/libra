.. api-lb:

=============
Load Balancer
=============


.. _api-lb-list:

Get List Of All Load Balancers
------------------------------

Operation
~~~~~~~~~

+-----------------+----------------------------------+----------+---------------------------------+
| Resource        | Operation                        | Method   | Path                            |
+=================+==================================+==========+=================================+
| Load Balancer   | Get list of all load balancers   | GET      | {baseURI}/{ver}/loadbalancers   |
+-----------------+----------------------------------+----------+---------------------------------+

Description
~~~~~~~~~~~

This operation provides a list of all load balancers configured and
associated with your account. This includes a summary of attributes for
each load balancer. In order to retrieve all the details for a load
balancer, an individual request for the load balancer must be made.

This operation returns the following attributes for each load balancer:

**id :** Unique identifier for the load balancer

**name :** Creator-assigned name for the load balancer

**algorithm :** Creator-specified algorithm for the load balancer

**protocol :** Creator-specified protocol for the load balancer

**port :** Creator-specified port for the load balancer

**status :** Current status, see section on load balancer status within
load balancer create

**created :** When the load balancer was created

**updated :** When the load balancer was last updated

Request Data
~~~~~~~~~~~~

None required.

Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

Request Body
~~~~~~~~~~~~~~~~~

None required.

Normal Response Code
~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 200                | OK            |
+--------------------+---------------+

Response Body
~~~~~~~~~~~~~~~~~~

The response body contains a list of load balancers for the tenant
making the request.

Error Response Codes
~~~~~~~~~~~~~~~~~~~~

+--------------------+----------------+
| HTTP Status Code   | Description    |
+====================+================+
| 400                | Bad Request    |
+--------------------+----------------+
| 401                | Unauthorized   |
+--------------------+----------------+
| 404                | Not Found      |
+--------------------+----------------+
| 405                | Not Allowed    |
+--------------------+----------------+
| 500                | LBaaS Fault    |
+--------------------+----------------+

Example
~~~~~~~

**Curl Request**

::

    curl -H "X-Auth-Token: TOKEN" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/loadbalancers

**Response**

::

    {
        "loadBalancers":[
            {
                "name":"lb-site1",
                "id":"71",
                "protocol":"HTTP",
                "port":"80",
                "algorithm":"LEAST_CONNECTIONS",
                "status":"ACTIVE",
                "created":"2010-11-30T03:23:42Z",
                "updated":"2010-11-30T03:23:44Z"
            },
            {
                "name":"lb-site2",
                "id":"166",
                "protocol":"TCP",
                "port":"9123",
                "algorithm":"ROUND_ROBIN",
                "status":"ACTIVE",
                "created":"2010-11-30T03:23:42Z",
                "updated":"2010-11-30T03:23:44Z"
            }
            ]
    }

.. _api-lb-status:

Get Load Balancer Details
-------------------------

Operation
~~~~~~~~~

+-----------------+--------------------------------+----------+--------------------------------------------------+
| Resource        | Operation                      | Method   | Path                                             |
+=================+================================+==========+==================================================+
| Load Balancer   | Get a specific load balancer   | GET      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}   |
+-----------------+--------------------------------+----------+--------------------------------------------------+

Description
~~~~~~~~~~~

This operation provides detailed description for a specific load
balancer configured and associated with your account. This operation is
not capable of returning details for a load balancer which has been
deleted. Details include load balancer virtual IP and node information.

Request Data
~~~~~~~~~~~~

None required.

Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

Request Body
~~~~~~~~~~~~

None required.

Normal Response Code
~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 200                | OK            |
+--------------------+---------------+

Response Body
~~~~~~~~~~~~~

The response body contains the load balancer requested or 404, if not
found.

Error Response Codes
~~~~~~~~~~~~~~~~~~~~

+--------------------+----------------+
| HTTP Status Code   | Description    |
+====================+================+
| 400                | Bad Request    |
+--------------------+----------------+
| 401                | Unauthorized   |
+--------------------+----------------+
| 404                | Not Found      |
+--------------------+----------------+
| 405                | Not Allowed    |
+--------------------+----------------+
| 500                | LBaaS Fault    |
+--------------------+----------------+

Example
~~~~~~~

**Curl Request**

::

    curl -H "X-Auth-Token: TOKEN" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/loadbalancers/2000

**Response**

::

    {
            "id": "2000",
            "name":"sample-loadbalancer",
            "protocol":"HTTP",
            "port": "80",
            "algorithm":"ROUND_ROBIN",
            "status":"ACTIVE",
            "created":"2010-11-30T03:23:42Z",
            "updated":"2010-11-30T03:23:44Z",
            "virtualIps":[
                        {
                            "id": "1000",
                            "address":"192.168.1.1",
                            "type":"PUBLIC",
                            "ipVersion":"IPV4"
                        }
                 ],
            "nodes":     [
                      {
                            "id": "1041",
                            "address":"10.1.1.1",
                            "port": "80",
                            "condition":"ENABLED",
                            "status":"ONLINE"
                       },
                       {
                            "id": "1411",
                            "address":"10.1.1.2",
                            "port": "80",
                            "condition":"ENABLED",
                            "status":"ONLINE"
                       }
                  ],
    }

.. _api-lb-create:

Create a New Load Balancer
--------------------------

Operation
~~~~~~~~~

+-----------------+------------------------------+----------+---------------------------------+
| Resource        | Operation                    | Method   | Path                            |
+=================+==============================+==========+=================================+
| Load Balancer   | Create a new load balancer   | POST     | {baseURI}/{ver}/loadbalancers   |
+-----------------+------------------------------+----------+---------------------------------+

Description
~~~~~~~~~~~

This operation provisions a new load balancer based on the configuration
defined in the request object. Once the request is validated and
progress has started on the provisioning process, a response object will
be returned. The object will contain a unique identifier and status of
the request.

If the status returned is set to 'BUILD', then using the identifier of
the load balancer, the caller can check on the progress of the creation
operation by performing a GET on loadbalancers/{loadbalancerId}. When
the status of the load balancer returned changes to 'ACTIVE', then the
load balancer has been successfully provisioned and is now operational.

**Load Balancer Status Values**

+-------------------+----------------------------------------------------------------+
| Status Name       | Description                                                    |
+===================+================================================================+
| BUILD             | Load balancer is in a building state and not yet operational   |
+-------------------+----------------------------------------------------------------+
| ACTIVE            | Load balancer is in an operational state                       |
+-------------------+----------------------------------------------------------------+
| PENDING\_UPDATE   | Load balancer is in the process of an update                   |
+-------------------+----------------------------------------------------------------+
| ERROR             | Load balancer is in an error state and not operational         |
+-------------------+----------------------------------------------------------------+

The caller of this operation must specify at least the following
attributes of the load balancer:

\*name

\*at least one node

If the request cannot be fulfilled due to insufficient or invalid data,
an HTTP 400 (Bad Request) error response will be returned with
information regarding the nature of the failure in the body of the
response. Failures in the validation process are non-recoverable and
require the caller to correct the cause of the failure and POST the
request again.

By default, the system will create a load balancer with protocol set to
HTTP, port set to 80 (or 443 if protocol is TCP), and assign a public
IPV4 address to the load balancer. The default algorithm used is set to
ROUND\_ROBIN.

A load balancer name has a max length that can be determined by querying
limits.

Users may configure all documented features of the load balancer at
creation time by simply providing the additional elements or attributes
in the request. This document provides an overview of all the features
the load balancing service supports.

If you have at least one load balancer, you may create subsequent load
balancers that share a single virtual IP by issuing a POST and supplying
a virtual IP ID instead of a type. Additionally, this feature is highly
desirable if you wish to load balance both an unsecured and secure
protocol using one IP address. For example, this method makes it
possible to use the same load balancing configuration to support an HTTP
and an TCP load balancer. Load balancers sharing a virtual IP must
utilize a unique port.

Request Data
~~~~~~~~~~~~

The caller is required to provide a request data with the POST which
includes the appropriate information to create a new load balancer.

Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **X-Auth-Token**
- **Accept: application/json**
- **Content-Type: application/json**

Request Body
~~~~~~~~~~~~

The request body must follow the correct format for new load balancer
creation, examples....

**Request body example to create a load balancer with two nodes**

::

    {
            "name": "a-new-loadbalancer",
            "nodes":      [
                        {
                            "address": "10.1.1.1",
                            "port": "80"
                        },
                        {
                            "address": "10.1.1.2",
                            "port": "81"
                        }
                ]
    }

**Request body example to create a load balancer using existing load
balancer virtual IP**

::

    {
        "name":"a-new-loadbalancer",
        "port":"83",
        "protocol":"HTTP",
        "virtualIps": [
                   {
                      "id":"39"
                   }
                 ],
        "nodes":      [
                   {
                      "address":"10.1.1.1",
                      "port":"80",
                      "condition":"ENABLED"
                   }
                 ]
    }

Normal Response Code
~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 202                | Accepted      |
+--------------------+---------------+

Response Body
~~~~~~~~~~~~~

The response body contains the load balancer requested or appropriate
error.

**Create Load Balancer (Required Attributes with Shared IP) Response:
JSON**

::

    {
            "name": "a-new-loadbalancer",
            "id": "144",
            "protocol": "HTTP",
            "port": "83",
            "algorithm": "ROUND_ROBIN",
            "status": "BUILD",
            "created": "2011-04-13T14:18:07Z",
            "updated":"2011-04-13T14:18:07Z",
            "virtualIps": [
                    {
                        "address": "3ffe:1900:4545:3:200:f8ff:fe21:67cf",
                        "id": "39",
                        "type": "PUBLIC",
                        "ipVersion": "IPV6"
                    }
                  ],
            "nodes":      [
                    {
                        "address": "10.1.1.1",
                        "id": "653",
                        "port": "80",
                        "status": "ONLINE",
                        "condition": "ENABLED"
                    }
                  ]
    }

Error Response Codes
~~~~~~~~~~~~~~~~~~~~

+--------------------+-----------------------+
| HTTP Status Code   | Description           |
+====================+=======================+
| 400                | Bad Request           |
+--------------------+-----------------------+
| 401                | Unauthorized          |
+--------------------+-----------------------+
| 404                | Not Found             |
+--------------------+-----------------------+
| 405                | Not Allowed           |
+--------------------+-----------------------+
| 413                | Over Limit            |
+--------------------+-----------------------+
| 500                | LBaaS Fault           |
+--------------------+-----------------------+
| 503                | Service Unavailable   |
+--------------------+-----------------------+

Example
~~~~~~~

**Contents of Request file lb.json**

::

    {
        "name": "lb #1",
        "protocol":"tcp",
            "nodes":      [
                    {
                        "address": "15.185.229.153",
                        "port": "443"
                    },
                   {
                        "address": "15.185.226.163",
                        "port": "443"
                    },
                   ],
    }

**Curl Request**

::

    curl -X POST -H "X-Auth-Token: TOKEN" --data-binary "@lb.json" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/loadbalancers

**Response**

::

    {
        "port":"443",
        "id":"10",
        "protocol":"tcp",
        "updated":"2013-02-10T18:20Z",
        "created":"2013-02-10T18:20Z",
        "status":"BUILD",
        "nodes":[
            {
                "port":"443",
                "id":"19",
                "condition":"ENABLED",
                "status":"ONLINE",
                "address":"15.185.229.153"
            },
            {
                "port":"443",
                "id":"20",
                "condition":"ENABLED",
                "status":"ONLINE",
                "address":"15.185.226.163"
            }
        ],
        "name":"lb #1",
        "virtualIps":[
            {
                "id":"5",
                "address":"15.185.96.125",
                "ipVersion":"IPV_4",
                "type":"PUBLIC"
            }
        ],
        "algorithm":"ROUND_ROBIN"
    }

.. _api-lb-modify:

Update an Existing Load Balancer
--------------------------------

Operation
~~~~~~~~~

+-----------------+-----------------------------------+----------+--------------------------------------------------+
| Resource        | Operation                         | Method   | Path                                             |
+=================+===================================+==========+==================================================+
| Load Balancer   | Update load balancer attributes   | PUT      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}   |
+-----------------+-----------------------------------+----------+--------------------------------------------------+

Description
~~~~~~~~~~~

This operation updates the attributes of the specified load balancer.
Upon successful validation of the request, the service will return a 202
(Accepted) response code. A caller should check that the load balancer
status is ACTIVE to confirm that the update has taken effect. If the
load balancer status is 'PENDING\_UPDATE' then the caller can poll the
load balancer with its ID (using a GET operation) to wait for the
changes to be applied and the load balancer to return to an ACTIVE
status.

This operation allows the caller to change one or more of the following
attributes:

\*name

\*algorithm

This operation does not return a response body.

.. note::
    The load balancer ID, status, port and protocol are immutable
    attributes and cannot be modified by the caller. Supplying an
    unsupported attribute will result in a 400 (badRequest) fault.

Request Data
~~~~~~~~~~~~

Load balancer body with attributes to be updated.

Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

Request Body
~~~~~~~~~~~~

**Example**

::

    {
        "name": "newname-loadbalancer",
        "algorithm": "LEAST_CONNECTIONS"
    }

Normal Response Code
~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 202                | Accepted      |
+--------------------+---------------+

Response Body
~~~~~~~~~~~~~

None.

Error Response Codes
~~~~~~~~~~~~~~~~~~~~

+--------------------+----------------+
| HTTP Status Code   | Description    |
+====================+================+
| 400                | Bad Request    |
+--------------------+----------------+
| 401                | Unauthorized   |
+--------------------+----------------+
| 404                | Not Found      |
+--------------------+----------------+
| 405                | Not Allowed    |
+--------------------+----------------+
| 500                | LBaaS Fault    |
+--------------------+----------------+

Example
~~~~~~~

**Contents of Request file lb.json**

::

    {
        "name": "newname-loadbalancer",
        "algorithm": "LEAST_CONNECTIONS"
    }

**Curl Request**

::

    curl -X PUT -H "X-Auth-Token: TOKEN" --data-binary "@lb.json" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/loadbalancers/100

**Response**

status with no response body.

.. _api-lb-delete:

Delete Load Balancer
--------------------

Operation
~~~~~~~~~

+-----------------+------------------------------------+----------+--------------------------------------------------+
| Resource        | Operation                          | Method   | Path                                             |
+=================+====================================+==========+==================================================+
| Load Balancer   | Delete an existing load balancer   | DELETE   | {baseURI}/{ver}/loadbalancers/{loadbalancerId}   |
+-----------------+------------------------------------+----------+--------------------------------------------------+

Description
~~~~~~~~~~~

Delete load balancer removes the specified load balancer and its
associated configuration from the account. Any and all configuration
data is immediately purged and is not recoverable.

This operation does not require a request body.

Request Data
~~~~~~~~~~~~

None required.

Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

Request Body
~~~~~~~~~~~~

None required.

Normal Response Code
~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 202                | Accepted      |
+--------------------+---------------+

Response Body
~~~~~~~~~~~~~

None.

Error Response Codes
~~~~~~~~~~~~~~~~~~~~

+--------------------+----------------+
| HTTP Status Code   | Description    |
+====================+================+
| 400                | Bad Request    |
+--------------------+----------------+
| 401                | Unauthorized   |
+--------------------+----------------+
| 404                | Not Found      |
+--------------------+----------------+
| 405                | Not Allowed    |
+--------------------+----------------+
| 500                | LBaaS Fault    |
+--------------------+----------------+

Example
~~~~~~~

**Curl Example**

::

    curl -X DELETE -H "X-Auth-Token: TOKEN" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/loadbalancers/100

**Response**

status with no response body.