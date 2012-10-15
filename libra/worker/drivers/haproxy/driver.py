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

from libra.common.utils import import_class
from libra.worker.drivers.base import LoadBalancerDriver
from libra.worker.drivers.haproxy.services_base import ServicesBase


class HAProxyDriver(LoadBalancerDriver):

    def __init__(
        self,
        ossvc='libra.worker.drivers.haproxy.ubuntu_services.UbuntuServices'
    ):
        ossvc_driver = import_class(ossvc)
        self.ossvc = ossvc_driver()
        if not isinstance(self.ossvc, ServicesBase):
            raise Exception('Class is not derived from ServicesBase: %s' %
                            ossvc.__class__)
        self._init_config()

    def _init_config(self):
        self._config = dict()
        self.set_protocol('HTTP', 80)
        self.set_algorithm(self.ROUNDROBIN)

    def _bind(self, address, port):
        self._config['bind_address'] = address
        self._config['bind_port'] = port

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
        output.append('    mode %s' % self._config['mode'])
        output.append('    option httplog')
        output.append('    option dontlognull')
        output.append('    option redispatch')
        output.append('    maxconn 2000')
        output.append('    retries 3')
        output.append('    timeout connect 5000ms')
        output.append('    timeout client 50000ms')
        output.append('    timeout server 5000ms')
        output.append('    balance %s' % self._config['algorithm'])
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

    ####################
    # Driver API Methods
    ####################

    def init(self):
        self._init_config()

    def add_server(self, host, port):
        if 'servers' not in self._config:
            self._config['servers'] = []
        self._config['servers'].append((host, port))

    def set_protocol(self, protocol, port=None):
        proto = protocol.lower()
        if proto not in ('tcp', 'http', 'health'):
            raise Exception("Invalid protocol: %s" % protocol)
        self._config['mode'] = proto

        if port is None:
            if proto == 'tcp':
                raise Exception('Port is required for TCP protocol.')
            elif proto == 'http':
                self._bind('0.0.0.0', 80)
        else:
            self._bind('0.0.0.0', port)

    def set_algorithm(self, algo):
        if algo == self.ROUNDROBIN:
            self._config['algorithm'] = 'roundrobin'
        elif algo == self.LEASTCONN:
            self._config['algorithm'] = 'leastconn'
        else:
            raise Exception('Invalid algorithm')

    def create(self):
        self.ossvc.write_config()
        self.ossvc.service_stop()
        self.ossvc.service_start()

    def suspend(self):
        self.ossvc.service_stop()

    def enable(self):
        self.ossvc.service_start()

    def delete(self):
        self.ossvc.service_stop()
        self.ossvc.remove_configs()
