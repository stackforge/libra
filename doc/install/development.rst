=======================
Development environment
=======================

Libra is a system to provide LoadBalancing as a Service on top of
various platforms. It is comprised of four components :ref:`libra-api`,
:ref:`libra-admin-api`, :ref:`libra-pool-mgm` and :ref:`libra-worker`,
supported by a few other open source components. For more information see
:doc:`/architecture/index`.


Development environment
+++++++++++++++++++++++
This guide will walk you through howto setup a development environment for Libra
using:

* 1 Node for the API, Admin API and Pool mgm with MySQL
* n+ Nodes for workers that is going to run HAProxy
* Ubuntu 12.04 as our OS of choice

Common steps
============

1. Install general system dependencies

::

    $ sudo apt-get install -qy python-virtualenv python-pip python-dev git gcc

2. Clone the repo from Stackforge at GitHub

::

    $ git clone https://github.com/stackforge/libra.git
    $ cd libra

3. Create a libra user

::

    $ sudo adduser --disabled-login libra

4. Create needed directories

::

    $ sudo mkdir -p /var/run/libra /var/log/libra
    $ sudo chown libra:libra /var/run/libra /var/log/libra


Installing
==========

.. index::
    double: install; libra

1. Do steps in :doc:`ppa`

2. Do steps in 'Common steps'

3. Install dependencies

::

    $ sudo apt-get install -qy gearman-job-server mysql-server

4. Setup a VirtualEnvironment

.. note::

    This is to not interfere with systemwide libraries.

::

    $ virtualenv .venv
    $ . .venv/bin/activate

5. Install python-gearman

.. note::

    This is a custom version with patches commited upstream but not release yet.

::

   $ pip install https://launchpad.net/~libra-core/+archive/ppa/+files/gearman_2.0.2.git3.orig.tar.gz

6. Install dependencies using pip

::

    $ pip install -r requirements.txt -r test-requirements.txt


7. Install python-keystoneclient

::

    $ pip install python-keystoneclient

8. Install Libra in development mode

::

    $ python setup.py develop

9. Copy the configuration file to /etc

::

    $ sudo cp etc/sample_libra.cfg /etc/libra.cfg

10. Configure libra

::

    $ sudo vi /etc/libra.cfg

.. note::

   See :ref:`configuration` for how to proceed for various options.

   You should at least configure the variables needed for your environment.


Setup database and gearman
==========================
1. Import the initial database

::

    $ mysql -p < libra/common/api/lbaas.sql

2. Change the listening address of Gearman server

::

    $ sudo vi /etc/default/gearman-job-server

3. Restart gearman

::

    $ sudo service gearman-job-server restart


Bring up services
=================

1. Start the Pool Manager

::

    $ libra_pool_mgm --config-file /etc/libra.cfg --log-dir /var/log/libra/

2. Start Admin API & API services

::

    $ libra_admin_api --config-file /etc/libra.cfg --log-dir /var/log/libra/
    $ libra_api --config-file /etc/libra.cfg --log-dir /var/log/libra/


Creating a Worker Image
=======================

.. note::

    In this setup we'll be using OpenStack as the underlying provider for our Libra Worker nodes to run HAProxy on.

1. Boot a server using Nova

.. note::

    You should at least open (for now at least) port 22 for ssh.

    --nic argument is only needed if you have multiple networks.
    --security-groups is not needed at the time if you have 22 in default

::

    $ nova boot --flavor <flavour id or name> --image <image id of ubuntu precise> --key-name default --nic net-id=<network id> --security-groups=<your security groups> worker

2. Create a floating ip

::

    $ neutron floatingip-create <external network name>

3. Assign a floating ip to the instance

.. note::

    You can view all the ports by issuing `neutron port-list`.

::

    $ neutron floatingip-associate <floating ip id> <port id>

4. Login to the instance

::

    $ ssh root@<ip>

5. Do steps in 'Common steps'

6. Install HAProxy

::

    $ apt-get install -qy haproxy socat


7. Install python-gearman

.. note::

    This is a custom version with patches commited upstream but not release yet.
    
::

   $ pip install  https://launchpad.net/~libra-core/+archive/ppa/+files/gearman_2.0.2.git3.orig.tar.gz

8. Install dependencies using pip

::

    $ pip install -r requirements.txt -r test-requirements.txt

9. Install Libra in development mode

::

    $ python setup.py develop

10. Install an Upstart job

.. note::

    You will also need to copy your libra.cnf to the worker machine, and update libra-worker.conf to use it (the default is /etc/libra/libra.cnf).
    There is also an additional logging configuration file to install. 
    You may want to test that the service starts up appropriately before moving to the next step.
    
::

    $ mkdir /etc/libra
    $ wget https://raw2.github.com/pcrews/lbaas-salt/master/lbaas-haproxy-base/logging_worker.cfg -O /etc/libra/logging_worker.cfg
    $ wget https://raw2.github.com/pcrews/lbaas-salt/master/lbaas-haproxy-base/libra-worker.conf -O /etc/init/libra_worker.conf

11. Make a snapshot of the worker image

::

    $ nova image-create worker libra-worker

12. At the libra-poo-mgm node change the 'nova_image' setting to the value of your newly created snapshot

.. note::

    To get the ID of the snapshot do
    nova image-show libra-worker | grep -w id | cut -d '|' -f3

::

    $ sudo vi /etc/libra.cfg

13. Restart libra_pool_mgm

::

    $ killall -9 libra_pool_mgm
    $ libra_pool_mgm --config-file /etc/libra.cfg --log-dir /var/log/libra/

Verifying that it works
=======================

If you have done all correctly you should be able to do something like the
below command on the node that has the :ref:`libra-pool-mgm`

::

    $ less +F /var/log/libra/libra_pool_mgm.log
