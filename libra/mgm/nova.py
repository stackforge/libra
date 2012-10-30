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

import uuid
import time

from novaclient import client

LIBRA_VERSION = 'v1'


class Node(object):
    def __init__(self, username, password, tenant, auth_url, region, keyname,
                 secgroup, image, node_type):
        self.nova = client.HTTPClient(
            username,
            password,
            tenant,
            auth_url,
            region_name=region,
            service_type='compute'
        )
        self.keyname = keyname
        self.secgroup = secgroup
        self.image = image
        self.node_type = node_type

    def build(self):
        """ create a node, test it is running """
        node_id = uuid.uuid1()
        try:
            body = self._create(node_id)
        except:
            return False, 'Error creating node {nid}'.format(nid=node_id)

        server_id = body['server']['id']
        # try for 40 * 3 seconds
        waits = 40
        while waits > 0:
            time.sleep(3)
            status = self._status(server_id)
            if status == 'ACTIVE':
                return True, body
            waits = waits - 1

        return (False,
                'Timeout creating node, uuid: {nid}, server ID: {sid}'
                .format(nid=node_id, sid=server_id)
                )

    def delete(self, node_id):
        """ delete a node """
        try:
            resp = self._delete(node_id)
        except:
            return False

        if resp['status'] != '204':
            return False

        return True

    def _create(self, node_id):
        """ create a nova node """
        url = "/servers"
        body = {"server": {
                "name": 'lbaas-{0}-{1}'.format(LIBRA_VERSION, node_id),
                "imageRef": self.image,
                "key_name": self.keyname,
                "flavorRef": self.node_type,
                "max_count": 1,
                "min_count": 1,
                "networks": [],
                "security_groups": [{"name": self.secgroup}]
                }}
        resp, body = self.nova.post(url, body=body)
        return body

    def _status(self, node_id):
        """ used to keep scanning to see if node is up """
        url = "/servers/{0}".format(node_id)
        resp, body = self.nova.get(url)
        return body['server']['status']

    def _delete(self, node_id):
        """ delete a nova node, return 204 succeed """
        url = "/servers/{0}".format(node_id)
        resp, body = self.nova.delete(url)

        return resp
