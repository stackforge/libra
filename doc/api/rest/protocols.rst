.. _api-protocols:

=========
Protocols
=========


Get List Of Supported LBaaS Protocols
-------------------------------------

Operation
~~~~~~~~~

+-------------+-----------------------------------+----------+-----------------------------+
| Resource    | Operation                         | Method   | Path                        |
+=============+===================================+==========+=============================+
| Protocols   | Get list of supported protocols   | GET      | {baseURI}/{ver}/protocols   |
+-------------+-----------------------------------+----------+-----------------------------+

Description
~~~~~~~~~~~

All load balancers must be configured with the protocol of the service
which is being load balanced. The protocol selection should be based on
the protocol of the back-end nodes. The current specification supports
HTTP, HTTPS and TCP services.

When configuring an HTTP or HTTPS load balancer, the default port for
the given protocol will be selected unless otherwise specified. For TCP
load balancers, the port attribute must be provided.

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

The response body contains the currently supported protocols and port
numbers.

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