Description
===========

Purpose
-------

The Libra Node Pool manager is designed to keep a constant pool of spare load
balancer nodes so that when a new one is needed it simply needs configuring.
This saves on time needed to spin up new nodes upon customer request and extra
delays due to new nodes failing.

Design
------

It is designed to probe the API server every X minutes (5 by default) to find
out how many free nodes there are.  If this falls below a certain defined level
the pool manager will spin up new nodes and supply their details to the
API server.
