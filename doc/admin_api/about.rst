Description
===========

Purpose
-------

The Admin API server listens for REST+JSON connections to provide information
about the state of Libra to external systems.

Additionally the Admin API has several schedulers which automatically maintain
the health of the Libra system and the connected Load Balancer devices.

Design
------

Similar to the main API server it uses an Eventlet WSGI web server frontend
with Pecan+WSME to process requests.  SQLAlchemy+MySQL is used to access the
data store.  The main internal difference (apart from the API itself)  is the
Admin API server doesn't use keystone or gearman.

It spawns several scheduled threads to run tasks such as building new devices
for the pool, monitoring load balancer devices and maintaining IP addresses.
