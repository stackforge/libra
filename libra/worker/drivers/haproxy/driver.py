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

from libra.worker.drivers.base import LoadBalancerDriver


class HAProxyDriver(LoadBalancerDriver):

    def __init__(self):
        self._config_file = '/etc/haproxy/haproxy.cfg'
        self._backup_config = self._config_file + '.BKUP'
        self._config = dict()
        self.bind('0.0.0.0', 80)

    def _config_to_string(self):
        """
        Use whatever configuration parameters have been set to generate
        output suitable for a HAProxy configuration file.
        """
        output = []
        output.append('global')
        output.append('    daemon')
        output.append('    log 127.0.0.1 local0')
        output.append('    log 127.0.0.1 local1 notice')
        output.append('    maxconn 4096')
        output.append('    user haproxy')
        output.append('    group haproxy')
        output.append(
            '    stats socket /var/run/haproxy-stats.socket mode operator'
        )
        output.append('defaults')
        output.append('    log global')
        output.append('    mode http')
        output.append('    option httplog')
        output.append('    option dontlognull')
        output.append('    option redispatch')
        output.append('    maxconn 2000')
        output.append('    retries 3')
        output.append('    timeout connect 5000ms')
        output.append('    timeout client 50000ms')
        output.append('    timeout server 5000ms')
        output.append('    balance roundrobin')
        output.append('    cookie SERVERID rewrite')
        output.append('frontend http-in')
        output.append('    bind %s:%s' % (self._config['bind_address'],
                                          self._config['bind_port']))
        output.append('    default_backend servers')
        output.append('backend servers')

        serv_num = 1
        for (addr, port) in self._config['servers']:
            output.append('    server server%d %s:%s' % (serv_num, addr, port))
            serv_num += 1

        return '\n'.join(output) + '\n'

    def _write_config(self):
        """
        Generate the new config and replace the current config file.

        We'll first write out a new config to a temporary file, backup
        the production config file, then rename the temporary config to the
        production config.
        """
        config_str = self._config_to_string()
        tmpfile = '/tmp/haproxy.cfg'
        fh = open(tmpfile, 'w')
        fh.write(config_str)
        fh.close()

        # Copy any existing configuration file to a backup.
        if os.path.exists(self._config_file):
            copy_cmd = "/usr/bin/sudo /bin/cp %s %s" % (self._config_file,
                                                        self._backup_config)
            try:
                subprocess.check_output(copy_cmd.split(),
                                        stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                raise Exception("Failed to copy configuration file: %s" %
                                e.output.rstrip('\n'))

        # Move the temporary config file to production version.
        move_cmd = "/usr/bin/sudo /bin/mv %s %s" % (tmpfile, self._config_file)
        try:
            subprocess.check_output(move_cmd.split(), stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise Exception("Failed to write configuration file: %s" %
                            e.output.rstrip('\n'))

        # Reset server list
        self._config['servers'] = []

    def _restart(self):
        """ Restart the HAProxy service on the local machine. """
        cmd = '/usr/bin/sudo /usr/sbin/service haproxy restart'
        try:
            subprocess.check_output(cmd.split())
        except subprocess.CalledProcessError as e:
            raise Exception("Failed to restart HAProxy service: %s" %
                            e.output.rstrip('\n'))

    def _stop(self):
        """ Stop the HAProxy service on the local machine. """
        cmd = '/usr/bin/sudo /usr/sbin/service haproxy stop'
        try:
            subprocess.check_output(cmd.split())
        except subprocess.CalledProcessError as e:
            raise Exception("Failed to stop HAProxy service: %s" %
                            e.output.rstrip('\n'))

    def _start(self):
        """ Start the HAProxy service on the local machine. """
        cmd = '/usr/bin/sudo /usr/sbin/service haproxy start'
        try:
            subprocess.check_output(cmd.split())
        except subprocess.CalledProcessError as e:
            raise Exception("Failed to start HAProxy service: %s" %
                            e.output.rstrip('\n'))

    def _delete_configs(self):
        """ Delete current and backup configs on the local machine. """
        cmd = '/usr/bin/sudo /bin/rm -f %s %s' % (self._config_file,
                                                  self._backup_config)
        try:
            subprocess.check_output(cmd.split())
        except subprocess.CalledProcessError as e:
            raise Exception("Failed to delete HAProxy config files: %s" %
                            e.output.rstrip('\n'))

    ####################
    # Driver API Methods
    ####################

    def bind(self, address, port):
        self._config['bind_address'] = address
        self._config['bind_port'] = port

    def add_server(self, host, port):
        if 'servers' not in self._config:
            self._config['servers'] = []
        self._config['servers'].append((host, port))

    def create(self):
        self._write_config()
        self._restart()

    def suspend(self):
        self._stop()

    def enable(self):
        self._start()

    def delete(self):
        self._stop()
        self._delete_configs()
