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
from novaclient import client


class LibraAPI(object):
    def __init__(self, username, password, tenant, auth_url, region):
        self.nova = client.HTTPClient(
            username,
            password,
            tenant,
            auth_url,
            region_name=region,
            service_type='libra'
        )

    def get(self, url, **kwargs):
        return self.nova.get(url, **kwargs)

    def post(self, url, **kwargs):
        return self.nova.post(url, **kwargs)

    def put(self, url, **kwargs):
        return self.nova.put(url, **kwargs)

    def delete(self, url, **kwargs):
        return self.nova.delete(url, **kwargs)


def main():
    options = argparse.ArgumentParser('Libra command line client')
    options.add_argument(
        '--os_auth_url',
        metavar='<auth-url>',
        help='Authentication URL'
    )
    options.add_argument(
        '--os_username',
        metavar='<auth-user-name>',
        help='Authentication username'
    )
    options.add_argument(
        '--os_password',
        metavar='<auth-password>',
        help='Authentication password'
    )
    options.add_argument(
        '--os_tenant_name',
        metavar='<auth-tenant-name>',
        help='Authentication tenant'
    )
    options.add_argument(
        '--os_region_name',
        metavar='<region-name>',
        help='Authentication region'
    )
    subparsers = options.add_subparsers(
        metavar='<subcommand>', dest='command'
    )
    subparsers.add_parser(
        'list', help='list load balancers'
    )
    subparsers.add_parser(
        'delete', help='delete a load balancer'
    )
    subparsers.add_parser(
        'create', help='create a load balancer'
    )
    subparsers.add_parser(
        'modify', help='modify a load balancer'
    )
    subparsers.add_parser(
        'status', help='get status of a load balancer'
    )
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

    args = options.parse_args()

    api = LibraAPI(args.os_username, args.os_password, args.os_tenant_name,
                   args.os_auth_url, args.os_region_name)

    if args.command == 'list':
        api.get('/devices')

    return 0
