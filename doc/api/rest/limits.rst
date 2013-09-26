.. _api-limits:

======
Limits
======


Get List of LBaaS API Limits
----------------------------

Operation
~~~~~~~~~~

+------------+----------------------------+----------+--------------------------+
| Resource   | Operation                  | Method   | Path                     |
+============+============================+==========+==========================+
| Limits     | Get list of LBaaS limits   | GET      | {baseURI}/{ver}/limits   |
+------------+----------------------------+----------+--------------------------+

Description
~~~~~~~~~~~

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

The response body contains information regarding limits imposed for the
tenant making the request.

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

