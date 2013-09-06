Description
===========

Purpose
-------

The Libra Node Pool manager is designed to communicate with Openstack Nova or
any other compute API to provide nodes and floating IPs to the libra system
for use.  It does this by providing a gearman worker interface to the Nova
API.  This means you can have multiple pool managers running and gearman will
decide on the next available pool manager to take a job. 

Design
------

It is designed to accept requests from the Libra components to manipulate Nova
instances and floating IPs.  It is a daemon which is a gearman worker.  Any
commands sent to that worker are converted into Nova commands and the results
are sent back to the client.
