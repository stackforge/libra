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
    via these API calls until the create() method is called.

    This design allows for a single load balancer to support multiple
    protocols simultaneously. Each protocol added via the add_protocol()
    method is assumed to be unique, and one protocol per port. This same
    protocol is then supplied to other methods (e.g., add_server() and
    set_algorithm()) to make changes for that specific protocol.
    """

    # Load balancer algorithms
    ROUNDROBIN = 1
    LEASTCONN = 2

    def init(self):
        """ Allows the driver to do any initialization for a new config. """
        raise NotImplementedError()

    def add_protocol(self, protocol, port):
        """ Add a supported protocol and listening port for the instance. """
        raise NotImplementedError()

    def add_server(self, protocol, host, port, weight, backup):
        """ Add a server for the protocol for which we will proxy. """
        raise NotImplementedError()

    def set_algorithm(self, protocol, algo):
        """ Set the algorithm used by the load balancer for this protocol. """
        raise NotImplementedError()

    def add_monitor(self, protocol, mtype, delay, timeout, attempts, path):
        """
        Add a health check monitor for this protocol.

        protocol
           Protocol of the load balancer (HTTP, TCP)
        mtype
           Monitor type (CONNECT, HTTP)
        delay
           Minimum time in seconds between regular calls to a monitor.
        timeout
           Maximum number of seconds for a monitor to wait for a connection
           to be established to the node before it times out. The value must
           be less than the delay value.
        attempts
           Number of permissible monitor failures before removing a node from
           rotation.
        path
           The HTTP path used in the HTTP request by the monitor. This must
           be a string beginning with a / (forward slash). The monitor
           expects a response from the node with an HTTP status code of 200.
        """
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

    def get_status(self, protocol):
        """
        Get load balancer status for specified protocol.

        Returns a list of tuples containing (in this order):
          - node ID
          - node status
        """
        raise NotImplementedError()

    def get_statistics(self):
        """
        Get load balancer statistics for all LBs on the device.

        Returns a tuple containing (in this order):
          - start timestamp for the reporting period as a string
          - end timestamp for the reporting period as a string
          - list of tuples containing (in this order):
             - protocol for the LB ('tcp' or 'http') as a string
             - bytes out for this LB for this reporting period as an int
        """
        raise NotImplementedError()

    def archive(self, method, params):
        """ Archive the load balancer logs using the specified method. """
        raise NotImplementedError()
