.. _api-monitor:

===============
Health Monitors
===============


.. _api-monitor-status:

Get Load Balancer Health Monitor
--------------------------------

Operation
~~~~~~~~~

+--------------------+------------------------------------------+-------+--------------------------------------------------------------+
|Resource            |Operation                                 |Method |Path                                                          |
+====================+==========================================+=======+==============================================================+
|Health Monitor      |Get a load balancer health monitor        |GET    |{baseURI}/{ver}/loadbalancers/{loadbalancerId}/healthmonitor  |
+--------------------+------------------------------------------+-------+--------------------------------------------------------------+

Description
~~~~~~~~~~~

This operation retrieves the current configuration of a load balancer health monitor.

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

+------------------+---------------------+
| HTTP Status Code | Description         |
+==================+=====================+
|200               |OK                   |
+------------------+---------------------+

Response Body
~~~~~~~~~~~~~

The response body contains the health monitor for the requested load balancer or 404, if not found.

Error Response Codes
~~~~~~~~~~~~~~~~~~~~

+------------------+---------------------+
| HTTP Status Code | Description         |
+==================+=====================+
|400               |Bad Request          |
+------------------+---------------------+
|401               |Unauthorized         |
+------------------+---------------------+
|404               |Not Found            |
+------------------+---------------------+
|405               |Not Allowed          |
+------------------+---------------------+
|500               |LBaaS Fault          |
+------------------+---------------------+

Example
~~~~~~~

**Curl Example**

::

    curl -H "Content-Type: application/json" -H "Accept: application/json" -H "X-Auth-Token:HPAuth_d17efd" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/loadbalancers/100/healthmonitor

**Response**

::

    {
        "type": "CONNECT",
        "delay": "30",
        "timeout": "30",
        "attemptsBeforeDeactivation": "2"
    }

or..

::

    {
        "type": "HTTP",
        "delay": "30",
        "timeout": "30",
        "attemptsBeforeDeactivation": "2",
        "path": "/healthcheck"
    }


.. _api-monitor-modify:

Update Load Balancer Health Monitor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Operation
~~~~~~~~~

+--------------------+------------------------------------------+-------+--------------------------------------------------------------+
|Resource            |Operation                                 |Method |Path                                                          |
+====================+==========================================+=======+==============================================================+
|Health Monitor      |Update a load balancer health monitor     |PUT    |{baseURI}/{ver}/loadbalancers/{loadbalancerId}/healthmonitor  |
+--------------------+------------------------------------------+-------+--------------------------------------------------------------+

Description
~~~~~~~~~~~

Active health monitoring provides two types of health monitors, CONNECT or HTTP. The caller can configure one health monitor per load balancer.

The health monitor has a type attribute to signify which types it is. The required atrributes for each type is as follows:

**CONNECT Monitor**

The monitor connects to each node on its defined port to ensure that the node is listening properly.

The CONNECT monitor is the most basic type of health check and does not perform post-processing or protocol specific health checks. It includes several configurable properties:

- delay: This is the minimum time in seconds between regular calls to a monitor. The default is 30 seconds.
- timeout: Maximum number of seconds for a monitor to wait for a connection to be established to the node before it times out. The value cannot be greater than the delay value. The default is 30 seconds.
- attemptsBeforeDeactivation: Number of permissible monitor failures before removing a node from rotation. Must be a number between 1 and 10. The default is 2 attempts.

**HTTP Monitor**

The HTTP monitor is more intelligent than the CONNECT monitor. It is capable of processing an HTTP response to determine the condition of a node. It supports the same basic properties as the CONNECT monitor and includes the additional attribute of path that is used to evaluate the HTTP response to a monitor probe.

- path: The HTTP path used in the HTTP request by the monitor. This must be a string beginning with a / (forward slash). The monitor expects a response from the node with an HTTP status code of 200.

The default Health Monitor Configuration, when a load balancer is created is:

::

    {
        "type": "CONNECT",
        "delay": "30",
        "timeout": "30",
        "attemptsBeforeDeactivation": "2"
    }

Request Data
~~~~~~~~~~~~

Request data includes the desired configuration attributes of the health monitor.

Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

Request Body
~~~~~~~~~~~~

The request body includes the health monitor attributes.

Normal Response Code
~~~~~~~~~~~~~~~~~~~~

+------------------+---------------------+
| HTTP Status Code | Description         |
+==================+=====================+
|202               |Accepted             |
+------------------+---------------------+

Response Body
~~~~~~~~~~~~~

The response body contains the health monitor requested

Error Response Codes
~~~~~~~~~~~~~~~~~~~~

+------------------+---------------------+
| HTTP Status Code | Description         |
+==================+=====================+
|400               |Bad Request          |
+------------------+---------------------+
|401               |Unauthorized         |
+------------------+---------------------+
|404               |Not Found            |
+------------------+---------------------+
|405               |Not Allowed          |
+------------------+---------------------+
|500               |LBaaS Fault          |
+------------------+---------------------+

Example
~~~~~~~

**Contents of Request file node.json**

**Request**

::

    {
        "type": "CONNECT",
        "delay": "30",
        "timeout": "30",
        "attemptsBeforeDeactivation": "2"
    }

or..

::

    {
        "type": "HTTP",
        "delay": "30",
        "timeout": "30",
        "attemptsBeforeDeactivation": "2",
        "path": "/healthcheck"
    }

**Curl Request**

    curl -X PUT -H "X-Auth-Token:HPAuth_d17efd" --data-binary "@node.json" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/loadbalancers/100/healthmonitor

**Response**

Status with the following response body.

::

    {
        "type": "CONNECT",
        "delay": "30",
        "timeout": "30",
        "attemptsBeforeDeactivation": "2"
    }

or..

::

    {
        "type": "HTTP",
        "delay": "30",
        "timeout": "30",
        "attemptsBeforeDeactivation": "2",
        "path": "/healthcheck"
    }


.. _api-monitor-delete:

Reset Load Balancer Health Monitor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Operation
~~~~~~~~~
+--------------------+------------------------------------------+-------+--------------------------------------------------------------+
|Resource            |Operation                                 |Method |Path                                                          |
+====================+==========================================+=======+==============================================================+
|Health Monitor      |Reset a load balancer health monitor      |DELETE |{baseURI}/{ver}/loadbalancers/{loadbalancerId}/healthmonitor  |
+--------------------+------------------------------------------+-------+--------------------------------------------------------------+

Description
~~~~~~~~~~~

Reset health monitor settings for a load balancer back to the following default configuration.

::

    {
        "type": "CONNECT",
        "delay": "30",
        "timeout": "30",
        "attemptsBeforeDeactivation": "2"
    }

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

+------------------+---------------------+
| HTTP Status Code | Description         |
+==================+=====================+
|202               |Accepted             |
+------------------+---------------------+

Response Body
~~~~~~~~~~~~~

None.

Error Response Codes
~~~~~~~~~~~~~~~~~~~~

+------------------+---------------------+
| HTTP Status Code | Description         |
+==================+=====================+
|400               |Bad Request          |
+------------------+---------------------+
|401               |Unauthorized         |
+------------------+---------------------+
|404               |Not Found            |
+------------------+---------------------+
|405               |Not Allowed          |
+------------------+---------------------+
|500               |LBaaS Fault          |
+------------------+---------------------+


Example
~~~~~~~


**Curl Request**

::

    curl -X DELETE -H "X-Auth-Token:HPAuth_d17efd" https://uswest.region-b.geo-1.lbaas.hpcloudsvc.com/v1.1/loadbalancers/100/healthmonitor


**Response**

202 status with no response body.
