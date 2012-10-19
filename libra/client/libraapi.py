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

import prettytable
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

    def list_lb(self, args):
        resp, body = self._get('/loadbalaners')
        column_names = ['Name', 'ID', 'Protocol', 'Port', 'Algorithm',
                        'Status', 'Created', 'Updated']
        columns = ['name', 'id', 'protocol', 'port', 'algorithm', 'status',
                   'created', 'updated']
        self._render_list(column_names, columns, body['loadBalancers'])

    def status_lb(self, args):
        resp, body = self._get('/loadbalancers/{0}'.format(args.lbid))
        column_names = ['ID', 'Name', 'Protocol', 'Port', 'Algorithm',
                        'Status', 'Created', 'Updated', 'IPs', 'Nodes',
                        'Persistence Type', 'Connection Throttle']
        columns = ['id', 'name', 'protocol', 'port', 'algorithm', 'status',
                   'created', 'updated', 'virtualIps', 'nodes',
                   'sessionPersistence', 'connectionThrottle']
        self._render_dict(column_names, columns, body)

    def delete_lb(self, args):
        self._delete('/loadbalancers/{0}'.format(args.lbid))

    def create_lb(self, args):
        data = {}
        nodes = []
        data['name'] = args.name
        if args.port is not None:
            data['port'] = args.port
        if args.protocol is not None:
            data['protocol'] = args.protocol
        for node in args.node:
            addr = args.node.split(':')
            nodes.append({'address': addr[0], 'port': addr[1],
                          'condition': 'ENABLED'})
        data['nodes'] = nodes
        if args.vip is not None:
            data['virtualIps'] = [{'id': args.vip}]

        resp, body = self._post('/loadbalancers', data)
        column_names = ['ID', 'Name', 'Protocol', 'Port', 'Algorithm',
                        'Status', 'Created', 'Updated', 'IPs', 'Nodes']
        columns = ['id', 'name', 'protocol', 'port', 'algorithm', 'status',
                   'created', 'updated', 'virtualIps', 'nodes']
        self._render_dict(column_names, columns, body)

    def modify_lb(self, args):
        pass

    def node_list_lb(self, args):
        pass

    def node_delete_lb(self, args):
        pass

    def node_add_lb(self, args):
        pass

    def node_modify_lb(self, args):
        pass

    def node_status_lb(self, args):
        pass

    def _render_list(self, column_names, columns, data):
        table = prettytable.PrettyTable(column_names)
        for item in data:
            row = []
            for column in columns:
                rdata = item[column]
                row.append(rdata)
            table.add_row(row)
        print table

    def _render_dict(self, column_names, columns, data):
        table = prettytable.PrettyTable(column_names)
        row = []
        for column in columns:
            rdata = data[column]
            row.append(rdata)
        table.add_row(row)
        print table

    def _get(self, url, **kwargs):
        return self.nova.get(url, **kwargs)

    def _post(self, url, **kwargs):
        return self.nova.post(url, **kwargs)

    def _put(self, url, **kwargs):
        return self.nova.put(url, **kwargs)

    def _delete(self, url, **kwargs):
        return self.nova.delete(url, **kwargs)
