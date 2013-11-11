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

import os
import subprocess

from libra.common.exc import DeletedStateError
from libra.worker.drivers.haproxy.stats import LBStatistics
from libra.worker.drivers.haproxy.services_base import ServicesBase
from libra.worker.drivers.haproxy.query import HAProxyQuery


class UbuntuServices(ServicesBase):
    """ Ubuntu-specific service implementation. """

    def __init__(self):
        self._haproxy_pid = '/var/run/haproxy.pid'
        self._config_file = '/etc/haproxy/haproxy.cfg'
        self._backup_config = self._config_file + '.BKUP'

    def syslog_restart(self):
        cmd = '/usr/bin/sudo -n /usr/sbin/service rsyslog restart'
        try:
            subprocess.check_output(cmd.split())
        except subprocess.CalledProcessError as e:
            raise Exception("Failed to restart rsyslog service: %s" % e)

    def service_stop(self):
        """ Stop the HAProxy service on the local machine. """
        cmd = '/usr/bin/sudo -n /usr/sbin/service haproxy stop'
        try:
            subprocess.check_output(cmd.split())
        except subprocess.CalledProcessError as e:
            raise Exception("Failed to stop HAProxy service: %s" % e)
        if os.path.exists(self._haproxy_pid):
            raise Exception("%s still exists. Stop failed." %
                            self._haproxy_pid)

    def service_start(self):
        """ Start the HAProxy service on the local machine. """
        cmd = '/usr/bin/sudo -n /usr/sbin/service haproxy start'
        try:
            subprocess.check_output(cmd.split())
        except subprocess.CalledProcessError as e:
            raise Exception("Failed to start HAProxy service: %s" % e)
        if not os.path.exists(self._haproxy_pid):
            raise Exception("%s does not exist. Start failed." %
                            self._haproxy_pid)

    def service_reload(self):
        """
        Reload the HAProxy config file in a non-intrusive manner.

        This assumes that /etc/init.d/haproxy is using the -sf option
        to the haproxy process.
        """
        cmd = '/usr/bin/sudo -n /usr/sbin/service haproxy reload'
        try:
            subprocess.check_output(cmd.split())
        except subprocess.CalledProcessError as e:
            raise Exception("Failed to reload HAProxy config: %s" % e)
        if not os.path.exists(self._haproxy_pid):
            raise Exception("%s does not exist. Reload failed." %
                            self._haproxy_pid)

    def sudo_copy(self, from_file, to_file):
        cmd = "/usr/bin/sudo -n /bin/cp %s %s" % (from_file, to_file)
        try:
            subprocess.check_output(cmd.split(),
                                    stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise Exception("Failed to copy file: %s\n%s"
                            % (e, e.output.rstrip('\n')))

    def sudo_chown(self, file, user, group):
        if group is None:
            cmd = "/usr/bin/sudo -n /bin/chown %s %s" % (user, file)
        else:
            cmd = "/usr/bin/sudo -n /bin/chown %s:%s %s" % (user, group, file)
        try:
            subprocess.check_output(cmd.split(),
                                    stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise Exception("Failed to change file ownership: %s\n%s"
                            % (e, e.output.rstrip('\n')))

    def sudo_rm(self, file):
        if not os.path.exists(file):
            return
        cmd = '/usr/bin/sudo -n /bin/rm -f %s' % file
        try:
            subprocess.check_output(cmd.split(),
                                    stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise Exception("Failed to delete %s\n%s"
                            % (file, e.output.rstrip('\n')))

    def write_config(self, config_str):
        """
        Generate the new config and replace the current config file.

        We'll first write out a new config to a temporary file, backup
        the production config file, then rename the temporary config to the
        production config.
        """
        tmpfile = '/tmp/haproxy.cfg'
        fh = open(tmpfile, 'w')
        fh.write(config_str)
        fh.close()

        # Validate the config
        check_cmd = "/usr/sbin/haproxy -f %s -c" % tmpfile
        try:
            subprocess.check_output(check_cmd.split(),
                                    stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise Exception("Configuration file is invalid: %s\n%s" %
                            (e, e.output.rstrip('\n')))

        # Copy any existing configuration file to a backup.
        if os.path.exists(self._config_file):
            self.sudo_copy(self._config_file, self._backup_config)

        # Move the temporary config file to production version.
        move_cmd = "/usr/bin/sudo -n /bin/mv %s %s" % (tmpfile,
                                                       self._config_file)
        try:
            subprocess.check_output(move_cmd.split(), stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise Exception("Failed to write configuration file: %s\n%s"
                            % (e, e.output.rstrip('\n')))

    def remove_configs(self):
        """ Delete current and backup configs on the local machine. """
        self.sudo_rm(self._config_file)
        self.sudo_rm(self._backup_config)

    def get_status(self, protocol=None):
        """
        Query HAProxy socket for node status on the given protocol.

        protocol
            One of the supported protocol names (http or tcp).

        This function will query the HAProxy statistics socket and pull out
        the values that it needs for the given protocol (which equates to one
        load balancer). The values are stored in a LBStatistics object that
        will be returned to the caller.

        The output of the socket query is in CSV format and defined here:

        http://cbonte.github.com/haproxy-dconv/configuration-1.4.html#9
        """

        if not os.path.exists(self._config_file):
            raise DeletedStateError("Load balancer is deleted.")
        if not os.path.exists(self._haproxy_pid):
            raise Exception("HAProxy is not running.")

        stats = LBStatistics()
        query = HAProxyQuery('/var/run/haproxy-stats.socket')

        node_status_list = query.get_server_status(protocol)
        for node, status in node_status_list:
            stats.add_node_status(node, status)

        return stats

    def get_statistics(self):
        if not os.path.exists(self._config_file):
            raise DeletedStateError("Load balancer is deleted.")
        if not os.path.exists(self._haproxy_pid):
            raise Exception("HAProxy is not running.")

        query = HAProxyQuery('/var/run/haproxy-stats.socket')
        results = query.get_bytes_out()

        return results
