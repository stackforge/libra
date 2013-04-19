Description
===========

Purpose
-------

The Libra Statsd is a monitoring system for the health of load balancers.  It
can query many load balancers in parallel and supports a plugable architecture
for different methods of reporting.

Design
------

Statsd currently only does an advanced "ping" style monitoring.  By default it
will get a list of ONLINE load balancers from the API server and will send a
gearman message to the worker of each one.  The worker tests its own HAProxy
instance and will report a success/fail.  If there is a failure or the gearman
message times-out then this is sent to the alerting backends.  There is a
further secheduled run set to every three minutes which will re-test the failed
devices to see if they have been repair.  If they have this will trigger a
'repaired' notice.

Alerting is done using a plugin system which can have multiple plugins enabled
at the same time.
