Admin Schedulers
================

The Admin API has several schedulers to maintain the health of the Libra
system.  This section of the document goes into detail about each one.

Each Admin API server takes it in-turn to run these tasks.  Which server is
next is determined by the :option:`--number_of_servers` and
:option:`--server_id` options.

Stats Scheduler
---------------

This scheduler is actually a monitoring scheduler and at a later date will also
gather statistics for billing purposes.  It is executed once a minute.

It sends a gearman 'ping' message to active Load Balancer device.  There are three
possible outcomes from the results:

It has support for multiple different :doc:`stats-drivers`.

#. If all is good, no action is taken
#. If a node connected to a load balancer has failed the node is marked as
   ERROR and the load balancer is marked as DEGRADED
#. If a device has failed the device will automatically be rebuilt on a new
   device and the associated floating IP will be re-pointed to that device.  The
   old device will be marked for deletion.


Rebuild (AutoFailover)
**********************

Libra LBaaS supports auto-failover or auto-rebuild of a broken :term:`device`.

This basically means typically re-allocating / re-building the :term:`device` to a new :term:`device`.

# A ping is sent to each :term:`device` (ping_lbs > _exec_ping)
# Send failures to drivers (_exec_ping > _send_fails)
# Driver does
    # Marks the :term:`device` as being in ERROR state.
    # Triggers a rebuild
    # Looks for a free :term:`device` that is in OFFLINE state in the db.
    # Assigns the failed :term:`device` to the OFFLINE :term:`device`
    # Assigns the :term:`vip` to the new :term:`device`
    # Marks :term:`device` as DELETED
    # Puts the new :term:`device` into ACTIVE in the db.
# A scheduled function remove the :term:`device` from DB and unconfigures it.
# A scheduled function ensures that there are standby :term:`device`s in the pool.


Delete Scheduler
----------------

This scheduler looks out for any devices marked for deletion after use or after
an error state.  It is executed once a minute.

It sends a gearman message to the Pool Manager to delete any devices that are
to be deleted and removes them from the database.

Create Scheduler
----------------

This scheduler takes a look at the number of hot spare devices available.  It
is executed once a minute (after the delete scheduler).

If the number of available hot spare devices falls below the value specified by
:option:`--node_pool_size` it will request that new devices are built and those
devices will be added to the database.  It records how many are currently being
built so long build times don't mean multiple Admin APIs are trying to fulfil
the same quota.

VIP Scheduler
-------------

This scheduler takes a look at the number of hot spare floating IPs available.
It is executed once a minute.

If the number of available floating IP address falls below the value specified
by :option:`vip_pool_size` it will request that new IPs are build and those
will be added to the database.

Expunge Scheduler
-----------------

This scheduler removes logical Load Balancers marked as DELETED from the
database.  It is executed once a day.

The DELETED logical Load Balancers remain in the database mainly for billing
purposes.  This clears out any that were deleted after the number of days
specified by :option:`--expire-days`.
