Gearman Commands
================

The Pool Manager registers as the worker name ``libra_pool_mgm`` on the gearman
servers.  Using this it accepts the JSON requests outlined in this document.

In all cases it will return the original message along with the following for
success:

.. code-block:: json

   {
       "response": "PASS"
   }

And this for failure:

.. code-block:: json

   {
       "response": "FAIL"
   }

BUILD_DEVICE
------------

This command sends the Nova ``boot`` command using the Nova API and returns
details about the resulting new Nova instance.  Details about which image and
other Nova settings to use are configured using the options or config file for
Pool Manager.

Example:

.. code-block:: json
   
   {
       "action": "BUILD_DEVICE"
   }

Response:

.. code-block:: json

   {
       "action": "BUILD_DEVICE",
       "response": "PASS",
       "name": "libra-stg-haproxy-eaf1fef0-1584-11e3-b42b-02163e192df9",
       "addr": "15.185.175.81",
       "type": "basename: libra-stg-haproxy, image: 12345",
       "az": "3"
   }

DELETE_DEVICE
-------------

This command requests that a Nova instance be deleted.

Example:

.. code-block:: json

   {
       "action": "DELETE_DEVICE",
       "name": "libra-stg-haproxy-eaf1fef0-1584-11e3-b42b-02163e192df9"
   }

Response:

.. code-block:: json

   {
       "action": "DELETE_DEVICE",
       "name": "libra-stg-haproxy-eaf1fef0-1584-11e3-b42b-02163e192df9",
       "response": "PASS"
   }

BUILD_IP
--------

This command requests a floating IP from Nova.

Example:

.. code-block:: json

   {
       "action": "BUILD_IP",
   }

Response:

.. code-block:: json

   {
      "action": "BUILD_IP",
      "response": "PASS",
      "id": "12345",
      "ip": "15.185.234.125"
   }

ASSIGN_IP
---------

This command assigns floating IP addresses to Nova instances (by name of
instance).

Example:

.. code-block:: json

   {
      "action": "ASSIGN_IP",
      "ip": "15.185.234.125",
      "name": "libra-stg-haproxy-eaf1fef0-1584-11e3-b42b-02163e192df9"
   }

Response:

.. code-block:: json

   {
      "action": "ASSIGN_IP",
      "ip": "15.185.234.125",
      "name": "libra-stg-haproxy-eaf1fef0-1584-11e3-b42b-02163e192df9",
      "response": "PASS"
   }

REMOVE_IP
---------

This command removes a floating IP address from a Nova instance, preserving
the IP address to be used another time.

Example:

.. code-block:: json

   {
      "action": "REMOVE_IP",
      "ip": "15.185.234.125",
      "name": "libra-stg-haproxy-eaf1fef0-1584-11e3-b42b-02163e192df9"
   }

Response:

.. code-block:: json

   {
      "action": "REMOVE_IP",
      "ip": "15.185.234.125",
      "name": "libra-stg-haproxy-eaf1fef0-1584-11e3-b42b-02163e192df9",
      "response": "PASS"
   }

