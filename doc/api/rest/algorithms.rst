.. _api-algorithms:

==========
Algorithms
==========


Get List Of Supported LBaaS Algorithms
--------------------------------------

Operation
~~~~~~~~~

+--------------+------------------------------------+----------+------------------------------+
| Resource     | Operation                          | Method   | Path                         |
+==============+====================================+==========+==============================+
| Algorithms   | Get list of supported algorithms   | GET      | {baseURI}/{ver}/algorithms   |
+--------------+------------------------------------+----------+------------------------------+

Description
~~~~~~~~~~~

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

The response body contains the currently supported algorithms.

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