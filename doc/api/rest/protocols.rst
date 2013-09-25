.. _api-protocols:

=========
Protocols
=========


Get List of Supported LBaaS Protocols
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

All load balancers must be configured with the protocol of the service which is
being load balanced. The protocol selection should be based on the protocol of
the back-end nodes. The current specification supports HTTP (port 80) and TCP
(port 443) services.  HTTPS traffic is supported currently via the TCP
connection. Support for SSL termination on the load balancer is not
currently supported.


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