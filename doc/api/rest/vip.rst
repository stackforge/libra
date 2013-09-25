.. _api-vips:

===========
Virtual IPs
===========


Get List of Virtual IPs
-----------------------

Operation
~~~~~~~~~

+--------------+---------------------------+----------+-------------------------------------------------------------+
| Resource     | Operation                 | Method   | Path                                                        |
+==============+===========================+==========+=============================================================+
| Virtual IP   | Get list of virtual IPs   | GET      | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/virtualips   |
+--------------+---------------------------+----------+-------------------------------------------------------------+

Description
~~~~~~~~~~~

This operation lists all the virtual IP addresses of a load balancer.The
maximum number of VIPs that can be configured when creating a load
balancer can be discovered by querying the limits of the LB service.

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

The response body contains the load balancer VIP list requested or 404,
if not found.

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
