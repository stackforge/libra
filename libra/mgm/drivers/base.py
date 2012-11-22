# Copyright 2012 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations


# Mapping of --driver options to a class
known_drivers = {
    'hp_rest': 'libra.mgm.drivers.hp_rest.driver.HPRestDriver',
    'dummy': 'libra.mgm.drivers.dummy.driver.DummyDriver'
}


class MgmDriver(object):
    """
    Pool manager device driver base class.

    This defines the API for interacting with various APIs.
    Drivers for these appliances should inherit from this class and implement
    the relevant API methods that it can support.
    """

    def get_free_count(self):
        """ Get a count of how many nodes are free. """
        raise NotImplementedError()

    def add_node(self, name, address):
        """ Add a node to a device. """
        raise NotImplementedError()

    def is_online(self):
        """ Returns false if no API server is available """
        raise NotImplementedError()

    def get_url(self):
        """ Gets the URL we are currently connected to """
        raise NotImplementedError()
