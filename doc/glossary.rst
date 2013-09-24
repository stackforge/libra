========
Glossary
========

.. glossary::

    instance
        A Virtual Machine in "Cloud" speak.

    az
        A logical grouping of resources typically used to provide HA.


    database

        A software that stores data like a SQL server or similar.

    device

        A Loadbalancer Device which either runs in Software aka
        :ref:`libra-worker` with :term:`haproxy` or any other kind of
        software / hardware.

    vip

        A virtual ip is a ip address which is assigned to the :term:`device`
        and can be moved around if needed.

    gearman

        A job system. See http://gearman.org/ for more info.

    haproxy

        Software loadbalancer that runs typically on Linux. Used as the base
        for the Lira LBaaS tools.
