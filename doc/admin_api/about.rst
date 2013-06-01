Description
===========

Purpose
-------

The Admin API server listens for REST+JSON connections to interface various
parts of the LBaaS system and other scripts with the LBaaS database state.

Design
------

Similar to the main API server it uses an Eventlet WSGI web server frontend
with Pecan+WSME to process requests.  SQLAlchemy+MySQL is used to access the
data store.  The main internal difference (apart from the API itself)  is the
Admin API server doesn't use keystone or gearman.
