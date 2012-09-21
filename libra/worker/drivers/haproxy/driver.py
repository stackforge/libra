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

from libra.worker.drivers.base import LoadBalancerDriver


class HAProxyDriver(LoadBalancerDriver):

    def __init__(self):
        self._config_file = '/etc/haproxy/haproxy.cfg'
        self._servers = []
        self.bind('0.0.0.0', 80)

    def _write_config(self):
        pass

    def _restart(self):
        pass

    ####################
    # Driver API Methods
    ####################

    def bind(self, address, port):
        self._bind_address = address
        self._bind_port = port

    def add_server(self, host, port):
        self._servers.append((host, port))

    def activate(self):
        self._write_config()
        self._restart()
