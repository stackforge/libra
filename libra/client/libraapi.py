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

    def list_lb(self):
        resp, body = self._get('/loadbalaners')
        columns = ['Name', 'ID', 'Protocol', 'Port', 'Algorithm', 'Status',
                   'Created', 'Updated']
        self._render(columns, body, 'loadbalancers')

    def _render(self, columns, data, row_item):
        table = prettytable.PrettyTable(columns)
        for item in data[row_item]:
            table.add_row(item)
        print table

    def _get(self, url, **kwargs):
        return self.nova.get(url, **kwargs)

    def _post(self, url, **kwargs):
        return self.nova.post(url, **kwargs)

    def _put(self, url, **kwargs):
        return self.nova.put(url, **kwargs)

    def _delete(self, url, **kwargs):
        return self.nova.delete(url, **kwargs)
