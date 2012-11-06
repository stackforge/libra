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

from libra.openstack.common import importutils
from libra.worker.drivers.base import LoadBalancerDriver
from libra.worker.drivers.haproxy.services_base import ServicesBase


class HAProxyDriver(LoadBalancerDriver):

    def __init__(self, ossvc):
        ossvc_driver = importutils.import_class(ossvc)
        self.ossvc = ossvc_driver()
        if not isinstance(self.ossvc, ServicesBase):
            raise Exception('Class is not derived from ServicesBase: %s' %
                            ossvc.__class__)
        self._init_config()

    def _init_config(self):
        self._config = dict()

    def _bind(self, protocol, address, port):
        self._config[protocol]['bind_address'] = address
        self._config[protocol]['bind_port'] = port

    def _config_to_string(self):
        """
        Use whatever configuration parameters have been set to generate
        output suitable for a HAProxy configuration file.
        """
        output = []
        output.append('global')
        output.append('    daemon')
        output.append('    log /dev/log local0')
        output.append('    log /dev/log local1 notice')
        output.append('    maxconn 4096')
        output.append('    user haproxy')
        output.append('    group haproxy')
        output.append(
            '    stats socket /var/run/haproxy-stats.socket mode operator'
        )
        output.append('defaults')
        output.append('    log global')
        output.append('    option dontlognull')
        output.append('    option redispatch')
        output.append('    maxconn 2000')
        output.append('    retries 3')
        output.append('    timeout connect 5000ms')
        output.append('    timeout client 50000ms')
        output.append('    timeout server 5000ms')

        serv_num = 1

        for proto in self._config:
            protocfg = self._config[proto]

            #------------------------
            # Frontend configuration
            #------------------------
            output.append('frontend %s-in' % proto)
            output.append('    mode %s' % proto)
            output.append('    bind %s:%s' % (protocfg['bind_address'],
                                              protocfg['bind_port']))
            output.append('    default_backend %s-servers' % proto)

            # HTTP specific options
            if proto == 'http':
                output.append('    option httplog')
                output.append('    cookie SERVERID rewrite')
            # TCP specific options
            elif proto == 'tcp':
                output.append('    option tcplog')

            #------------------------
            # Backend configuration
            #------------------------
            output.append('backend %s-servers' % proto)
            output.append('    mode %s' % proto)
            output.append('    balance %s' % protocfg['algorithm'])

            for (addr, port) in protocfg['servers']:
                output.append('    server server%d %s:%s' %
                              (serv_num, addr, port))
                serv_num += 1

        return '\n'.join(output) + '\n'

    ####################
    # Driver API Methods
    ####################

    def init(self):
        self._init_config()

    def add_protocol(self, protocol, port=None):
        proto = protocol.lower()
        if proto not in ('tcp', 'http', 'health'):
            raise Exception("Unsupported protocol: %s" % protocol)
        if proto in self._config:
            raise Exception("Protocol '%s' is already defined." % protocol)
        else:
            self._config[proto] = dict()

        if port is None:
            if proto == 'tcp':
                raise Exception('Port is required for TCP protocol.')
            elif proto == 'http':
                self._bind(proto, '0.0.0.0', 80)
        else:
            self._bind(proto, '0.0.0.0', port)

    def add_server(self, protocol, host, port):
        proto = protocol.lower()
        if 'servers' not in self._config[proto]:
            self._config[proto]['servers'] = []
        self._config[proto]['servers'].append((host, port))

    def set_algorithm(self, protocol, algo):
        proto = protocol.lower()
        if algo == self.ROUNDROBIN:
            self._config[proto]['algorithm'] = 'roundrobin'
        elif algo == self.LEASTCONN:
            self._config[proto]['algorithm'] = 'leastconn'
        else:
            raise Exception('Invalid algorithm: %s' % protocol)

    def create(self):
        self.ossvc.write_config(self._config_to_string())
        self.ossvc.service_stop()
        self.ossvc.service_start()

    def suspend(self):
        self.ossvc.service_stop()

    def enable(self):
        self.ossvc.service_start()

    def delete(self):
        self.ossvc.service_stop()
        self.ossvc.remove_configs()
