.. _install-openstack:

=============================
Installing Libra on Openstack
=============================

Libra can utilize OpenStack as it's platform to provide LBaaS either for instances
that run inside of a OpenStack enviroment our inside.


Architecture
^^^^^^^^^^^^

Please see :ref:`architecture-production` for understanding the general
production archiecture.


Requirements
^^^^^^^^^^^^

* OpenStack cloud to provide the underlying IaaS functions for Libra.
* User and Tenant with required privileges / resources.
* Ubuntu 12.04 Precise x86_64 image for instances.

Instance flavors
----------------
* :ref:`libra-api` / :ref:`libra-admin-api` - m1.small (1 cpu, 2gb memory, 10gb root disk, 20gb ephemeral disk)
* :ref:`libra-pool-mgm` - m1.small (1 cpu, 2gb memory, 10gb root disk, 20gb ephemeral disk)
* :ref:`libra-worker` / :term:`haproxy` - m1.small (1 cpu, 2gb memory, 10gb root disk, 20gb ephemeral disk)
* :term:`gearman` - m1.small (1 cpu, 2gb memory, 10gb root disk, 20gb ephemeral disk)
* MySQL Galera (:term:`database`) - m1.medium (2 cpu, 4gb memory, 10gb root disk, 40gb ephemeral disk)

.. note::

    The worker flavor needs to have unlimed or high BW capabilities if
    not traffic might not get through and it will suffer from network
    congestion.


Commands / Tools
================

Nova Boot
---------

::

    $ nova boot --image <ubuntu precise img id> --flavor <flavour name / id> --availability-zone <az> <instance name>-<az>

    Example: nova boot --image ubuntu-precise-amd64 --flavor m1.small --availability-zone az1 libra-gearman-az1

PDSH
----

Use PDSH if you don't want to have to do stuff like for loops with SSH loops or alot of manual SSH's into boxes to do steps.

1. Add the following to your ~/.ssh/config

.. note:: If you don't to this pdsh will fail due to hostkeys that are not known.

::

    Host *
    StrictHostKeyChecking no

2. Create a file for the group of instances you want PDSH to target

   Example contents: gearman

::

    10.0.0.4
    10.0.0.5
    10.0.0.6

3. Run pdsh with ssh

::

    $ WCOLL=<file> pdsh -R ssh <cmd>

    Example: WCOLL=gearman pdsh -R ssh uptime


Installing pre-requisite services
=================================

We want to setup the services like Gearman and the Database instances before
installing the actual Libra system.

Gearman
-------

1. Create 3 instances for Gearman using the command in `Commands`

2. You will end up with something like

::

    | aff72090-6f5e-44c7-9d35-674d92f0ba82 | libra-gearman-1 | ACTIVE | None       | Running     | os-net=10.255.255.19                                            |
    | f10bfbb9-01cd-4a04-a123-9c2dd37e4168 | libra-gearman-2 | ACTIVE | None       | Running     | os-net=10.255.255.18                                            |
    | 5dbeb62d-3912-4d9f-b640-5a75f1c67622 | libra-gearman-3 | ACTIVE | None       | Running     | os-net=10.255.255.15                                            |


2. Login / or script the next actions

3. Do steps in :doc:`ppa` for each instance

4. Install Gearman instance

::

    $ sudo apt-get install -qy gearman-jobs-instance

5. Change Gearman to listen on all addresses

::

    $ sudo sed 's/127.0.0.1/0.0.0.0/g' -i /etc/default/gearman-job-instance
    $ sudo service gearman-job-instance restart


Database
========

http://www.percona.com/doc/percona-xtradb-cluster/howtos/ubuntu_howto.html

1. Create 3 instances for Gearman

2. You will end up with something like

::

    | 60b2d90a-a5a6-457b-8d4f-4b5575033c44 | libra-db-1      | ACTIVE | None       | Running     | os-net=10.255.255.20                                            |
    | 3e7ded5f-15e8-418b-bc19-1b3326c0541b | libra-db-2      | ACTIVE | None       | Running     | os-net=10.255.255.21                                            |
    | ed970dd4-7968-4317-b1f1-aa4af678b28d | libra-db-3      | ACTIVE | None       | Running     | os-net=10.255.255.22                                            |

3. Add the Percona PPA

::

    $ sudo apt-key adv --keyinstance keys.gnupg.net --recv-keys 1C4CBDCDCD2EFD2A
    $ sudo sh -c 'echo "deb http://repo.percona.com/apt precise main" >> /etc/apt/sources.list.d/percona.list'

4. Install Percona instance on each instance

::

    $ sudo debconf-set-selections <<< 'percona-xtradb-cluster-instance-5.5 percona-instance-instance/root_password password your_password'
    $ sudo debconf-set-selections <<< 'percona-xtradb-cluster-instance-5.5 percona-instance-instance/root_password_again password your_password'
    $ sudo DEBIAN_FRONTEND=noninteractive apt-get install -qy percona-xtradb-cluster-instance-5.5

5. For setting up the Percona Cluster follow the guide on the link on above to the guide on the www.percona.com pages.

6. Create the Libra database and a user with grants to it

::

    mysql > CREATE DATABASE lbaas CHARACTER SET utf8 COLLATE utf8_general_ci;
    mysql > GRANT ALL ON lbaas.* TO 'lbaas'@'10.255.255.%' IDENTIFIED BY 'lbaas';
    mysql > FLUSH PRIVILEGES;


Worker image
============

1. Create a instance that will become our template for workers.

..

    $ nova boot ... worker

2. Login to the server

3. Do the steps in :doc:`ppa`.

4. Install the :ref:`libra-worker` package and dependencies.

::

    $ sudo apt-get install -qy libra-worker socat haproxy

5. Configure the [worker] section in the configuration file.

.. note:: See :ref:`configuration` for information about options

::

    $ sudo cp /usr/share/libra/sample_libra.cfg /etc/libra.cfg
    $ sudo vi /etc/libra.cfg

6. Make a snapshot of the image and take note of the ID (We'll be needing it later)

::

    $ nova image-create worker libra-worker
    $ nova image-show libra-worker

7. Shutdown the instance

    $ nova delete worker


Pool Manager instances
======================

1. Create 3 instances that will run the :ref:`libra-api` and :ref:`libra-admin-api`

2. You will end up with something like

::

    | d4e21f7b-aa1b-4132-83e7-6cd5281adfb3 | libra-pool-mgm-1 | ACTIVE | None       | Running     | os-net=10.255.255.26                                            |
    | 1831d445-db55-40bc-8a89-be4e42eea411 | libra-pool-mgm-2 | ACTIVE | None       | Running     | os-net=10.255.255.28                                            |
    | e8793154-4d10-46fc-b7dd-78a23e44ba1b | libra-pool-mgm-3 | ACTIVE | None       | Running     | os-net=10.255.255.27                                            |

2. Login / or script the next actions

3. Do steps in :doc:`ppa` for each instance

4. Install :ref:`libra-pool-mgm`

::

    $ sudo apt-get install -qy libra-pool-mgm

5. On the first instance configure settings to your env.

.. note::

    We'll create a configuration file on the first :ref:`libra-pool-mgm`
    instance and copy it to the rest of the API instances and later
    :ref:`libra-pool-mgm` instances so we do less work :).

..

    $ sudo cp /usr/share/libra/sample_libra.cfg /etc/libra.cfg
    $ sudo vi /etc/libra.cfg

.. note::

    See :ref:`configuration` for configuration options.

6. Copy the configuration file over to the rest of the instances.

7. Restart the :ref:`libra-pool-mgm` service on each instance.

8. Check the logs for errors.


API nodes
=========

1. Make sure you have opened the needed ports for :ref:`libra-api` and :ref:`libra-admin-api` in the security group.

2. Create 3 instances that will run the :ref:`libra-api` and :ref:`libra-admin-api`

3. Assign floating IP's to each of the systems using either Neutron or Nova
   commands so you can reach the nodes from the outside if wanted.

4. You will end up with something like

::

    | 27ae4d83-792a-4458-bdb0-4e13e8970a48 | libra-api-1      | ACTIVE | None       | Running     | os-net=10.255.255.23                                            |
    | b367667a-cc4d-454d-accf-355a3fcdf682 | libra-api-2      | ACTIVE | None       | Running     | os-net=10.255.255.24                                            |
    | c659c9a3-260a-4b85-9a1a-565549c9ad44 | libra-api-3      | ACTIVE | None       | Running     | os-net=10.255.255.25                                            |

5. Login / or script the next actions

6. Add the Ubuntu CloudArchive PPA

::

    $ sudo apt-get install -qy ubuntu-cloud-keyring
    $ sudo su -c "echo 'deb http://ubuntu-cloud.archive.canonical.com/ubuntu precise-updates/havana main' > /etc/apt/sources.list.d/cloudarchive.list"
    $ sudo apt-get -q update

7. Install python-keystoneclient

::

    $ sudo apt-get install -qy python-keystoneclient

8. Do steps in :doc:`ppa` for each instance

9. Install latest version of Libra

::

    $ sudo apt-get install -qy libra-api libra-admin-api

10. Copy the configuration file from one of the :ref:`libra-pool-mgm` instances
   to each instance.

11. Restart :ref:`libra-api` and :ref:`libra-admin-api` on each instance.

::

    $ for i in api admin-api; do sudo service libra-$i restart; done

12. Now you're done with the API services

13. Check that the logs have any errors.

14. See :ref:`install-verify` to verify that the system works!
