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
import sys
import urllib

from oslo.config import cfg

from novaclient import client
from novaclient import exceptions

from libra.openstack.common import log as logging

LOG = logging.getLogger(__name__)

class NotFound(Exception):
    pass


class BuildError(Exception):
    def __init__(self, msg, node_name, node_id=0):
        self.msg = msg
        self.node_name = node_name
        self.node_id = node_id

    def __str__(self):
        return self.msg


class Node(object):
    def __init__(self):
        self.nova = client.HTTPClient(
            cfg.CONF['mgm']['nova_user'],
            cfg.CONF['mgm']['nova_pass'],
            cfg.CONF['mgm']['nova_tenant'],
            cfg.CONF['mgm']['nova_auth_url'],
            region_name=cfg.CONF['mgm']['nova_region'],
            no_cache=True,
            insecure=cfg.CONF['mgm']['nova_insecure'],
            timeout=cfg.CONF['mgm']['nova_timeout'],
            tenant_id=cfg.CONF['mgm']['nova_tenant_id'],
            bypass_url=cfg.CONF['mgm']['nova_bypass_url'],
            service_type='compute'
        )
        self.keyname = cfg.CONF['mgm']['nova_keyname']
        self.secgroup = cfg.CONF['mgm']['nova_secgroup']
        self.node_basename = cfg.CONF['mgm']['node_basename']
        self.az = cfg.CONF['mgm']['nova_az_name']
        self.net_id = cfg.CONF['mgm']['nova_net_id']
        self.rm_fip_ignore_500 = cfg.CONF['mgm']['rm_fip_ignore_500']

        # Replace '_' with '-' in basename
        if self.node_basename:
            self.node_basename = self.node_basename.replace('_', '-')

        self.image = cfg.CONF['mgm']['nova_image']

        image_size = cfg.CONF['mgm']['nova_image_size']
        if image_size.isdigit():
            self.node_type = image_size
        else:
            self.node_type = self._get_flavor(image_size)

    def build(self):
        """ create a node, test it is running """
        node_id = uuid.uuid1()
        try:
            body = self._create(node_id)
        except exceptions.ClientException, e:
            msg = 'Error creating node, exception {exc}' \
                  'Message: {msg} Details: {details}'
            raise BuildError(msg.format(exc=sys.exc_info()[0], msg=e.message,
                             details=e.details), node_id)

        return body['server']['id']

    def vip_create(self):
        """ create a virtual IP  """
        url = '/os-floating-ips'
        body = {"pool": None}
        try:
            resp, body = self.nova.post(url, body=body)
        except Exception as novaexcept:
            if "timed out" in str(novaexcept):
                LOG.error('Nova create floating IP %s %s ' \
                          'POST call timed out after %d seconds.' \
                          % (url, body, cfg.CONF['mgm']['nova_timeout']))
            raise
        return body['floating_ip']

    def vip_assign(self, node_id, vip):
        """ assign a virtual IP to a Nova instance """
        url = '/servers/{0}/action'.format(node_id)
        body = {
            "addFloatingIp": {
                "address": vip
            }
        }
        try:
            resp, body = self.nova.post(url, body=body)
        except Exception as novaexcept:
            if "timed out" in str(novaexcept):
                LOG.error('Nova assign floating IP %s %s ' \
                          'POST call timed out after %d seconds.' \
                          % (url, body, cfg.CONF['mgm']['nova_timeout']))
            raise

        if resp.status_code != 202:
            raise Exception(
                'Response code {0}, message {1} when assigning vip'
                .format(resp.status_code, body)
            )

    def vip_remove(self, node_id, vip):
        """ delete a virtual IP from a Nova instance """
        url = '/servers/{0}/action'.format(node_id)
        body = {
            "removeFloatingIp": {
                "address": vip
            }
        }
        try:
            resp, body = self.nova.post(url, body=body)
        except exceptions.ClientException as e:
            if e.code == 500 and self.rm_fip_ignore_500:
                return
            raise
        except Exception as novaexcept:
            if "timed out" in str(novaexcept):
                LOG.error('Nova remove floating IP %s %s ' \
                          'POST call timed out after %d seconds.' \
                          % (url, body, cfg.CONF['mgm']['nova_timeout']))
            raise

        if resp.status_code != 202:
            raise Exception(
                'Response code {0}, message {1} when removing vip'
                .format(resp.status_code, body)
            )

    def vip_delete(self, vip):
        """ delete a virtual IP """
        vip_id = self._find_vip_id(vip)
        url = '/os-floating-ips/{0}'.format(vip_id)
        # sometimes this needs to be tried twice
        try:
            resp, body = self.nova.delete(url)
        except exceptions.ClientException:
            resp, body = self.nova.delete(url)
        except Exception as novaexcept:
            if "timed out" in str(novaexcept):
                LOG.error('Nova delete floating IP %s %s ' \
                          'DELETE call timed out after %d seconds.' \
                          % (url, body, cfg.CONF['mgm']['nova_timeout']))
            raise

    def vip_get_instance_id(self, vip):
        """ get the instance id owning the vip """
        vip_id = self._find_vip_id(vip)
        url = '/os-floating-ips/{0}'.format(vip_id)
        try:
            resp, body = self.nova.get(url)
        except Exception as novaexcept:
            if "timed out" in str(novaexcept):
                LOG.error('Nova get instance id %s ' \
                          'GET call timed out after %d seconds.' \
                          % (url, cfg.CONF['mgm']['nova_timeout']))
            raise
        if resp.status_code != 200:
           raise Exception(
             'Response code {0}, message {1} when getting ' \
             'floating IP {2} details'
             .format(resp.status_code, body, vip)
           )
        return body['floating_ip']['instance_id']

    def _find_vip_id(self, vip):
        url = '/os-floating-ips'
        try:
            resp, body = self.nova.get(url)
        except Exception as novaexcept:
            if "timed out" in str(novaexcept):
                LOG.error('Nova get floating IP id %s ' \
                          'GET call timed out after %d seconds.' \
                          % (url, cfg.CONF['mgm']['nova_timeout']))
            raise
        for fip in body['floating_ips']:
            if fip['ip'] == vip:
                return fip['id']
        raise NotFound('floating IP not found')

    def delete(self, node_id):
        """ delete a node """
        try:
            resp = self._delete(node_id)
        except exceptions.ClientException:
            return False, 'Error deleting node {nid} exception {exc}'.format(
                nid=node_id, exc=sys.exc_info()[0]
            )
        except Exception as novaexcept:
            return False, 'Error deleting node {nid} exception {exc}'.format(
                nid=node_id, exc=sys.exc_info()[0]
            )

        if resp.status_code != 204:
            return False, 'Error deleting node {nid} status {stat}'.format(
                nid=node_id, stat=resp.status_code
            )

        return True, ''

    def _create(self, node_id):
        """ create a nova node """
        url = "/servers"
        if self.node_basename:
            node_name = '{0}-{1}'.format(self.node_basename, node_id)
        else:
            node_name = '{0}'.format(node_id)

        networks = []
        if self.net_id:
            networks.append({"uuid": self.net_id})

        body = {"server": {
                "name": node_name,
                "imageRef": self.image,
                "key_name": self.keyname,
                "flavorRef": self.node_type,
                "max_count": 1,
                "min_count": 1,
                "availability_zone": self.az,
                "networks": networks,
                "security_groups": [{"name": self.secgroup}]
                }}
        try:
            resp, body = self.nova.post(url, body=body)
        except Exception as novaexcept:
            if "timed out" in str(novaexcept):
                LOG.error('Nova create node %s %s ' \
                          'POST call timed out after %d seconds.' \
                          % (url, body, cfg.CONF['mgm']['nova_timeout']))
            raise

        return body

    def status(self, node_id):
        """ used to keep scanning to see if node is up """
        url = "/servers/{0}".format(node_id)
        try:
            resp, body = self.nova.get(url)
        except exceptions.NotFound:
            msg = "Could not find node with id {0}".format(node_id)
            raise NotFound(msg)
        except Exception as novaexcept:
            if "timed out" in str(novaexcept):
                LOG.error('Nova node status %s ' \
                          'GET call timed out after %d seconds.' \
                          % (url, cfg.CONF['mgm']['nova_timeout']))
            raise

        return resp, body

    def _delete(self, node_id):
        """ delete a nova node, return 204 succeed """
        url = "/servers/{0}".format(node_id)
        try:
            resp, body = self.nova.delete(url)
        except Exception as novaexcept:
            if "timed out" in str(novaexcept):
                LOG.error('Nova node delete %s ' \
                          'DELETE call timed out after %d seconds.' \
                          % (url, cfg.CONF['mgm']['nova_timeout']))
            raise

        return resp

    # TODO: merge get_node and _get_image to remove duplication of code

    def get_node(self, node_name):
        """ tries to find a node from the name """
        args = {'name': node_name}
        url = "/servers?{0}".format(urllib.urlencode(args))
        try:
            resp, body = self.nova.get(url)
        except exceptions.NotFound:
            msg = "Could not find node with name {0}".format(node_name)
            raise NotFound(msg)
        except Exception as novaexcept:
            if "timed out" in str(novaexcept):
                LOG.error('Nova get node %s ' \
                          'GET call timed out after %d seconds.' \
                          % (url, cfg.CONF['mgm']['nova_timeout']))
            raise

        if resp.status_code not in [200, 203]:
            msg = "Error {0} searching for node with name {1}".format(
                resp.status_code, node_name
            )
            raise NotFound(msg)
        if len(body['servers']) != 1:
            msg = "Could not find node with name {0}".format(node_name)
            raise NotFound(msg)
        return body['servers'][0]['id']

    def _get_image(self, image_name):
        """ tries to find an image from the name """
        args = {'name': image_name}
        url = "/images?{0}".format(urllib.urlencode(args))
        try:
            resp, body = self.nova.get(url)
        except Exception as novaexcept:
            if "timed out" in str(novaexcept):
                LOG.error('Nova get image %s ' \
                          'GET call timed out after %d seconds.' \
                          % (url, cfg.CONF['mgm']['nova_timeout']))
            raise

        if resp.status_code not in [200, 203]:
            msg = "Error {0} searching for image with name {1}".format(
                resp.status_code, image_name
            )
            raise NotFound(msg)
        if len(body['images']) != 1:
            msg = "Could not find image with name {0}".format(image_name)
            raise NotFound(msg)
        return body['images'][0]['id']

    def _get_flavor(self, flavor_name):
        """ tries to find a flavor from the name """
        url = "/flavors"
        try:
            resp, body = self.nova.get(url)
        except Exception as novaexcept:
            if "timed out" in str(novaexcept):
                LOG.error('Nova get flavors %s ' \
                          'GET call timed out after %d seconds.' \
                          % (url, cfg.CONF['mgm']['nova_timeout']))
            raise

        if resp.status_code not in [200, 203]:
            msg = "Error {0} searching for flavor with name {1}".format(
                resp.status_code, flavor_name
            )
            raise NotFound(msg)
        for flavor in body['flavors']:
            if flavor['name'] == flavor_name:
                return flavor['id']
        msg = "Could not find flavor with name {0}".format(flavor_name)
        raise NotFound(msg)
