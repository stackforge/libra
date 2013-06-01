Load Balancer as a Service (LBaaS) API Specification
====================================================

**Date:** February 8, 2013

**Document Version:** 0.6

1. Overview
-----------

This guide is intended for software developers who wish to create
applications using the Load Balancer as a Service (LBaaS) set
of APIs. It assumes the reader has a general understanding of cloud
APIs, load balancing concepts, RESTful web services, HTTP/1.1
conventions and JSON serialization formats. The LBaaS set of APIs
utilize and take advantage of a variety of Openstack cloud API patterns
which are described in detail.

1.1 API Maturity Level
~~~~~~~~~~~~~~~~~~~~~~

This API definition represents the Load Balancer as a Service
in Beta release form. Functionality represented within this
specification is supported. The LBaaS API defined within this
specification represents version 1.1 of LBaaS.

**Maturity Level**: *Experimental*

**Version API Status**: *BETA*

2. Architecture View
--------------------

2.1 Overview
~~~~~~~~~~~~

The Load Balancer as a Service (LBaaS) is a set of APIs that
provide a RESTful interface for the creation and management of load
balancers in the cloud. Load balancers created can be used for a variety
of purposes including load balancers for your external cloud hosted
services as well as internal load balancing needs. The load balancing
solution is meant to provide both load balancing and high availability
in an industry standard manner. The LBaaS APIs defined are integrated
within the API ecosystem including integration with the 
identity management system, billing and monitoring systems.

2.2 Conceptual/Logical Architecture View
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use the Load Balancers API effectively, you should
understand several key concepts.

2.2.1 Load Balancer
^^^^^^^^^^^^^^^^^^^

A load balancer is a logical device. It is used to distribute workloads
between multiple back-end systems or services called 'nodes', based on
the criteria defined as part of its configuration.

2.2.2 Virtual IP
^^^^^^^^^^^^^^^^

A virtual IP is an Internet Protocol (IP) address configured on the load
balancer for use by clients connecting to a service that is load
balanced. Incoming connections and requests are distributed to back-end
nodes based on the configuration of the load balancer.

2.2.3 Node
^^^^^^^^^^

A node is a back-end device providing a service on a specified IP and
port.

The nodes defined by the load balancer are responsible for servicing the
requests received through the load balancers virtual IP. By default, the
load balancer employs a basic health check that ensures the node is
listening on its defined port. The node is checked at the time of
addition and at regular intervals as defined by the load balancer health
check configuration. If a back-end node is not listening on its port or
does not meet the conditions of the defined active health check for the
load balancer, then the loadbalancer will not forward connections or
requests to it and its status will be listed as OFFLINE. Only nodes that
are in an ONLINE status will receive and be able to service traffic from
the load balancer.

2.3 Infrastructure Architecture View
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

LBaaS fits into the ecosystem of APIs by utilizing the common
authentication mechanisms as any other services. In order to
use LBaaS, a user account must have activated "Load Balancer" service.
All API calls require require a valid authentication token.

3. Account-level View
---------------------

Once the account is activated, the LBaaS service will show up
in the service catelog returned during user login. In addition, LBaaS
endpoints to be used will also be presented. Availability zone
information may vary based on region.

3.1 Service Catalog
~~~~~~~~~~~~~~~~~~~

Once user authenticates using REST API, a service
catalog will list the availability of the LBaaS service, roles and
endpoints for the region you have logged into and in which you are
activated for.

*The following is an example of LBaaS service information within the
service catalog including roles and endpoints:*

::

     "user": {
        "id": "59267322167978",
        "name": "lbaas_user",
        "roles": [
          {
            "id": "83241756956007",
            "serviceId": "220",
            "name": "lbaas-user",
            "tenantId": "11223344556677"
          },
          {
            "id": "00000000004024",
            "serviceId": "140",
            "name": "user",
            "tenantId": "11223344556677"
          },
          {
            "id": "00000000004013",
            "serviceId": "130",
            "name": "block-admin",
            "tenantId": "11223344556677"
          }
        ]
      },
      "serviceCatalog": [
        {
          "name": "Identity",
          "type": "identity",
          "endpoints": [{
            "publicURL": "https:\/\/usa.region-b.geo-1.identity.hpcloudsvc.com:35357\/v2.0\/",
            "region": "region-b.geo-1",
            "versionId": "2.0",
            "versionInfo": "https:\/\/usa.region-b.geo-1.identity-internal.hpcloudsvc.com:35357\/v2.0\/"
          }]
        },
        {
          "name": "Load Balancer",
          "type": "hpext:lbaas",
          "endpoints": [{
            "tenantId": "11223344556677",
            "publicURL": "https:\/\/usa.region-b.geo-1.lbaas.hpcloudsvc.com\/v1.1",
            "publicURL2": "",
            "region": "region-b.geo-1",
            "versionId": "1.1",
            "versionInfo": "https:\/\/usa.region-b.geo-1.lbaas.hpcloudsvc.com\/v1.1",
            "versionList": "https:\/\/usa.region-b.geo-1.lbaas.hpcloudsvc.com"
          }]
        }
    ]

4. General API Information
--------------------------

This section describes operations and guidelines that are common to all
LBaaS APIs.

4.1 Authentication
~~~~~~~~~~~~~~~~~~

The LBaaS API uses standard defined by OpenStack Keystone project and
used by the for authentication. Please refer to the
identity management system for more details on all authentication
methods currently supported.

4.2 Service Access/Endpoints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As shown in the example above, logging into your region will provide you
with the appropriate LBaaS endpoints to use. In addition, all supported
versions are published within the service catalog. A client may chose to
use any LBaaS API version listed.

4.3 Request/Response Types
~~~~~~~~~~~~~~~~~~~~~~~~~~

The LBaaS API currently only supports JSON data serialization formats
for request and response bodies. The request format is specified using
the 'Content-Type' header and is required for operations that have a
request body. The response format should be specified in requests using
the 'Accept'header. If no response format is specified, JSON is the
default.

4.4 Persistent Connections
~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, the API supports persistent connections via HTTP/1.1
'keep-alive's. All connections will be kept alive unless the connection
header is set to close. In adherence with the IETF HTTP RFCs, the server
may close the connection at any time and clients should not rely on this
behavior.

4.5 Paginated Collections
~~~~~~~~~~~~~~~~~~~~~~~~~

Some LBaaS APIs have the capability to return collections as a list of
many resources. To reduce load on the service, list operations will
return a maximum of 100 items at a time. To navigate the collection,
Openstack style 'limit' and 'marker' query parameters are utilized. For
example, '?limit=50&marker=1' can be set in the URI. If a marker beyond
the end of a list is given, an empty list is returned.

4.6 Absolute Limits
~~~~~~~~~~~~~~~~~~~

Absolute limits are limits which prohibit a user from creating too many
LBaaS resources. For example, 'maxNodesPerLoadbalancer' identifies the
total number of nodes that may be associated with a given load balancer.
Limits for a specific tenant may be queried for using the 'GET /limits'
API. This will return the limit values which apply to the tenant who
made the request.

+-----------------------------+------------------------------------------------------------+
| Limited Resource            | Description                                                |
+=============================+============================================================+
| maxLoadBalancers            | Maximum number of load balancers allowed for this tenant   |
+-----------------------------+------------------------------------------------------------+
| maxNodesPerLoadBalancer     | Maximum number of nodes allowed for each load balancer     |
+-----------------------------+------------------------------------------------------------+
| maxLoadBalancerNameLength   | Maximum length allowed for a load balancer name            |
+-----------------------------+------------------------------------------------------------+
| maxVIPsPerLoadBalancer      | Maximum number of Virtual IPs for each load balancer       |
+-----------------------------+------------------------------------------------------------+

4.7 Faults
~~~~~~~~~~

When issuing a LBaaS API request, it is possible that an error can
occur. In these cases, the system will return an HTTP error response
code denoting the type of error and a LBaaS response body with
additional details regarding the error. Specific HTTP status codes
possible are listed in each API definition.

*The following JSON message represents the JSON response body used for
all faults:*

::

    {
       "message":"Description of fault",
       "details":"Details of fault",
       "code": HTTP standard error status
    }

4.8 Specifying Tenant IDs
~~~~~~~~~~~~~~~~~~~~~~~~~

Tenant identifiers with LBaaS API URIs are not required. The tenant
identifier is derived from the Openstack Keystone authentication token
provided with each API call. This simplifies the REST URIs to only
include the base URI and the resource. The tenant identifier is derived
from the authentication token which is provided wi the API call. All
LBaaS calls behave in this manner.

5. LBaaS API Resources and Methods
----------------------------------

The following is a summary of all supported LBaaS API resources and
methods. Each resource and method is defined in detail in the subsequent
sections.

**Derived resource identifiers:**

**{baseURI}** is the endpoint URI returned in the service catalog upon
logging in including the protocol, endpoint and base URI.

**{ver}** is the specific version URI returned as part of the service
catalog.

**{loadbalancerId}** is the unique identifier for a load balancer
returned by the LBaaS service.

**{nodeId}** is the unique identifier for a load balancer node returned
by the LBaaS service.

5.1 LBaaS API Summary Table
~~~~~~~~~~~~~~~~~~~~~~~~~~~

+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Resource        | Operation                           | Method   | Path                                                            |
+=================+=====================================+==========+=================================================================+
| Versions        | Get list of all API versions        | GET      | {baseURI}/                                                      |
+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Versions        | Get specific API version            | GET      | {baseURI}/{ver}                                                 |
+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Limits          | Get list of LBaaS limits            | GET      | {baseURI}/{ver}/limits                                          |
+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Protocols       | Get list of supported protocols     | GET      | {baseURI}/{ver}/protocols                                       |
+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Algorithms      | Get list of supported algorithms    | GET      | {baseURI}/{ver}/algorithms                                      |
+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Load Balancer   | Get list of all load balancers      | GET      | {baseURI}/{ver}/loadbalancers                                   |
+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Load Balancer   | Get load balancer details           | GET      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}                  |
+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Load Balancer   | Create a new load balancer          | POST     | {baseURI}/{ver}/loadbalancers                                   |
+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Load Balancer   | Update load balancer attributes     | PUT      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}                  |
+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Load Balancer   | Delete an existing load balancer    | DELETE   | {baseURI}/{ver}/loadbalancers/{loadbalancerId}                  |
+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Node            | Get list of load balancer nodes     | GET      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/nodes            |
+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Node            | Get a specific load balancer node   | GET      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/nodes/{nodeId}   |
+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Node            | Create a new load balancer node     | POST     | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/nodes            |
+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Node            | Update a load balancer node         | PUT      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/nodes/{nodeId}   |
+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Node            | Delete a load balancer node         | DELETE   | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/nodes/{nodeId}   |
+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Virtual IP      | Get list of virtual IPs             | GET      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/virtualips       |
+-----------------+-------------------------------------+----------+-----------------------------------------------------------------+

5.2 Common Request Headers
~~~~~~~~~~~~~~~~~~~~~~~~~~

*HTTP standard request headers*

**Accept** - Internet media types that are acceptable in the response.
LBaaS API supports the media type 'application/json'.

**Content-Length** - The length of the request body in octets (8-bit
bytes).

**Content-Type** - The Internet media type of the request body. Used
with POST and PUT requests. LBaaS API supports
'application/json'.

*Non-standard request headers*

**X-Auth-Token** - authorization token.

*Example*

::

    GET /v1.0/loadbalancers HTTP/1.1
    Host: system.hpcloudsvc.com
    Content-Type: application/json
    Accept: application/json
    X-Auth-Token: TOKEN
    Content-Length: 85

5.3 Common Response Headers
~~~~~~~~~~~~~~~~~~~~~~~~~~~

*HTTP standard response headers*

**Content-Type** - Internet media type of the response body.

**Date** - The date and time that the response was sent.

*Example*

::

    HTTP/1.1 200 OK
    Content-Length: 1135
    Content-Type: application/json; charset=UTF-8
    Date: Tue, 30 Oct 2012 16:22:35 GMT

6. Get a List of All LBaaS API Versions Supported
-------------------------------------------------

6.1 Operation
~~~~~~~~~~~~~

+------------+--------------------------------+----------+--------------+
| Resource   | Operation                      | Method   | Path         |
+============+================================+==========+==============+
| Versions   | Get list of all API versions   | GET      | {baseURI}/   |
+------------+--------------------------------+----------+--------------+

6.2 Description
~~~~~~~~~~~~~~~

This method allows querying the LBaaS service for all supported versions
it supports. This method is also advertised within the Keystone service
catalog which is presented upon user login. All versions listed can be
used for LBaaS.

6.3 Request Data
~~~~~~~~~~~~~~~~

None required.

6.4 Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

6.5 Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

6.6 Request Body
~~~~~~~~~~~~~~~~

None required.

6.7 Normal Response Code
~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 200                | OK            |
+--------------------+---------------+

6.8 Response Body
~~~~~~~~~~~~~~~~~

The response body contains a list of all supported versions of LBaaS.

6.9 Error Response Codes
~~~~~~~~~~~~~~~~~~~~~~~~

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

6.10 Example
~~~~~~~~~~~~

**Curl Request**

::

    curl -H "X-Auth-Token: TOKEN" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com

**Response**

::

    {
        "versions": [
            {
                "id": "v1.1", 
                "links": [
                    {
                        "href": "http://api-docs.hpcloud.com", 
                        "rel": "self"
                    }
                ], 
                "status": "CURRENT", 
                "updated": "2012-12-18T18:30:02.25Z"
            }
        ]
    }

7. Get Specific LBaaS API Version Information
---------------------------------------------

7.1 Operation
~~~~~~~~~~~~~

+------------+----------------------------+----------+-------------------+
| Resource   | Operation                  | Method   | Path              |
+============+============================+==========+===================+
| Versions   | Get specific API version   | GET      | {baseURI}/{ver}   |
+------------+----------------------------+----------+-------------------+

7.2 Description
~~~~~~~~~~~~~~~

This method allows querying the LBaaS service for information regarding
a specific version of the LBaaS API. This method is also advertised
within the Keystone service catalog which is presented upon user login.

7.3 Request Data
~~~~~~~~~~~~~~~~

None required.

7.4 Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

7.5 Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

7.6 Request Body
~~~~~~~~~~~~~~~~

None required.

7.7 Normal Response Code
~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 200                | OK            |
+--------------------+---------------+

7.8 Response Body
~~~~~~~~~~~~~~~~~

The response body contains information regarding a specific LBaaS API
version.

7.9 Error Response Codes
~~~~~~~~~~~~~~~~~~~~~~~~

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

7.10 Example
~~~~~~~~~~~~

**Curl Request**

::

    curl -H "X-Auth-Token: TOKEN" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1 

**Response**

::

    {
            "version": {
            "id": "v1.1", 
            "links": [
                {
                    "href": "http://api-docs.hpcloud.com", 
                    "rel": "self"
                }
            ], 
            "media-types": [
                {
                    "base": "application/json"
                }
            ], 
            "status": "CURRENT", 
            "updated": "2012-12-18T18:30:02.25Z"
            }
    }

8. Get List of LBaaS API Limits
-------------------------------

8.1 Operation
~~~~~~~~~~~~~

+------------+----------------------------+----------+--------------------------+
| Resource   | Operation                  | Method   | Path                     |
+============+============================+==========+==========================+
| Limits     | Get list of LBaaS limits   | GET      | {baseURI}/{ver}/limits   |
+------------+----------------------------+----------+--------------------------+

8.2 Description
~~~~~~~~~~~~~~~

This method allows querying the LBaaS service for a list of API limits
which apply on a tenant basis. Each tenant may not utilize LBaaS API
resources exceeding these limits and will receive and over limit error
if attempted (413).

+-----------------------------+------------------------------------------------------------+
| Returned Limit Name         | Value                                                      |
+=============================+============================================================+
| maxLoadBalancers            | Maximum number of load balancers allowed for this tenant   |
+-----------------------------+------------------------------------------------------------+
| maxNodesPerLoadBalancer     | Maximum number of nodes allowed for each load balancer     |
+-----------------------------+------------------------------------------------------------+
| maxLoadBalancerNameLength   | Maximum length allowed for a load balancer name            |
+-----------------------------+------------------------------------------------------------+
| maxVIPsPerLoadBalancer      | Maximum number of Virtual IPs for each load balancer       |
+-----------------------------+------------------------------------------------------------+

8.3 Request Data
~~~~~~~~~~~~~~~~

None required.

8.4 Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

8.5 Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

8.6 Request Body
~~~~~~~~~~~~~~~~

None required.

8.7 Normal Response Code
~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 200                | OK            |
+--------------------+---------------+

8.8 Response Body
~~~~~~~~~~~~~~~~~

The response body contains information regarding limits imposed for the
tenant making the request.

8.9 Error Response Codes
~~~~~~~~~~~~~~~~~~~~~~~~

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

8.10 Example
~~~~~~~~~~~~

**Curl Request**

::

    curl -H "X-Auth-Token: TOKEN" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/limits 

**Response**

::

    {
    "limits": {
            "absolute": {
                    "values": {
                        "maxLoadBalancerNameLength": 128, 
                        "maxLoadBalancers": 20, 
                        "maxNodesPerLoadBalancer": 5, 
                        "maxVIPsPerLoadBalancer": 1
                        }
                }
            }
    }

9. Get List Of Supported LBaaS Protocols
----------------------------------------

9.1 Operation
~~~~~~~~~~~~~

+-------------+-----------------------------------+----------+-----------------------------+
| Resource    | Operation                         | Method   | Path                        |
+=============+===================================+==========+=============================+
| Protocols   | Get list of supported protocols   | GET      | {baseURI}/{ver}/protocols   |
+-------------+-----------------------------------+----------+-----------------------------+

9.2 Description
~~~~~~~~~~~~~~~

All load balancers must be configured with the protocol of the service
which is being load balanced. The protocol selection should be based on
the protocol of the back-end nodes. The current specification supports
HTTP, HTTPS and TCP services.

When configuring an HTTP or HTTPS load balancer, the default port for
the given protocol will be selected unless otherwise specified. For TCP
load balancers, the port attribute must be provided.

9.3 Request Data
~~~~~~~~~~~~~~~~

None required.

9.4 Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

9.5 Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

9.6 Request Body
~~~~~~~~~~~~~~~~

None required.

9.7 Normal Response Code
~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 200                | OK            |
+--------------------+---------------+

9.8 Response Body
~~~~~~~~~~~~~~~~~

The response body contains the currently supported protocols and port
numbers.

9.9 Error Response Codes
~~~~~~~~~~~~~~~~~~~~~~~~

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

9.10 Example
~~~~~~~~~~~~

**Curl Request**

::

    curl -H "X-Auth-Token: TOKEN" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/protocols 

**Response**

::

    {
        "protocols": [
        {   
                    "name": "HTTP", 
                    "port": 80
            }, 
            {
                    "name": "TCP", 
                    "port": 443
            }
            ]
    }

10. Get List Of Supported LBaaS Algorithms
------------------------------------------

10.1 Operation
~~~~~~~~~~~~~~

+--------------+------------------------------------+----------+------------------------------+
| Resource     | Operation                          | Method   | Path                         |
+==============+====================================+==========+==============================+
| Algorithms   | Get list of supported algorithms   | GET      | {baseURI}/{ver}/algorithms   |
+--------------+------------------------------------+----------+------------------------------+

10.2 Description
~~~~~~~~~~~~~~~~

All load balancers utilize an algorithm that defines how traffic should
be directed between back end nodes. The default algorithm for newly
created load balancers is ROUND\_ROBIN, which can be overridden at
creation time or changed after the load balancer has been initially
provisioned.

The algorithm name is to be constant within a major revision of the load
balancing API, though new algorithms may be created with a unique
algorithm name within a given major revision of this API.

**Supported Algorithms**

+----------------------+-------------------------------------------------------------------------+
| Name                 | Description                                                             |
+======================+=========================================================================+
| LEAST\_CONNECTIONS   | The node with the lowest number of connections will receive requests.   |
+----------------------+-------------------------------------------------------------------------+
| ROUND\_ROBIN         | Connections are routed to each of the back-end servers in turn.         |
+----------------------+-------------------------------------------------------------------------+

10.3 Request Data
~~~~~~~~~~~~~~~~~

None required.

10.4 Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

10.5 Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

10.6 Request Body
~~~~~~~~~~~~~~~~~

None required.

10.7 Normal Response Code
~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 200                | OK            |
+--------------------+---------------+

10.8 Response Body
~~~~~~~~~~~~~~~~~~

The response body contains the currently supported algorithms.

10.9 Error Response Codes
~~~~~~~~~~~~~~~~~~~~~~~~~

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

10.10 Example
~~~~~~~~~~~~~

**Curl Request**

::

    curl -H "X-Auth-Token: TOKEN" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/algorithms 

**Response**

::

    {
            "algorithms": [
                {
                        "name": "ROUND_ROBIN"
                }, 
                {
                        "name": "LEAST_CONNECTIONS"
                }
            ]
    }

11. Get List Of All Load Balancers
----------------------------------

11.1 Operation
~~~~~~~~~~~~~~

+-----------------+----------------------------------+----------+---------------------------------+
| Resource        | Operation                        | Method   | Path                            |
+=================+==================================+==========+=================================+
| Load Balancer   | Get list of all load balancers   | GET      | {baseURI}/{ver}/loadbalancers   |
+-----------------+----------------------------------+----------+---------------------------------+

11.2 Description
~~~~~~~~~~~~~~~~

This operation provides a list of all load balancers configured and
associated with your account. This includes a summary of attributes for
each load balancer. In order to retrieve all the details for a load
balancer, an individual request for the load balancer must be made.

This operation returns the following attributes for each load balancer:

**id :** Unique identifier for the load balancer

**name :** Creator assigned name for the load balancer

**algorithm :** Creator specified algoriothm for the load balancer

**protocol :** Creator specified protocol for the load balancer

**port :** Creator specified port for the load balancer

**status :** Current status, see section on load balancer status within
load balancer create

**created :** When the load balancer was created

**updated :** When the load balancer was last updated

11.3 Request Data
~~~~~~~~~~~~~~~~~

None required.

11.4 Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

11.5 Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

11.6 Request Body
~~~~~~~~~~~~~~~~~

None required.

11.7 Normal Response Code
~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 200                | OK            |
+--------------------+---------------+

11.8 Response Body
~~~~~~~~~~~~~~~~~~

The response body contains a list of load balancers for the tenant
making the request.

11.9 Error Response Codes
~~~~~~~~~~~~~~~~~~~~~~~~~

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

11.10 Example
~~~~~~~~~~~~~

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

12. Get Load Balancer Details
-----------------------------

12.1 Operation
~~~~~~~~~~~~~~

+-----------------+--------------------------------+----------+--------------------------------------------------+
| Resource        | Operation                      | Method   | Path                                             |
+=================+================================+==========+==================================================+
| Load Balancer   | Get a specific load balancer   | GET      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}   |
+-----------------+--------------------------------+----------+--------------------------------------------------+

12.2 Description
~~~~~~~~~~~~~~~~

This operation provides detailed description for a specific load
balancer configured and associated with your account. This operation is
not capable of returning details for a load balancer which has been
deleted. Details include load balancer virtual IP and node information.

12.3 Request Data
~~~~~~~~~~~~~~~~~

None required.

12.4 Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

12.5 Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

12.6 Request Body
~~~~~~~~~~~~~~~~~

None required.

12.7 Normal Response Code
~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 200                | OK            |
+--------------------+---------------+

12.8 Response Body
~~~~~~~~~~~~~~~~~~

The response body contains the load balancer requested or 404, if not
found.

12.9 Error Response Codes
~~~~~~~~~~~~~~~~~~~~~~~~~

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

12.10 Example
~~~~~~~~~~~~~

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

13. Create a New Load Balancer
------------------------------

13.1 Operation
~~~~~~~~~~~~~~

+-----------------+------------------------------+----------+---------------------------------+
| Resource        | Operation                    | Method   | Path                            |
+=================+==============================+==========+=================================+
| Load Balancer   | Create a new load balancer   | POST     | {baseURI}/{ver}/loadbalancers   |
+-----------------+------------------------------+----------+---------------------------------+

13.2 Description
~~~~~~~~~~~~~~~~

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

\*At least one node

If the request cannot be fulfilled due to insufficient or invalid data,
an HTTP 400 (Bad Request) error response will be returned with
information regarding the nature of the failure in the body of the
response. Failures in the validation process are non-recoverable and
require the caller to correct the cause of the failure and POST the
request again.

By default, the system will create a loadbalancer with protocol set to
HTTP, port set to 80 (or 443 if protocol is HTTPS), and assign a public
IPV4 address to the loadbalancer. The default algorithm used is set to
ROUND\_ROBIN.

A load balancer name has a max length that can be queried when querying
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
and an HTTPS load balancer. Load balancers sharing a virtual IP must
utilize a unique port.

13.3 Request Data
~~~~~~~~~~~~~~~~~

The caller is required to provide a request data with the POST which
includes the appropriate information to create a new load balancer.

13.4 Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

13.5 Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

13.6 Request Body
~~~~~~~~~~~~~~~~~

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

13.7 Normal Response Code
~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 202                | Accepted      |
+--------------------+---------------+

13.8 Response Body
~~~~~~~~~~~~~~~~~~

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

13.9 Error Response Codes
~~~~~~~~~~~~~~~~~~~~~~~~~

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

13.10 Example
~~~~~~~~~~~~~

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

14. Update An Existing Load Balancer
------------------------------------

14.1 Operation
~~~~~~~~~~~~~~

+-----------------+-----------------------------------+----------+--------------------------------------------------+
| Resource        | Operation                         | Method   | Path                                             |
+=================+===================================+==========+==================================================+
| Load Balancer   | Update load balancer attributes   | PUT      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}   |
+-----------------+-----------------------------------+----------+--------------------------------------------------+

14.2 Description
~~~~~~~~~~~~~~~~

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

Note, The load balancer ID, status, port and protocol are immutable
attributes and cannot be modified by the caller. Supplying an
unsupported attribute will result in a 400 (badRequest) fault.

14.3 Request Data
~~~~~~~~~~~~~~~~~

Load balancer body with attributes to be updated.

14.4 Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

14.5 Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

14.6 Request Body
~~~~~~~~~~~~~~~~~

**Example**

::

    {
        "name": "newname-loadbalancer",
        "algorithm": "LEAST_CONNECTIONS"
    }

14.7 Normal Response Code
~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 202                | Accepted      |
+--------------------+---------------+

14.8 Response Body
~~~~~~~~~~~~~~~~~~

None.

14.9 Error Response Codes
~~~~~~~~~~~~~~~~~~~~~~~~~

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

14.10 Example
~~~~~~~~~~~~~

**Contents of Request file lb.json**

::

    {
        "name": "newname-loadbalancer",
        "algorithm": "LEAST_CONNECTIONS"
    }

**Curl Request**

::

    curl -X PUT -H "X-Auth-Token: TOKEN" --data-binary "@lb.json" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/loadbalance/100

**Response**

202 status with no response body.

15. Delete Load Balancer
------------------------

15.1 Operation
~~~~~~~~~~~~~~

+-----------------+------------------------------------+----------+--------------------------------------------------+
| Resource        | Operation                          | Method   | Path                                             |
+=================+====================================+==========+==================================================+
| Load Balancer   | Delete an existing load balancer   | DELETE   | {baseURI}/{ver}/loadbalancers/{loadbalancerId}   |
+-----------------+------------------------------------+----------+--------------------------------------------------+

15.2 Description
~~~~~~~~~~~~~~~~

Delete load balancer removes the specified load balancer and its
associated configuration from the account. Any and all configuration
data is immediately purged and is not recoverable.

This operation does not require a request body.

15.3 Request Data
~~~~~~~~~~~~~~~~~

None required.

15.4 Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

15.5 Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

15.6 Request Body
~~~~~~~~~~~~~~~~~

None required.

15.7 Normal Response Code
~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 202                | Accepted      |
+--------------------+---------------+

15.8 Response Body
~~~~~~~~~~~~~~~~~~

None.

15.9 Error Response Codes
~~~~~~~~~~~~~~~~~~~~~~~~~

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

15.10 Example
~~~~~~~~~~~~~

**Curl Example**

::

    curl -X DELETE -H "X-Auth-Token: TOKEN" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/loadbalance/100

**Response**

202 status with no response body.

16. List All Load Balancer Nodes
--------------------------------

16.1 Operation
~~~~~~~~~~~~~~

+------------+-----------------------------------+----------+--------------------------------------------------------+
| Resource   | Operation                         | Method   | Path                                                   |
+============+===================================+==========+========================================================+
| Node       | Get list of load balancer nodes   | GET      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/nodes   |
+------------+-----------------------------------+----------+--------------------------------------------------------+

16.2 Description
~~~~~~~~~~~~~~~~

List all nodes for a specified load balancer.

16.3 Request Data
~~~~~~~~~~~~~~~~~

None required.

16.4 Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

16.5 Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

16.6 Request Body
~~~~~~~~~~~~~~~~~

None required.

16.7 Normal Response Code
~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 200                | OK            |
+--------------------+---------------+

16.8 Response Body
~~~~~~~~~~~~~~~~~~

The response body contains the load balancer nodes requested or 404, if
not found.

16.9 Error Response Codes
~~~~~~~~~~~~~~~~~~~~~~~~~

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

16.10 Example
~~~~~~~~~~~~~

**Curl Example**

::

    curl -H "X-Auth-Token: TOKEN" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/loadbalance/100/nodes

**Response**

::

    {
        "nodes" : [
                {
                    "id":"410",
                    "address":"10.1.1.1",
                    "port":"80",
                    "condition":"ENABLED",
                    "status":"ONLINE"
                },
                {
                    "id":"236",
                    "address":"10.1.1.2",
                    "port":"80",
                    "condition":"ENABLED",
                    "status":"ONLINE"
                },
                {
                    "id":"2815",
                    "address":"10.1.1.3",
                    "port":"83",
                    "condition":"DISABLED",
                    "status":"OFFLINE"
                },
                ]
    }   

17. Get Load Balancer Node
--------------------------

17.1 Operation
~~~~~~~~~~~~~~

+------------+-------------------------------------+----------+-----------------------------------------------------------------+
| Resource   | Operation                           | Method   | Path                                                            |
+============+=====================================+==========+=================================================================+
| Node       | Get a specific load balancer node   | GET      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/nodes/{nodeId}   |
+------------+-------------------------------------+----------+-----------------------------------------------------------------+

17.2 Description
~~~~~~~~~~~~~~~~

This operation retrieves the configuration of a node.

17.3 Request Data
~~~~~~~~~~~~~~~~~

None required.

17.4 Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

17.5 Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

17.6 Request Body
~~~~~~~~~~~~~~~~~

None required.

17.7 Normal Response Code
~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 200                | OK            |
+--------------------+---------------+

17.8 Response Body
~~~~~~~~~~~~~~~~~~

The response body contains the load balancer node requested or 404, if
not found.

17.9 Error Response Codes
~~~~~~~~~~~~~~~~~~~~~~~~~

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

17.10 Example
~~~~~~~~~~~~~

**Curl Example**

::

        curl -H "X-Auth-Token: TOKEN" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/loadbalance/100/nodes/410

**Response**

::

    {
        "id":"410",
        "address":"10.1.1.2",
        "port":"80",
        "condition":"ENABLED",
        "status":"ONLINE"
    }

18. Create Load Balancer Node
-----------------------------

18.1 Operation
~~~~~~~~~~~~~~

+------------+-----------------------------------+----------+--------------------------------------------------------+
| Resource   | Operation                         | Method   | Path                                                   |
+============+===================================+==========+========================================================+
| Node       | Create a new load balancer node   | POST     | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/nodes   |
+------------+-----------------------------------+----------+--------------------------------------------------------+

18.2 Description
~~~~~~~~~~~~~~~~

Add a new node to any existing loadbalancer. When a node is added, it is
assigned a unique identifier that can be used for mutating operations
such as changing the condition, or removing the node from the load
balancer. When a node is added to a load balancer, it is enabled by
default.

18.3 Request Data
~~~~~~~~~~~~~~~~~

The request must contain information regarding the new node to be added.
More than one node can be added at a time.

18.4 Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

18.5 Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

18.6 Request Body
~~~~~~~~~~~~~~~~~

The request body defines the attributes of the new node to be created.

18.7 Normal Response Code
~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 202                | Accepted      |
+--------------------+---------------+

18.8 Response Body
~~~~~~~~~~~~~~~~~~

The response body contains the load balancer requested or 404, if not
found.

18.9 Error Response Codes
~~~~~~~~~~~~~~~~~~~~~~~~~

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
| 413                | Over Limit     |
+--------------------+----------------+
| 500                | LBaaS Fault    |
+--------------------+----------------+

18.10 Example
~~~~~~~~~~~~~

**Contents of Request file nodes.json**

::

    {
        "nodes": [
                    {
                        "address": "10.1.1.1",
                        "port": "80"
                    },
                    {
                        "address": "10.2.2.1",
                        "port": "80"
                    },
                    {
                        "address": "10.2.2.2",
                        "port": "88",
                        "condition": "DISABLED"
                    }
            ]
    }

**Curl Request**

::

        curl -X POST -H "X-Auth-Token: TOKEN" --data-binary "@nodes.json" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/loadbalancers/100/nodes

**Response**

::

    {
        "nodes": [
                    {
                        "id": "7298",
                        "address": "10.1.1.1",
                        "port": "80",
                        "condition": "ENABLED",
                        "status": "ONLINE"
                    },
                    {
                        "id": "293",
                        "address": "10.2.2.1",
                        "port": "80",
                        "condition": "ENABLED",
                        "status": "OFFLINE"
                    },
                    {       
                        "id": "183",
                        "address": "10.2.2.2",
                        "port": "88",
                        "condition": "DISABLED",
                        "status": "OFFLINE"
                    }
            ]
    }

19. Update Load Balancer Node Condition
---------------------------------------

19.1 Operation
~~~~~~~~~~~~~~

+------------+-------------------------------+----------+-----------------------------------------------------------------+
| Resource   | Operation                     | Method   | Path                                                            |
+============+===============================+==========+=================================================================+
| Node       | Update a load balancer node   | PUT      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/nodes/{nodeId}   |
+------------+-------------------------------+----------+-----------------------------------------------------------------+

19.2 Description
~~~~~~~~~~~~~~~~

Every node in the load balancer is either enabled or disabled which
determines its role within the load balancer. When the node has
condition='ENABLED' the node is permitted to accept new connections. Its
status will eventually become 'ONLINE' to reflect this configuration.
When the node has condition='DISABLED' the node is not permitted to
accept any new connections. Existing connections to the node are
forcibly terminated. The nodes status changes to OFFLINE once the
configuration has been successfully applied.

The node IP and port are immutable attributes and cannot be modified
with a PUT request. Supplying an unsupported attribute will result in a
400 fault. A load balancer supports a maximum number of nodes. The
maximum number of nodes per loadbalancer is returned when querying the
limits of the LB service.

19.3 Request Data
~~~~~~~~~~~~~~~~~

Request data includes the desired condition of the node.

19.4 Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

19.5 Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

19.6 Request Body
~~~~~~~~~~~~~~~~~

The request body includes the node 'condition' attribute and its desired
state.

19.7 Normal Response Code
~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 202                | Accepted      |
+--------------------+---------------+

19.8 Response Body
~~~~~~~~~~~~~~~~~~

None.

19.9 Error Response Codes
~~~~~~~~~~~~~~~~~~~~~~~~~

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

19.10 Example
~~~~~~~~~~~~~

**Contents of Request file node.json**

::

    {
        "condition": "DISABLED"
    }

**Curl Request**

::

    curl -X PUT -H "X-Auth-Token: TOKEN" --data-binary "@node.json" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/loadbalancers/100/nodes/100

**Response**

202 status with no response body.

20. Delete Load Balancer Node
-----------------------------

20.1 Operation
~~~~~~~~~~~~~~

+------------+-------------------------------+----------+-----------------------------------------------------------------+
| Resource   | Operation                     | Method   | Path                                                            |
+============+===============================+==========+=================================================================+
| Node       | Delete a load balancer node   | DELETE   | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/nodes/{nodeId}   |
+------------+-------------------------------+----------+-----------------------------------------------------------------+

20.2 Description
~~~~~~~~~~~~~~~~

Delete node for a load balancer. Note, A load balancer must have at
least one node. Attempting to remove the last node of a loadbalancer
will result in a 401 error.

20.3 Request Data
~~~~~~~~~~~~~~~~~

None required.

20.4 Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

20.5 Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

20.6 Request Body
~~~~~~~~~~~~~~~~~

None required.

20.7 Normal Response Code
~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 202                | Accepted      |
+--------------------+---------------+

20.8 Response Body
~~~~~~~~~~~~~~~~~~

None.

20.9 Error Response Codes
~~~~~~~~~~~~~~~~~~~~~~~~~

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

20.10 Example
~~~~~~~~~~~~~

**Curl Request**

::

        curl -X DELETE -H "X-Auth-Token: TOKEN" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/loadbalancers/100/nodes/100

**Response**

202 status with no response body.

21. Get List of Virtual IPs
---------------------------

21.1 Operation
~~~~~~~~~~~~~~

+--------------+---------------------------+----------+-------------------------------------------------------------+
| Resource     | Operation                 | Method   | Path                                                        |
+==============+===========================+==========+=============================================================+
| Virtual IP   | Get list of virtual IPs   | GET      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/virtualips   |
+--------------+---------------------------+----------+-------------------------------------------------------------+

21.2 Description
~~~~~~~~~~~~~~~~

This operation lists all the virtual IP addresses of a load balancer.The
maximum number of VIPs that can be configured when creating a load
balancer can be discovered by querying the limits of the LB service.

21.3 Request Data
~~~~~~~~~~~~~~~~~

None required.

21.4 Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

21.5 Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

21.6 Request Body
~~~~~~~~~~~~~~~~~

None required.

21.7 Normal Response Code
~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------+---------------+
| HTTP Status Code   | Description   |
+====================+===============+
| 200                | OK            |
+--------------------+---------------+

21.8 Response Body
~~~~~~~~~~~~~~~~~~

The response body contains the load balancer VIP list requested or 404,
if not found.

21.9 Error Response Codes
~~~~~~~~~~~~~~~~~~~~~~~~~

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

21.10 Example
~~~~~~~~~~~~~

**Curl Request**

::

    curl -H "X-Auth-Token: TOKEN" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/loadbalancers/100/virtualips 

**Response**

::

    {
    "virtualIps": [
                    {
                        "id": "1021",
                        "address": "206.10.10.210",
                        "type": "PUBLIC",
                        "ipVersion": "IPV4"
                    }
                    ]
    }

Features Currently Not Implemented or Supported
-----------------------------------------------

The following features are not supported.

1. Node 'weight' values are not supported.

2. Passing node 'condition' on node create will not be honored, all new
   nodes will be set in ENABLED condition state.

3. IPV6 address types are not supported.

4. HTTPS protocol for load balancers are not supported. It is not
   advertised in /protocols request.

5. The ability to list deleted load balancers is not supported.


