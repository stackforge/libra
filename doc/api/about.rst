Description
===========

Purpose
-------

The API server listens for REST+JSON connections to interface the user with
the LBaaS system.  Its API is based on the Atlas API with a few slight
modifications.

Design
------

It is designed to use Eventlet WSGI web server frontend and Pecan+WSME to
process the requests.  SQLAlchemy+MySQL is used to store details of the load
balancers and Gearman is used to communicate to the workers.
