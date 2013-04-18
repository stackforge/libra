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

import gzip
import hashlib
import os
import re
from datetime import datetime
from swiftclient import client as sc

from libra.openstack.common import importutils
from libra.worker.drivers.base import LoadBalancerDriver
from libra.worker.drivers.haproxy.services_base import ServicesBase


class HAProxyDriver(LoadBalancerDriver):

    def __init__(self, ossvc, user, group):
        self.user = user
        self.group = group
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

            # HTTP specific options for the frontend
            if proto == 'http':
                output.append('    option httplog')
            # TCP specific options for the frontend
            elif proto == 'tcp':
                output.append('    option tcplog')

            #------------------------
            # Backend configuration
            #------------------------
            output.append('backend %s-servers' % proto)
            output.append('    mode %s' % proto)
            output.append('    balance %s' % protocfg['algorithm'])

            # HTTP specific options for the backend
            if proto == 'http':
                output.append('    cookie SERVERID rewrite')

            for (addr, port, weight) in protocfg['servers']:
                output.append('    server server%d %s:%s weight %d' %
                              (serv_num, addr, port, weight))
                serv_num += 1

        return '\n'.join(output) + '\n'

    def _archive_swift(self, endpoint, token, basepath, lbid, proto):
        """
        Archive HAProxy log files into swift.

        endpoint - Object store endpoint
        token - Authorization token
        basepath - Container base path
        lbid - Load balancer ID
        proto - Protocol of the load balancer we are archiving

        Note: It should be acceptable for exceptions to be thrown here as
        the controller should wrap these up nicely in a message back to the
        API server.
        """

        proto = proto.lower()

        reallog = '/mnt/log/haproxy.log'

        if not os.path.exists(reallog):
            raise Exception('No HAProxy logs found')

        # We need a copy we can read
        reallog_copy = '/tmp/haproxy.log'
        self.ossvc.sudo_copy(reallog, reallog_copy)
        self.ossvc.sudo_chown(reallog_copy, self.user, self.group)

        # Extract contents from the log based on protocol. This is
        # because each protocol (tcp or http) represents a separate
        # load balancer in Libra. See _config_to_string() for the
        # frontend and backend names we search for below.

        filtered_log = '/tmp/haproxy-' + proto + '.log'
        fh = open(filtered_log, 'wb')
        for line in open(reallog_copy, 'rb'):
            if re.search(proto + '-in', line):
                fh.write(line)
            elif re.search(proto + '-servers', line):
                fh.write(line)
        fh.close()
        os.remove(reallog_copy)

        # Compress the filtered log and generate the MD5 checksum value.
        # We generate object name using UTC timestamp. The MD5 checksum of
        # the compressed file is used to guarantee Swift properly receives
        # the file contents.

        ts = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        objname = 'haproxy-' + ts + '.log.gz'
        compressed_file = '/tmp/' + objname

        gzip_in = open(filtered_log, 'rb')
        gzip_out = gzip.open(compressed_file, 'wb')
        gzip_out.writelines(gzip_in)
        gzip_out.close()
        gzip_in.close()
        os.remove(filtered_log)

        etag = hashlib.md5(open(compressed_file, 'rb').read()).hexdigest()

        # We now have a file to send to Swift for storage. We'll connect
        # using the pre-authorized token passed to use for the given endpoint.
        # Then make sure that we have a proper container name for this load
        # balancer, and place the compressed file in that container. Creating
        # containers is idempotent so no need to check if it already exists.

        object_path = '/'.join([lbid, objname])
        logfh = open(compressed_file, 'rb')

        try:
            conn = sc.Connection(preauthurl=endpoint, preauthtoken=token)
            conn.put_container(basepath)
            conn.put_object(container=basepath,
                            obj=object_path,
                            etag=etag,
                            contents=logfh)
        except Exception as e:
            logfh.close()
            os.remove(compressed_file)
            errmsg = "Failure during Swift operations. Swift enabled?"
            errmsg = errmsg + "\nException was: %s" % e
            raise Exception(errmsg)

        logfh.close()
        os.remove(compressed_file)

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

    def add_server(self, protocol, host, port, weight=1):
        proto = protocol.lower()
        if weight is None:
            weight = 1

        try:
            weight = int(weight)
        except ValueError:
            raise Exception("Non-integer 'weight' value: '%s'" % weight)

        if weight > 256:
            raise Exception("Server 'weight' %d exceeds max of 256" % weight)

        if 'servers' not in self._config[proto]:
            self._config[proto]['servers'] = []
        self._config[proto]['servers'].append((host, port, weight))

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

    def get_stats(self, protocol):
        return self.ossvc.get_stats(protocol)

    def archive(self, method, params):
        """
        Implementation of the archive() API call.

        method
            Method we use for archiving the files.

        params
            Dictionary with parameters needed for archiving. The keys of
            the dictionary will vary based on the value of 'method'.
        """

        if method == 'swift':
            return self._archive_swift(params['endpoint'],
                                       params['token'],
                                       params['basepath'],
                                       params['lbid'],
                                       params['proto'])
        else:
            raise Exception("Driver does not support archive method '%s'" %
                            method)
