Diskimage Builder
=================

Building Libra Images using Diskimage Builder.


Setup the builder
-----------------

1. Set DIB path

::

    $ echo 'export DIB_PATH=$HOME/diskimage-builder' >> ~/.bashrc

2. Clone the repository "git://github.com:openstack/diskimage-builder" locally.

::

    $ git clone git://github.com:openstack/diskimage-builder $DIB_PATH

3. Add DIB bin to PATH and DIB directory to your directory to your env.

::

    $ echo 'export PATH=$PATH:$DIB_PATH/bin' >> ~/.bashrc
    $ . ~/.bashrc


4. Setup some variables

::

    $ echo 'export LIBRA_ELEMENTS=$HOME/libra-elements' >> ~/.bashrc
    $ . ~/.bashrc

5. Clone the 'libra-elements' repository

::

    $ git clone git://github.com/ekarlso/libra-elements $LIBRA_ELEMENTS


6. Export the following variable to your .bashrc. Then source it.

::

    $ export ELEMENTS_PATH=$DIB_PATH/elements:$LIBRA_ELEMENTS/elements


Supported distros
-----------------

Currently the supported distributions for DIB are:

.. note::

    There are not support in the elements nor in the packages for anythign else at this time

* precise


Worker image
------------

To generate a worker image, do

::

    DIB_RELEASE=precise disk-image-create "libra-worker" -o libra-worker.qcow2


API node
--------

To generate a API image, do

::

    DIB_RELEASE=precise disk-image-create "libra-api" -o libra-api.qcow2

Or to put both the API and Admin API on the same image

::

    DIB_RELEASE=precise disk-image-create "libra-api libra-admin-api" -o libra-api.qcow2


Pool Manager image
------------------

To generate a API image, do

::

    DIB_RELEASE=precise disk-image-create "libra-pool-mgr" -o libra-pool-mgr.qcow2
