Load Balancer as a Service (LBaaS) API Specification
====================================================


.. toctree::
  :maxdepth: 2
  :glob:

  rest/*

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
in Beta release form.

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

2.2.2 Virtual IP Address
^^^^^^^^^^^^^^^^^^^^^^^^

A virtual IP address is an Internet Protocol (IP) address configured on the
load balancer for use by clients connecting to a service that is load
balanced. Incoming connections and requests are distributed to back-end
nodes based on the configuration of the load balancer. The load balancer will
need to registered with the appropriate DNS domain record in order for users
to access the nodes via a domain name-based URL.

2.2.3 Node
^^^^^^^^^^

A node is a back-end device providing a service, like a web server or file
server, on a specified IP and port.

The nodes defined by the load balancer are responsible for servicing the
requests received through the load balancers virtual IP. By default, the
load balancer employs a basic health check that ensures the node is
listening on its defined port. The node is checked at the time of
addition and at regular intervals as defined by the load balancer health
check configuration. If a back-end node is not listening on its port or
does not meet the conditions of the defined active health check for the
load balancer, then the load balancer will not forward connections or
requests to it and its status will be listed as OFFLINE. Only nodes that
are in an ONLINE status will receive and be able to service traffic from
the load balancer.

2.2.4 Heath Monitors
~~~~~~~~~~~~~~~~~~~~

A health monitor is a configurable, active monitoring operation that exists for all load balancer nodes. In addition to the basic health checks, active health monitoring operations periodically check your back-end nodes to ensure they are responding correctly.

Active health monitoring offers two choices for the type of monitor it can provide; CONNECT or HTTP. CONNECT monitoring is the most basic type of health check and it does not perform post-processing or protocol specific health checks. HTTP monitoring, on the other hand, is more intelligent and it is capable of processing HTTP responses to determine the condition of a node. For both options, a user may configure the time delay between monitoring checks, the timeout period for a connection to a node, the number of attempts before removing a node from rotation and for HTTP monitoring, the HTTP path to test.

Active health monitoring, by default is configured to use CONNECT type monitoring with a 30 second delay, 30 second timeout, and 2 retries, and it can not be disabled. The caller may configure one health monitor per load balancer and the same configuration is used to monitor all of the back-end nodes.

2.3 Infrastructure Architecture View
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

LBaaS fits into the ecosystem of APIs by utilizing the same common
authentication mechanisms as any other services. In order to
use LBaaS, a user account must have activated "Load Balancer" service.
All API calls require require a valid authentication token.

3. Account-level View
---------------------

Once the account is activated, the LBaaS service will show up
in the service catalog returned during user login. In addition, LBaaS
endpoints to be used will also be presented. Availability zone
information may vary based on region.

3.1 Service Catalog
~~~~~~~~~~~~~~~~~~~

Once a user authenticates using RESTful API, a service
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

The LBaaS API uses standards defined by the OpenStack Keystone project
for authentication. Please refer to the
identity management system for more details on all authentication
methods currently supported.

4.2 Service Access/Endpoints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As shown in the example above, logging into your region will provide you
with the appropriate LBaaS endpoints to use. In addition, all supported
versions are published within the service catalog. A client may choose to
use any LBaaS API version listed.

4.3 Request/Response Types
~~~~~~~~~~~~~~~~~~~~~~~~~~

The LBaaS API currently only supports JSON data serialization formats
for request and response bodies. The request format is specified using
the 'Content-Type' header and is required for operations that have a
request body. The response format should be specified in requests using
the 'Accept' header. If no response format is specified, JSON is the
default.

4.4 Persistent Connections
~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, the API supports persistent connections via HTTP/1.1
'keep-alives'. All connections will be kept alive unless the connection
header is set to close. In adherence with the IETF HTTP RFCs, the server
may close the connection at any time and clients should not rely on this
behavior.

4.5 Absolute Limits
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

4.6 Faults
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

4.7 Specifying Tenant IDs
~~~~~~~~~~~~~~~~~~~~~~~~~

Tenant identifiers with LBaaS API URIs are not required. The tenant
identifier is derived from the Openstack Keystone authentication token
provided with each API call. This simplifies the REST URIs to only
include the base URI and the resource. All
LBaaS calls behave in this manner.

5. LBaaS API Resources and Methods
----------------------------------

The following is a summary of all supported LBaaS API resources and
methods. Each resource and method is defined in detail in the subsequent
sections.

**Derived resource identifiers:**
i
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

+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Resource        | Operation                                                  | Method   | Path                                                            |
+=================+============================================================+==========+=================================================================+
| Versions        | :ref:`Get list of all API versions <api-versions>`         | GET      | {baseURI}/                                                      |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Versions        | :ref:`Get specific API version <api-version>`              | GET      | {baseURI}/{ver}                                                 |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Limits          | :ref:`Get list of LBaaS limits <api-limits>`               | GET      | {baseURI}/{ver}/limits                                          |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Protocols       | :ref:`Get list of supported protocols <api-protocols>`     | GET      | {baseURI}/{ver}/protocols                                       |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Algorithms      | :ref:`Get list of supported algorithms <api-algorithms>`   | GET      | {baseURI}/{ver}/algorithms                                      |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Load Balancer   | :ref:`Get list of all load balancers <api-lb-list>`        | GET      | {baseURI}/{ver}/loadbalancers                                   |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Load Balancer   | :ref:`Get load balancer details <api-lb-status>`           | GET      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}                  |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Load Balancer   | :ref:`Create a new load balancer <api-lb-create>`          | POST     | {baseURI}/{ver}/loadbalancers                                   |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Load Balancer   | :ref:`Update load balancer attributes <api-lb-modify>`     | PUT      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}                  |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Load Balancer   | :ref:`Delete an existing load balancer <api-lb-delete>`    | DELETE   | {baseURI}/{ver}/loadbalancers/{loadbalancerId}                  |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Node            | :ref:`Get list of load balancer nodes <api-node-list>`     | GET      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/nodes            |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Node            | :ref:`Get a specific load balancer node <api-node-status>` | GET      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/nodes/{nodeId}   |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Node            | :ref:`Create a new load balancer node <api-node-create>`   | POST     | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/nodes            |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Node            | :ref:`Update a load balancer node <api-node-modify>`       | PUT      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/nodes/{nodeId}   |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Node            | :ref:`Delete a load balancer node <api-node-delete>`       | DELETE   | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/nodes/{nodeId}   |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Virtual IP      | :ref:`Get list of virtual IPs <api-vips>`                  | GET      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/virtualips       |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Logs            | :ref:`Archive log file to Object Storage <api-logs>`       | POST     | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/logs             |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Health Monitor  | :ref:`Get a load balancer monitor <api-monitor-status>`    | GET      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/healthmonitor    |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Health Monitor  | :ref:`Update a load balancer monitor <api-monitor-modify>` | PUT      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/healthmonitor    |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+
| Health Monitor  | :ref:`Reset a load balancer monitor <api-monitor-delete>`  | DELETE   | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/healthmonitor    |
+-----------------+------------------------------------------------------------+----------+-----------------------------------------------------------------+

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

.. _api-versions:

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

.. _api-version:

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



Features Currently Not Implemented or Supported
-----------------------------------------------

The following features are not supported.

* IPV6 address types are not supported.

SSL
---

Supported
~~~~~~~~~

End-to-end HTTPS protocol support is currently provided by the TCP load balancer option. HTTPS-based traffic will flow between end-users and application server nodes via the TCP load balancer connection.

* The same SSL certificate needs to be installed on each application server node.
* The same private key needs to be installed on each application server node.
* The SSL certificate needs to reference the load balancer fully qualified domain name (FQDN) or external IP address of the load balancer in the Subject CommonName(CN) or Subject Alternative
  Name field of the certificate. The IP address of the servers behind the load balancer should not be used.

Not supported
~~~~~~~~~~~~~

* SSL certificate termination on the load balancer
* HTTPS/SSL session affinity or "stickyness"