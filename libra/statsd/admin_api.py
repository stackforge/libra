# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
import random
import sys


class AdminAPI(object):
    def __init__(self, addresses, logger):
        self.logger = logger
        random.shuffle(addresses)
        for address in addresses:
            self.url = 'https://{0}/v1'.format(address)
            self.logger.info('Trying {url}'.format(url=self.url))
            status, data = self._get('{url}/devices/usage'
                                     .format(url=self.url))
            if status:
                self.logger.info('API Server is online')
                self.online = True
                return

        # if we get this far all API servers are down
        self.online = False

    def get_ping_list(self):
        marker = 0
        limit = 20
        lb_list = []
        while True:
            nodes = self._get_node_list(limit, marker)
            # if we hit an empty device list we have hit end of list
            if not len(nodes['devices']):
                break

            for device in nodes['devices']:
                if device['status'] == 'ONLINE':
                    lb_list.append(device)
            marker = marker + limit
        return lb_list

    def _get_node_list(self, limit, marker):
        return self._get(
            '{url}/devices?marker={marker}&limit={limit}'
            .format(url=self.url, marker=marker, limit=limit)
        )

    def _get(self, url):
        try:
            r = requests.get(url, verify=False)
        except requests.exceptions.RequestException:
            self.logger.error('Exception communicating to server: {exc}'
                              .format(exc=sys.exc_info()[0]))
            return False, None

        if r.status_code != 200:
            self.logger.error('Server returned error {code}'
                              .format(code=r.status_code))
            return False, r.json()
        return True, r.json()

    def is_online(self):
        return self.online
