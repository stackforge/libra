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

    def syslog_restart(self):
        """ Restart syslog daemon. """
        raise NotImplementedError()

    def service_stop(self):
        """ Stop the HAProxy service. """
        raise NotImplementedError()

    def service_start(self):
        """ Start the HAProxy service. """
        raise NotImplementedError()

    def service_reload(self):
        """ Reload the HAProxy config file. """
        raise NotImplementedError()

    def write_config(self, config_str):
        """ Write the HAProxy configuration file. """
        raise NotImplementedError()

    def remove_configs(self):
        """ Remove current and saved HAProxy config files. """
        raise NotImplementedError()

    def get_stats(self):
        """ Get the stats from HAProxy. """
        raise NotImplementedError()

    def sudo_copy(self, from_file, to_file):
        """ Do a privileged file copy. """
        raise NotImplementedError()

    def sudo_chown(self, file, user, group):
        """ Do a privileged file ownership change. """
        raise NotImplementedError()

    def sudo_rm(self, file):
        """ Do a privileged file delete. """
        raise NotImplementedError()
