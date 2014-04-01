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

    def __init__(self, ossvc, user, group, haproxy_logfile=None):
        self.haproxy_log = haproxy_logfile
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
        stats_socket = "/var/run/haproxy-stats.socket"
        output = []
        output.append('global')
        output.append('    daemon')
        output.append('    log /dev/log local0')
        output.append('    maxconn 4096')
        output.append('    user haproxy')
        output.append('    group haproxy')

        # group can be None, but user cannot
        if self.group is None:
            output.append(
                '    stats socket %s user %s mode operator' %
                (stats_socket, self.user)
            )
        else:
            output.append(
                '    stats socket %s user %s group %s mode operator' %
                (stats_socket, self.user, self.group)
            )

        output.append('defaults')
        output.append('    log global')
        output.append('    option dontlognull')
        output.append('    option redispatch')
        output.append('    maxconn 50000')

        for proto in self._config:
            protocfg = self._config[proto]
            real_proto = proto
            if proto == 'galera':
                real_proto = 'tcp'

            # ------------------------
            # Frontend configuration
            # ------------------------
            output.append('frontend %s-in' % real_proto)
            output.append('    mode %s' % real_proto)
            output.append('    bind %s:%s' % (protocfg['bind_address'],
                                              protocfg['bind_port']))
            output.append('    timeout client %sms' %
                          protocfg['timeouts']['timeout_client'])
            output.append('    default_backend %s-servers' % real_proto)

            # HTTP specific options for the frontend
            if real_proto == 'http':
                output.append('    option httplog')
            # TCP specific options for the frontend
            elif real_proto == 'tcp':
                output.append('    option tcplog')

            # ------------------------
            # Backend configuration
            # ------------------------

            output.append('backend %s-servers' % real_proto)
            output.append('    mode %s' % real_proto)
            output.append('    balance %s' % protocfg['algorithm'])
            output.append('    timeout connect %sms' %
                          protocfg['timeouts']['timeout_connect'])
            output.append('    timeout server %sms' %
                          protocfg['timeouts']['timeout_server'])
            output.append('    retries %s' % protocfg['timeouts']['retries'])

            # default healthcheck if none specified
            monitor = 'check inter 30s'

            # HTTP specific options for the backend
            if real_proto == 'http':
                output.append('    cookie SERVERID insert indirect')
                output.append('    option httpclose')
                output.append('    option forwardfor')

                if 'monitor' in self._config[proto]:
                    mon = self._config[proto]['monitor']
                    if mon['type'] == 'http':
                        output.append('    option httpchk GET %s' %
                                      mon['path'])
                    # our timeout will be connect + read time
                    output.append('    timeout check %ds' % mon['timeout'])
                    # intentionally set rise/fall to the same value
                    monitor = "check inter %ds rise %d fall %d" % (
                              mon['delay'], mon['attempts'], mon['attempts'])

                for (node_id, addr, port, wt, bkup) in protocfg['servers']:
                    if bkup:
                        output.append(
                            '    server id-%s %s:%s backup cookie id-%s'
                            ' weight %d %s' %
                            (node_id, addr, port, node_id, wt, monitor)
                        )
                    else:
                        output.append(
                            '    server id-%s %s:%s cookie id-%s'
                            ' weight %d %s' %
                            (node_id, addr, port, node_id, wt, monitor)
                        )

            # TCP or Galera specific options for the backend
            #
            # The Galera protocol is a convenience option that lets us set
            # our TCP options specifically for load balancing between Galera
            # database nodes in a manner that helps avoid deadlocks. A main
            # node is chosen which will act as the 'write' node, sending all
            # updates to this one node.

            else:

                # No stick table for Galera protocol since we want to return to
                # the main backend node once it is available after being down.
                if proto == 'tcp':
                    # Allow session stickiness for TCP connections. The 'size'
                    # value affects memory usage (about 50 bytes per entry).
                    output.append(
                        '    stick-table type ip size 200k expire 30m'
                    )
                    output.append('    stick store-request src')
                    output.append('    stick match src')

                if 'monitor' in self._config[proto]:
                    mon = self._config[proto]['monitor']
                    if mon['type'] == 'http':
                        output.append('    option httpchk GET %s' %
                                      mon['path'])
                    # our timeout will be connect + read time
                    output.append('    timeout check %ds' % mon['timeout'])
                    # intentionally set rise/fall to the same value
                    monitor = "check inter %ds rise %d fall %d" % (
                              mon['delay'], mon['attempts'], mon['attempts'])

                for (node_id, addr, port, wt, bkup) in protocfg['servers']:
                    if bkup:
                        output.append(
                            '    server id-%s %s:%s backup weight %d %s' %
                            (node_id, addr, port, wt, monitor)
                        )
                    else:
                        output.append(
                            '    server id-%s %s:%s weight %d %s' %
                            (node_id, addr, port, wt, monitor)
                        )

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

        if not os.path.exists(self.haproxy_log):
            raise Exception('No HAProxy logs found')

        # We need a copy we can read
        reallog_copy = '/tmp/haproxy.log'
        self.ossvc.sudo_copy(self.haproxy_log, reallog_copy)
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
        if proto not in ('tcp', 'http', 'galera'):
            raise Exception("Unsupported protocol: %s" % protocol)
        if proto in self._config:
            raise Exception("Protocol '%s' is already defined." % protocol)
        else:
            self._config[proto] = dict()

        if port is None:
            if proto in ('tcp', 'galera'):
                raise Exception('Port is required for this protocol.')
            elif proto == 'http':
                self._bind(proto, '0.0.0.0', 80)
        else:
            self._bind(proto, '0.0.0.0', port)

    def add_server(self, protocol, node_id, host, port,
                   weight=1, backup=False):
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

        if proto == 'galera':
            for (n, h, p, w, b) in self._config[proto]['servers']:
                if b is False and backup is False:
                    raise Exception("Galera protocol does not accept more"
                                    " than one non-backup node")

        self._config[proto]['servers'].append((node_id, host, port,
                                               weight, backup))

    def set_algorithm(self, protocol, algo):
        proto = protocol.lower()
        if algo == self.ROUNDROBIN:
            self._config[proto]['algorithm'] = 'roundrobin'
        elif algo == self.LEASTCONN:
            self._config[proto]['algorithm'] = 'leastconn'
        else:
            raise Exception('Invalid algorithm: %s' % protocol)

    def add_monitor(self, protocol, mtype, delay, timeout, attempts, path):
        proto = protocol.lower()
        if mtype.lower() not in ['connect', 'http']:
            raise Exception('Invalid monitor type: %s' % mtype)

        # default values
        if delay is None:
            delay = 30
        if attempts is None:
            attempts = 2
        if timeout is None:
            timeout = delay
        if (path is None) or (len(path) == 0):
            path = '/'

        if path[0] != '/':
            path = '/' + path

        try:
            delay = int(delay)
        except ValueError:
            raise Exception("Non-integer 'delay' value: '%s'" % delay)

        try:
            timeout = int(timeout)
        except ValueError:
            raise Exception("Non-integer 'timeout' value: '%s'" % timeout)

        try:
            attempts = int(attempts)
        except ValueError:
            raise Exception("Non-integer 'attempts' value: '%s'" % attempts)

        if timeout > delay:
            raise Exception("Timeout cannot be greater than delay")

        self._config[proto]['monitor'] = {'type': mtype.lower(),
                                          'delay': delay,
                                          'timeout': timeout,
                                          'attempts': attempts,
                                          'path': path}

    def create(self):
        self.ossvc.write_config(self._config_to_string())
        self.ossvc.service_reload()

    def suspend(self):
        self.ossvc.service_stop()

    def enable(self):
        self.ossvc.service_start()

    def delete(self):
        self.ossvc.service_stop()
        self.ossvc.remove_configs()
        self.ossvc.sudo_rm(self.haproxy_log)
        # Since haproxy should be logging via syslog, we need a syslog
        # restart, otherwise the log file will be kept open and not reappear.
        self.ossvc.syslog_restart()

    def get_status(self, protocol=None):
        return self.ossvc.get_status(protocol)

    def get_statistics(self):
        return self.ossvc.get_statistics()

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

    def set_timeouts(self, protocol, client_timeout, server_timeout,
                     connect_timeout, connect_retries):
        protocol = protocol.lower()
        self._config[protocol]['timeouts'] = {
            'timeout_client': client_timeout,
            'timeout_server': server_timeout,
            'timeout_connect': connect_timeout,
            'retries': connect_retries
        }
