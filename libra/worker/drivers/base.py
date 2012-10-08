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
    'haproxy': 'libra.worker.drivers.haproxy.driver.HAProxyDriver'
}


class LoadBalancerDriver(object):
    """
    Load balancer device driver base class.

    This defines the API for interacting with various load balancing
    appliances. Drivers for these appliances should inherit from this
    class and implement the relevant API methods that it can support.

    Generally, an appliance driver should queue up any changes made
    via these API calls until the activate() method is called.
    """

    def bind(self, address, port):
        """ Set proxy listening interface and port. """
        raise NotImplementedError()

    def add_server(self, host, port):
        """ Add a server for which we will proxy. """
        raise NotImplementedError()

    def create(self):
        """ Create the load balancer. """
        raise NotImplementedError()

    def suspend(self):
        """ Suspend the load balancer. """
        raise NotImplementedError()

    def enable(self):
        """ Enable a suspended load balancer. """
        raise NotImplementedError()

    def delete(self):
        """ Delete a load balancer. """
        raise NotImplementedError()
