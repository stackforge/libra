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

import datetime
import os
import subprocess

from oslo.config import cfg

from libra.common import exc
from libra.openstack.common import log
from libra.worker.drivers.haproxy import query
from libra.worker.drivers.haproxy import services_base
from libra.worker.drivers.haproxy import stats

LOG = log.getLogger(__name__)


class UbuntuServices(services_base.ServicesBase):
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
        load balancer).

        The output of the socket query is in CSV format and defined here:

        http://cbonte.github.com/haproxy-dconv/configuration-1.4.html#9
        """

        if not os.path.exists(self._config_file):
            raise exc.DeletedStateError("Load balancer is deleted.")
        if not os.path.exists(self._haproxy_pid):
            raise Exception("HAProxy is not running.")

        q = query.HAProxyQuery('/var/run/haproxy-stats.socket')
        return q.get_server_status(protocol)

    def get_statistics(self):
        if not os.path.exists(self._config_file):
            raise exc.DeletedStateError("Load balancer is deleted.")
        if not os.path.exists(self._haproxy_pid):
            raise Exception("HAProxy is not running.")

        q = query.HAProxyQuery('/var/run/haproxy-stats.socket')
        results = q.get_bytes_out()

        stats_file = cfg.CONF['worker:haproxy']['statsfile']
        stats_mgr = stats.StatisticsManager(stats_file)

        # Read the contents (if any) of the existing file.
        stats_mgr.read()

        # Calculate a new start value for our reporting time range,
        # which should be just after the last reported end value. If
        # there is no start value, then we haven't recorded one yet
        # (i.e., haven't reported any stats yet) so use the current time.
        new_start = stats_mgr.get_last_end()
        if new_start is None:
            new_start = datetime.datetime.utcnow()
        else:
            new_start = new_start + datetime.timedelta(microseconds=1)

        new_end = datetime.datetime.utcnow()
        prev_tcp_bo = stats_mgr.get_last_tcp_bytes()
        prev_http_bo = stats_mgr.get_last_http_bytes()
        tcp_bo = 0
        http_bo = 0

        for proto, bytes_out in results:
            if proto.lower() == 'http':
                http_bo = bytes_out
            elif proto.lower() == 'tcp':
                tcp_bo = bytes_out

        # If our totals that we previously recorded are greater than the
        # totals we have now, then somehow HAProxy was restarted outside
        # of the worker's control, so we have no choice but to zero the
        # values to avoid overcharging on usage.
        if (prev_tcp_bo > tcp_bo) or (prev_http_bo > http_bo):
            LOG.warn("Forced reset of HAProxy statistics")
            prev_tcp_bo = 0
            prev_http_bo = 0

        # Record totals for each protocol for comparison in the next request.
        stats_mgr.save_last_queried(new_start, new_end, tcp_bo, http_bo)

        # We are to deliver the number of bytes out since our last report,
        # not the total, so calculate that here.
        incremental_results = []
        for proto, bytes_out in results:
            if proto.lower() == 'http':
                incremental_results.append((proto, http_bo - prev_http_bo))
            elif proto.lower() == 'tcp':
                incremental_results.append((proto, tcp_bo - prev_tcp_bo))

        return str(new_start), str(new_end), incremental_results
