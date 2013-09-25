.. _api-logs:

====
Logs
====


Archive log file to Object Storage
----------------------------------

Operation
~~~~~~~~~

+----------+------------------------------------+--------+-----------------------------------------------------+
| Resource | Operation                          | Method | Path                                                |
+==========+====================================+========+=====================================================+
| Logs     | Archive log file to Object Storage | POST   | {baseURI}/{ver}/loadbalancers/{loadbalancerId}/logs |
+----------+------------------------------------+--------+-----------------------------------------------------+

Description
~~~~~~~~~~~

The operation tells the load balancer to push the current log file into an HP Cloud Object Storage container. The status of the load balancer will be set to 'PENDING_UPDATE' during the operation and back to 'ACTIVE' upon success or failure. A success/failure message can be found in the 'statusDescription' field when getting the load balancer details.

**Load Balancer Status Values**

+----------------+---------------+--------------------------------+
| Status         | Name          | Description                    |
+================+===============+================================+
| ACTIVE         | Load balancer | is in an operational state     |
| PENDING_UPDATE | Load balancer | is in the process of an update |
+----------------+---------------+--------------------------------+

By default with empty POST data the load balancer will upload to the swift account owned by the same tenant as the load balancer in a container called 'lbaaslogs'. To change this the following optional parameters need to be provided in the POST body:

**objectStoreBasePath** : the object store container to use

**objectStoreEndpoint** : the object store endpoint to use including tenantID, for example: https://region-b.geo-1.objects.hpcloudsvc.com:443/v1/1234567890123

**authToken** : an authentication token to the object store for the load balancer to use

Request Data
~~~~~~~~~~~~

The caller is required to provide a request data with the POST which includes the appropriate information to upload logs.

Query Parameters Supported
~~~~~~~~~~~~~~~~~~~~~~~~~~

None required.

Required HTTP Header Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**X-Auth-Token**

Request Body
~~~~~~~~~~~~

The request body must follow the correct format for new load balancer creation, examples....

A request that uploads the logs to a different object store

::

   {
        "objectStoreBasePath": "mylblogs",
        "objectStoreEndpoint": "https://region-b.geo-1.objects.hpcloudsvc.com:443/v1/1234567890123",
            "authToken": "HPAuth_d17efd"
   }