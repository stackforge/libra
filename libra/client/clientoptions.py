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

import argparse


class ClientOptions(object):
    def __init__(self):
        self.options = argparse.ArgumentParser('Libra command line client')

    def _generate(self):
        self.options.add_argument(
            '--os_auth_url',
            metavar='<auth-url>',
            required=True,
            help='Authentication URL'
        )
        self.options.add_argument(
            '--os_username',
            metavar='<auth-user-name>',
            required=True,
            help='Authentication username'
        )
        self.options.add_argument(
            '--os_password',
            metavar='<auth-password>',
            required=True,
            help='Authentication password'
        )
        self.options.add_argument(
            '--os_tenant_name',
            metavar='<auth-tenant-name>',
            required=True,
            help='Authentication tenant'
        )
        self.options.add_argument(
            '--os_region_name',
            metavar='<region-name>',
            required=True,
            help='Authentication region'
        )
        self.options.add_argument(
            '--debug',
            action='store_true',
            help='Debug network messages'
        )
        self.options.add_argument(
            '--insecure',
            action='store_true',
            help='Don\'t verify SSL cert'
        )
        self.options.add_argument(
            '--bypass_url',
            help='Use this API endpoint instead of the Service Catalog'
        )
        subparsers = self.options.add_subparsers(
            metavar='<subcommand>', dest='command'
        )
        subparsers.add_parser(
            'limits', help='get account API usage limits'
        )
        subparsers.add_parser(
            'algorithms', help='get a list of supported algorithms'
        )
        subparsers.add_parser(
            'protocols', help='get a list of supported protocols and ports'
        )
        sp = subparsers.add_parser(
            'list', help='list load balancers'
        )
        sp.add_argument(
            '--deleted', help='list deleted load balancers',
            action='store_true'
        )
        sp = subparsers.add_parser(
            'delete', help='delete a load balancer'
        )
        sp.add_argument('--id', help='load balancer ID', required=True)
        sp = subparsers.add_parser(
            'create', help='create a load balancer'
        )
        sp.add_argument('--name', help='name for the load balancer',
                        required=True)
        sp.add_argument('--port',
                        help='port for the load balancer, 80 is default')
        sp.add_argument('--protocol',
                        help='protocol for the load balancer, HTTP is default',
                        choices=['HTTP', 'TCP'])
        sp.add_argument('--algorithm',
                        help='algorithm for the load balancer,'
                             ' ROUND_ROBIN is default',
                        choices=['LEAST_CONNECTIONS', 'ROUND_ROBIN'])
        sp.add_argument('--node',
                        help='a node for the load balancer in ip:port format',
                        action='append', required=True)
        sp.add_argument('--vip',
                        help='the virtual IP to attach the load balancer to')
        sp = subparsers.add_parser(
            'modify', help='modify a load balancer'
        )
        sp.add_argument('--id', help='load balancer ID', required=True)
        sp.add_argument('--name', help='new name for the load balancer')
        sp.add_argument('--algorithm',
                        help='new algorithm for the load balancer',
                        choices=['LEAST_CONNECTIONS', 'ROUND_ROBIN'])
        sp = subparsers.add_parser(
            'status', help='get status of a load balancer'
        )
        sp.add_argument('--id', help='load balancer ID', required=True)
        sp = subparsers.add_parser(
            'node-list', help='list nodes in a load balancer'
        )
        sp.add_argument('--id', help='load balancer ID', required=True)
        sp = subparsers.add_parser(
            'node-delete', help='delete node from a load balancer'
        )
        sp.add_argument('--id', help='load balancer ID', required=True)
        sp.add_argument('--nodeid',
                        help='node ID to remove from load balancer',
                        required=True)
        sp = subparsers.add_parser(
            'node-add', help='add node to a load balancer'
        )
        sp.add_argument('--id', help='load balancer ID', required=True)
        sp.add_argument('--node', help='node to add in ip:port form',
                        required=True, action='append')
        sp = subparsers.add_parser(
            'node-modify', help='modify node in a load balancer'
        )
        sp.add_argument('--id', help='load balancer ID', required=True)
        sp.add_argument('--nodeid', help='node ID to modify', required=True)
        sp.add_argument('--condition', help='the new state for the node',
                        choices=['ENABLED', 'DISABLED'], required=True)
        sp = subparsers.add_parser(
            'node-status', help='get status of a node in a load balancer'
        )
        sp.add_argument('--id', help='load balancer ID', required=True)
        sp.add_argument('--nodeid', help='node ID to get status from',
                        required=True)

    def run(self):
        self._generate()
        return self.options.parse_args()
