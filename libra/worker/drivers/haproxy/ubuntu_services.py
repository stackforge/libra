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

import csv
import os
import subprocess

from libra.common.exc import ServiceUnavailable
from libra.common.lbstats import LBStatistics
from libra.worker.drivers.haproxy.services_base import ServicesBase


class UbuntuServices(ServicesBase):
    """ Ubuntu-specific service implementation. """

    def __init__(self):
        self._haproxy_pid = '/var/run/haproxy.pid'
        self._config_file = '/etc/haproxy/haproxy.cfg'
        self._backup_config = self._config_file + '.BKUP'

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
            copy_cmd = "/usr/bin/sudo -n /bin/cp %s %s" % (self._config_file,
                                                           self._backup_config)
            try:
                subprocess.check_output(copy_cmd.split(),
                                        stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                raise Exception("Failed to copy configuration file: %s\n%s"
                                % (e, e.output.rstrip('\n')))

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
        cmd = '/usr/bin/sudo -n /bin/rm -f %s %s' % (self._config_file,
                                                     self._backup_config)
        try:
            subprocess.check_output(cmd.split())
        except subprocess.CalledProcessError as e:
            raise Exception("Failed to delete HAProxy config files: %s" % e)

    def get_stats(self, protocol):
        """
        Query HAProxy socket for stats on the given protocol.

        protocol
            One of the supported protocol names (http or tcp).

        This function will query the HAProxy statistics socket and pull out
        the values that it needs for the given protocol (which equates to one
        load balancer). The values are stored in a LBStatistics object that
        will be returned to the caller.

        The output of the socket query is in CSV format and defined here:

        http://cbonte.github.com/haproxy-dconv/configuration-1.4.html#9
        """

        if not os.path.exists(self._haproxy_pid):
            raise ServiceUnavailable()

        stats = LBStatistics()

        cmd = 'echo "show stat" | ' \
              'sudo -n /usr/bin/socat stdio /var/run/haproxy-stats.socket'
        try:
            csv_output = subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            raise Exception("Failed to get statistics: %s" % e)

        # Remove leading '# ' from string and trailing newlines
        csv_output = csv_output[2:].rstrip()
        # Turn string into a list, removing last two empty lines
        csv_lines = csv_output.split('\n')

        proxy_name = "%s-in" % protocol.lower()
        service_name = "FRONTEND"

        reader = csv.DictReader(csv_lines)
        for row in reader:
            if row['pxname'] == proxy_name and row['svname'] == service_name:
                if row['bout']:
                    stats.bytes_out = long(row['bout'])
                if row['bin']:
                    stats.bytes_in = long(row['bin'])
                break

        return stats
