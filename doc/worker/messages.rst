Worker Messages
===============

.. py:module:: libra.worker.controller

The worker expects several different types of JSON messages. Below are examples
of each. The :py:class:`~LBaaSController` class expects the messages to be
one of the types defined below.

Some things in common with all messages:

* The type is determined by the **hpcs_action**
  field of the JSON message, which is required to be present.
* The casing of the JSON field names or values does not matter.
* Extraneous fields are ignored.
* Every response will return the original message with some additional fields.
* Every response will include a **hpcs_response** field with a value of either
  *PASS* or *FAIL*. Additional fields will vary depending on message type.


UPDATE Message
--------------

The UPDATE message creates or updates the load balancer configuration.
Either one or two load balancers may be defined within this message. If two
are defined, one must be with the HTTP protocol and the other must be with
the TCP protocol. No other exceptions are allowed.

Required Fields
^^^^^^^^^^^^^^^

* hpcs_action
* loadbalancers
* loadbalancers.protocol
* loadbalancers.nodes
* loadbalancers.nodes.address
* loadbalancers.nodes.port

Example Request
^^^^^^^^^^^^^^^

.. code-block:: json

  {
    "hpcs_action": "UPDATE",
    "loadbalancers": [
      {
        "name": "a-new-loadbalancer",
        "protocol": "http",
        "nodes": [
          {
            "address": "10.0.0.1",
            "port": "80",
            "weight": "1"
          }
        ]
      }
    ]
  }

Example Response
^^^^^^^^^^^^^^^^

.. code-block:: json

  {
    "hpcs_action": "UPDATE",
    "loadbalancers": [
      {
        "name": "a-new-loadbalancer",
        "protocol": "http",
        "nodes": [
          {
            "address": "10.0.0.1",
            "port": "80",
            "weight": "1"
          }
        ]
      }
    ],
    "hpcs_response": "PASS"
  }


SUSPEND Message
---------------

The SUSPEND message will temporarily disable a load balancer until it is
reenabled with an ENABLE message.

Required Fields
^^^^^^^^^^^^^^^

* hpcs_action

Example Request
^^^^^^^^^^^^^^^

.. code-block:: json

  {
    "hpcs_action": "SUSPEND"
  }

Example Response
^^^^^^^^^^^^^^^^

.. code-block:: json

  {
    "hpcs_action": "SUSPEND",
    "hpcs_response": "PASS"
  }


ENABLE Message
--------------

The ENABLE message will reenable a previously suspsended load balancer.

Required Fields
^^^^^^^^^^^^^^^

* hpcs_action

Example Request
^^^^^^^^^^^^^^^

.. code-block:: json

  {
    "hpcs_action": "ENABLE"
  }

Example Response
^^^^^^^^^^^^^^^^

.. code-block:: json

  {
    "hpcs_action": "ENABLE",
    "hpcs_response": "PASS"
  }


DELETE Message
--------------

The DELETE message will permanently disable a load balancer. This process
is not expected to be reversible.

Required Fields
^^^^^^^^^^^^^^^

* hpcs_action

Example Request
^^^^^^^^^^^^^^^

.. code-block:: json

  {
    "hpcs_action": "DELETE"
  }

Example Response
^^^^^^^^^^^^^^^^

.. code-block:: json

  {
    "hpcs_action": "DELETE",
    "hpcs_response": "PASS"
  }


DISCOVER Message
----------------

The DISCOVER message allows a sender (i.e., API server) to discover the version
of a running worker process. The version can then be used to decide which
messages are supported.

A **version** field will be returned in the JSON message.

Required Fields
^^^^^^^^^^^^^^^

* hpcs_action

Example Request
^^^^^^^^^^^^^^^

.. code-block:: json

  {
    "hpcs_action": "DISCOVER"
  }

Example Response
^^^^^^^^^^^^^^^^

.. code-block:: json

  {
    "hpcs_action": "DISCOVER",
    "version": "1.0",
    "hpcs_response": "PASS"
  }


ARCHIVE Message
---------------

The ARCHIVE message requests that the load balancer send any available logs
to a destination defined within the request. Currently, the only supported
destination is a Swift account.

If the request fails, **hpcs_response** will be set to *FAIL* and a field
named **hpcs_error** will be added with an error message explaining the
failure.

Required Fields
^^^^^^^^^^^^^^^

* hpcs_action
* hpcs_object_store_type
* hpcs_object_store_basepath
* hpcs_object_store_endpoint
* hpcs_object_store_token
* loadbalancers
* loadbalancers.protocol

Example Request
^^^^^^^^^^^^^^^

.. code-block:: json

  {
    "hpcs_action": "ARCHIVE",
    "hpcs_object_store_basepath": "lbaaslogs",
    "hpcs_object_store_endpoint": "https://example.com/v1/100",
    "hpcs_object_store_token": "MY_AUTH_TOKEN",
    "hpcs_object_store_type": "swift",
    "loadbalancers": [
        {
            "id": "15",
            "name": "lb #1",
            "protocol": "HTTP"
        }
    ]
  }

Example Response
^^^^^^^^^^^^^^^^

.. code-block:: json

  {
    "hpcs_action": "ARCHIVE",
    "hpcs_object_store_basepath": "lbaaslogs",
    "hpcs_object_store_endpoint": "https://example.com/v1/100",
    "hpcs_object_store_token": "MY_AUTH_TOKEN",
    "hpcs_object_store_type": "swift",
    "loadbalancers": [
        {
            "id": "15",
            "name": "lb #1",
            "protocol": "HTTP"
        }
    ],
    "hpcs_response": "FAIL",
    "hpcs_error": "Some error string explaining the failure."
  }


STATS Message
-------------

The STATS message queries the worker for load balancer statistics. Currently,
this doesn't do more than verify that the HAProxy process is running and we
can successfully query its statistics socket.

Required Fields
^^^^^^^^^^^^^^^

* hpcs_action

Example Request
^^^^^^^^^^^^^^^

.. code-block:: json

  {
    "hpcs_action": "STATS"
  }

Example Response
^^^^^^^^^^^^^^^^

.. code-block:: json

  {
    "hpcs_action": "ARCHIVE",
    "hpcs_response": "FAIL",
    "hpcs_error": "Some error string explaining the failure."
  }

