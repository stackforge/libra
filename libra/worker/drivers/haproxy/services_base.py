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
# under the License.


# Mapping of --haproxy-services options to a class
haproxy_services = {
    'ubuntu': 'libra.worker.drivers.haproxy.ubuntu_services.UbuntuServices'
}


class ServicesBase:
    """
    Operating system services needed by the HAProxy driver.

    NOTE: All of these methods must be implemented.
    """

    def service_stop(self):
        """ Stop the HAProxy service. """
        return NotImplementedError()

    def service_start(self):
        """ Start the HAProxy service. """
        return NotImplementedError()

    def service_restart(self):
        """ Restart the HAProxy service. """
        return NotImplementedError()

    def write_config(self):
        """ Write the HAProxy configuration file. """
        return NotImplementedError()

    def remove_configs(self):
        """ Remove current and saved HAProxy config files. """
        return NotImplementedError()
