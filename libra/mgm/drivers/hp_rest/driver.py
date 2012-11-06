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
import random
import sys

from libra.mgm.drivers.base import MgmDriver

API_VERSION = 'v1'


class HPRestDriver(MgmDriver):

    def __init__(self, addresses, logger):
        self.logger = logger
        random.shuffle(addresses)
        for address in addresses:
            self.url = 'https://{0}/{1}'.format(address, API_VERSION)
            self.logger.info('Trying {url}'.format(url=self.url))
            status, data = self._get('{url}/devices/usage'
                                     .format(url=self.url))
            if status:
                self.logger.info('API Server is online')
                self.online = True
                return

        # if we get this far all API servers are down
        self.online = False

    def get_url(self):
        return self.url

    def get_free_count(self):
        status, usage = self.get_usage()
        if not status:
            return None
        return usage['free']

    def is_online(self):
        return self.is_online

    def get_node_list(self, limit, marker):
        return self._get('{url}/devices'.format(url=self.url))

    def get_usage(self):
        return self._get('{url}/devices/usage'.format(url=self.url))

    def get_node(self, node_id):
        return self._get(
            '{url}/devices/{nid}'.format(url=self.url, nid=node_id)
        )

    def add_node(self, node_data):
        return self._post('{url}/devices'.format(url=self.url), node_data)

    def delete_node(self, node_id):
        requests.delete(
            '{url}/devices/{nid}'.format(url=self.url, nid=node_id)
        )

    def update_node(self, node_id, node_data):
        requests.put(
            '{url}/devices/{nid}'.format(url=self.url, nid=node_id),
            json.dumps(node_data)
        )

    def _get(self, url):
        try:
            r = requests.get(url, verify=False)
        except:
            self.logger.error('Exception communicating to server: {exc}'
                              .format(exc=sys.exc_info()[0]))
            return False, None

        if r.status_code != 200:
            self.logger.error('Server returned error {code}'
                              .format(code=r.status_code))
            return False, r.json
        return True, r.json

    def _post(self, url, node_data):
        try:
            r = requests.post(url, data=json.dumps(node_data), verify=False)
        except:
            self.logger.error('Exception communicating to server: {exc}'
                              .format(exc=sys.exc_info()[0]))
            return False, None

        if r.status_code != 200:
            self.logger.error('Server returned error {code}'
                              .format(code=r.status_code))
            return False, r.json
        return True, r.json
