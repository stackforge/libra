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
            help='Authentication URL'
        )
        self.options.add_argument(
            '--os_username',
            metavar='<auth-user-name>',
            help='Authentication username'
        )
        self.options.add_argument(
            '--os_password',
            metavar='<auth-password>',
            help='Authentication password'
        )
        self.options.add_argument(
            '--os_tenant_name',
            metavar='<auth-tenant-name>',
            help='Authentication tenant'
        )
        self.options.add_argument(
            '--os_region_name',
            metavar='<region-name>',
            help='Authentication region'
        )
        subparsers = self.options.add_subparsers(
            metavar='<subcommand>', dest='command'
        )
        subparsers.add_parser(
            'list', help='list load balancers'
        )
        subparsers.add_parser(
            'delete', help='delete a load balancer'
        )
        sp = subparsers.add_parser(
            'create', help='create a load balancer'
        )
        sp.add_argument('--name', help='name for the load balancer')
        sp.add_argument('--port', help='port for the load balancer')
        sp.add_argument('--protocol',
                        help='protocol for the load balancer (TCP or HTTP)',
                        choices=['HTTP', 'TCP'])
        sp.add_argument('--nodes',
                        help='a node for the load balancer in ip:port format',
                        action='append')
        sp.add_argument('--vip',
                        help='the virtual IP to attach the load balancer to')
        subparsers.add_parser(
            'modify', help='modify a load balancer'
        )
        sp = subparsers.add_parser(
            'status', help='get status of a load balancer'
        )
        sp.add_argument('lbid', help='Load Balancer ID')
        subparsers.add_parser(
            'node-list', help='list nodes in a load balancer'
        )
        subparsers.add_parser(
            'node-delete', help='delete node from a load balancer'
        )
        subparsers.add_parser(
            'node-add', help='add node to a load balancer'
        )
        subparsers.add_parser(
            'node-modify', help='modify node in a load balancer'
        )
        subparsers.add_parser(
            'node-status', help='get status of a node in a load balancer'
        )

    def run(self):
        self._generate()
        return self.options.parse_args()
