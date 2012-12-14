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
import novaclient

from novaclient import client


# NOTE(LinuxJedi): Override novaclient's error handler as we send messages in
# a slightly different format which causes novaclient's to throw an exception

def from_response(response, body):
    """
    Return an instance of an ClientException or subclass
    based on an httplib2 response.

    Usage::

        resp, body = http.request(...)
        if resp.status != 200:
            raise exception_from_response(resp, body)
    """
    cls = novaclient.exceptions._code_map.get(
        response.status, novaclient.exceptions.ClientException
    )
    request_id = response.get('x-compute-request-id')
    if body:
        message = "n/a"
        details = "n/a"
        if hasattr(body, 'keys'):
            message = body.get('message', None)
            details = body.get('details', None)
        return cls(code=response.status, message=message, details=details,
                   request_id=request_id)
    else:
        return cls(code=response.status, request_id=request_id)

novaclient.exceptions.from_response = from_response


class LibraAPI(object):
    def __init__(self, username, password, tenant, auth_url, region,
                 insecure, debug, bypass_url):
        self.nova = client.HTTPClient(
            username,
            password,
            tenant,
            auth_url,
            region_name=region,
            service_type='compute',
            http_log_debug=debug,
            insecure=insecure,
            bypass_url=bypass_url
        )

    def limits_lb(self, args):
        resp, body = self._get('/limits')
        column_names = ['Verb', 'Value', 'Remaining', 'Unit', 'Next Available']
        columns = ['verb', 'value', 'remaining', 'unit', 'next-available']
        self._render_list(column_names, columns,
                          body['limits']['rate']['values']['limit'])
        column_names = ['Values']
        columns = ['values']
        self._render_dict(column_names, columns, body['limits']['absolute'])

    def protocols_lb(self, args):
        resp, body = self._get('/protocols')
        column_names = ['Name', 'Port']
        columns = ['name', 'port']
        self._render_list(column_names, columns, body['protocols'])

    def algorithms_lb(self, args):
        resp, body = self._get('/algorithms')
        column_names = ['Name']
        columns = ['name']
        self._render_list(column_names, columns, body['algorithms'])

    def list_lb(self, args):
        if args.deleted:
            resp, body = self._get('/loadbalancers?status=DELETED')
        else:
            resp, body = self._get('/loadbalancers')
        column_names = ['Name', 'ID', 'Protocol', 'Port', 'Algorithm',
                        'Status', 'Created', 'Updated']
        columns = ['name', 'id', 'protocol', 'port', 'algorithm', 'status',
                   'created', 'updated']
        self._render_list(column_names, columns, body['loadBalancers'])

    def status_lb(self, args):
        resp, body = self._get('/loadbalancers/{0}'.format(args.id))
        column_names = ['ID', 'Name', 'Protocol', 'Port', 'Algorithm',
                        'Status', 'Created', 'Updated', 'IPs', 'Nodes',
                        'Persistence Type', 'Connection Throttle']
        columns = ['id', 'name', 'protocol', 'port', 'algorithm', 'status',
                   'created', 'updated', 'virtualIps', 'nodes',
                   'sessionPersistence', 'connectionThrottle']
        if 'sessionPersistence' not in body:
            body['sessionPersistence'] = 'None'
        if 'connectionThrottle' not in body:
            body['connectionThrottle'] = 'None'
        self._render_dict(column_names, columns, body)

    def delete_lb(self, args):
        self._delete('/loadbalancers/{0}'.format(args.id))

    def create_lb(self, args):
        data = {}
        nodes = []
        data['name'] = args.name
        if args.port is not None:
            data['port'] = args.port
        if args.protocol is not None:
            data['protocol'] = args.protocol
        if args.algorithm is not None:
            data['algorithm'] = args.algorithm
        for node in args.node:
            addr = node.split(':')
            nodes.append({'address': addr[0], 'port': addr[1],
                          'condition': 'ENABLED'})
        data['nodes'] = nodes
        if args.vip is not None:
            data['virtualIps'] = [{'id': args.vip}]

        resp, body = self._post('/loadbalancers', body=data)
        column_names = ['ID', 'Name', 'Protocol', 'Port', 'Algorithm',
                        'Status', 'Created', 'Updated', 'IPs', 'Nodes']
        columns = ['id', 'name', 'protocol', 'port', 'algorithm', 'status',
                   'created', 'updated', 'virtualIps', 'nodes']
        self._render_dict(column_names, columns, body)

    def modify_lb(self, args):
        data = {}
        if args.name is not None:
            data['name'] = args.name
        if args.algorithm is not None:
            data['algorithm'] = args.algorithm
        self._put('/loadbalancers/{0}'.format(args.id), body=data)

    def node_list_lb(self, args):
        resp, body = self._get('/loadbalancers/{0}/nodes'.format(args.id))
        column_names = ['ID', 'Address', 'Port', 'Condition', 'Status']
        columns = ['id', 'address', 'port', 'condition', 'status']
        self._render_list(column_names, columns, body['nodes'])

    def node_delete_lb(self, args):
        self._delete('/loadbalancers/{0}/nodes/{1}'
                     .format(args.id, args.nodeid))

    def node_add_lb(self, args):
        data = {}
        nodes = []

        for node in args.node:
            addr = node.split(':')
            nodes.append({'address': addr[0], 'port': addr[1],
                          'condition': 'ENABLED'})
        data['nodes'] = nodes
        resp, body = self._post('/loadbalancers/{0}/nodes'
                                .format(args.id), body=data)
        column_names = ['ID', 'Address', 'Port', 'Condition', 'Status']
        columns = ['id', 'address', 'port', 'condition', 'status']
        self._render_list(column_names, columns, body['nodes'])

    def node_modify_lb(self, args):
        data = {'condition': args.condition}
        self._put('/loadbalancers/{0}/nodes/{1}'
                  .format(args.id, args.nodeid), body=data)

    def node_status_lb(self, args):
        resp, body = self._get('/loadbalancers/{0}/nodes/{1}'
                               .format(args.id, args.nodeid))
        column_names = ['ID', 'Address', 'Port', 'Condition', 'Status']
        columns = ['id', 'address', 'port', 'condition', 'status']
        self._render_dict(column_names, columns, body)

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
