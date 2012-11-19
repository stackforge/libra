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
import sys
import urllib

from novaclient import client
from novaclient import exceptions


class NotFound(Exception):
    pass


class Node(object):
    def __init__(self, username, password, tenant, auth_url, region, keyname,
                 secgroup, image, node_type):
        self.nova = client.HTTPClient(
            username,
            password,
            tenant,
            auth_url,
            region_name=region,
            no_cache=True,
            service_type='compute'
        )
        self.keyname = keyname
        self.secgroup = secgroup
        if image.isdigit():
            self.image = image
        else:
            self.image = self._get_image(image)

        if node_type.isdigit():
            self.node_type = node_type
        else:
            self.node_type = self._get_flavor(node_type)

    def build(self):
        """ create a node, test it is running """
        node_id = uuid.uuid1()
        try:
            body = self._create(node_id)
        except exceptions.ClientException:
            return False, 'Error creating node {nid} exception {exc}'.format(
                nid=node_id, exc=sys.exc_info()[0]
            )

        server_id = body['server']['id']
        # try for 40 * 3 seconds
        waits = 40
        while waits > 0:
            time.sleep(3)
            status = self._status(server_id)
            if status['status'] == 'ACTIVE':
                return True, status
            elif not status['status'].startswith('BUILD'):
                return False, 'Error spawning node {nid} status {stat}'.format(
                    node=node_id, stat=status['status']
                )
            waits = waits - 1

        return (False,
                'Timeout creating node, uuid: {nid}, server ID: {sid}'
                .format(nid=node_id, sid=server_id)
                )

    def delete(self, node_id):
        """ delete a node """
        try:
            resp = self._delete(node_id)
        except exceptions.ClientException:
            return False, 'Error deleting node {nid} exception {exc}'.format(
                nid=node_id, exc=sys.exc_info()[0]
            )

        if resp['status'] != '204':
            return False, 'Error deleting node {nid} status {stat}'.format(
                node=node_id, stat=resp['status']
            )

        return True, ''

    def _create(self, node_id):
        """ create a nova node """
        url = "/servers"
        body = {"server": {
                "name": '{0}'.format(node_id),
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
        return body['server']

    def _delete(self, node_id):
        """ delete a nova node, return 204 succeed """
        url = "/servers/{0}".format(node_id)
        resp, body = self.nova.delete(url)

        return resp

    def _get_image(self, image_name):
        """ tries to find an image from the name """
        args = {'name': image_name}
        url = "/images?{0}".format(urllib.urlencode(args))
        resp, body = self.nova.get(url)
        if resp['status'] not in ['200', '203']:
            msg = "Error {0} searching for image with name {1}".format(
                resp['status'], image_name
            )
            raise NotFound(msg)
        if len(body['images']) != 1:
            print body['images']
            msg = "Could not find image with name {0}".format(image_name)
            raise NotFound(msg)
        return body['images'][0]['id']

    def _get_flavor(self, flavor_name):
        """ tries to find a flavor from the name """
        url = "/flavors"
        resp, body = self.nova.get(url)
        if resp['status'] not in ['200', '203']:
            msg = "Error {0} searching for flavor with name {1}".format(
                resp['status'], flavor_name
            )
            raise NotFound(msg)
        for flavor in body['flavors']:
            if flavor['name'] == flavor_name:
                return flavor['id']
        msg = "Could not find flavor with name {0}".format(flavor_name)
        raise NotFound(msg)
