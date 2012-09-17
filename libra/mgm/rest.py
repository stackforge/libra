#!/usr/bin/env python
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

import requests
import json


class APIClient(object):
    def __init__(self, url):
        self.url = url

    def get_node_list(self, limit, marker):
        if marker:
            marker = '&marker={id}'.format(id=id)

        r = requests.get(
            '{url}/devices/?limit={limit}{marker}'
            .format(url=self.url, limit=limit, marker=marker)
        )
        return r.json

    def get_node(self, node_id):
        r = requests.get(
            '{url}/devices/{nid}'.format(url=self.url, nid=node_id)
        )
        return r.json

    def add_node(self, node_data):
        requests.post('{url}/devices', json.dumps(node_data))

    def delete_node(self, node_id):
        requests.delete(
            '{url}/devices/{nid}'.format(url=self.url, nid=node_id)
        )

    def update_node(self, node_id, node_data):
        requests.put(
            '{url}/devices/{nid}'.format(url=self.url, nid=node_id),
            json.dumps(node_data)
        )
