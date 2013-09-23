.. _ppa:

=========
Libra PPA
=========

Currently we require a PPA that is provided by the HPCS LBaaS / Libra team in order
to get the right versions of the dependencies. So we'll need to setup a PPA.

To add it to your Ubuntu node follow the instructions below.


Adding the PPA
==============

1. Install a utility package

::

    $ sudo apt-get install -qy python-software-properties

2. Add the PPA

::

    $ sudo apt-add-repository ppa:libra-core/ppa

3. Update package indexes

::

    $ sudo apt-get update -q
