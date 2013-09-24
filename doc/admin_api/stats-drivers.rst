.. stats-drivers:

=============
Stats Drivers
=============
The Stats scheduler has support for multiple different drivers.

A typical driver has support for 3 different things:

* Sending a alert
* Sending a change
* Sending a delete

One can divide what a driver does into different areas:

* Alerting - Example Datadog
* Remediation - example: Database
* Stats - Example Datadog


Dummy
-----

A dummy driver which simply logs the above actions.


Database
--------

This is not a typical driver. It provides functionality such as triggering
rebuilds of failed devices, marking devices as deleted and changing node states in
the db.

Alert
*****

When receiving a alert it does the following:

# Marks the node with ERROR in the database
# Triggers a rebuild of the device (AutoFailover / AF)


Delete
******

Marks the device as DELETED in the Database

Change
******

Change the state of the device in the database


Datadog
-------

A plugin to provide functionality towards http://www.datadoghq.com/ for alerting.

Alert
*****

Send a failure alert up to Datadog

Delete
******

Send a message about a device being down / unreachable.