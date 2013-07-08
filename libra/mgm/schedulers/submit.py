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

import sys
import threading
from novaclient import exceptions
from libra.mgm.nova import Node, NotFound


class SubmitNodes(object):
    def __init__(self, driver, lock, logger, node_list, args):
        self.driver = driver
        self.lock = lock
        self.args = args
        self.logger = logger
        self.node_list = node_list
        self.timer = None

    def run(self):
        """ check/submit list of nodes to be added """
        with self.lock:
            try:
                self.logger.info('Checking log of nova builds')
                nodes = self.node_list.get()
                if len(nodes) == 0:
                    self.logger.info('Node log empty')
                else:
                    api = self.driver(self.args.api_server, self.logger)
                    if api.is_online():
                        self.logger.info(
                            'Connected to {url}'.format(url=api.get_url())
                        )
                        for node in nodes:
                            self.test_node(node, api)
                    else:
                        self.logger.error('No working API server found')
            except Exception:
                self.logger.exception(
                    'Uncaught exception during failed node check'
                )
            self.scheduler()

    def test_node(self, node_id, api):
        try:
            nova = Node(
                self.args.nova_user,
                self.args.nova_pass,
                self.args.nova_tenant,
                self.args.nova_auth_url,
                self.args.nova_region,
                self.args.nova_keyname,
                self.args.nova_secgroup,
                self.args.nova_image,
                self.args.nova_image_size,
                node_basename=self.args.node_basename
            )
        except Exception as exc:
            self.logger.error(
                'Error initialising Nova connection {exc}'
                .format(exc=exc)
            )
            return
        self.logger.info('Testing readiness node {0}'.format(node_id))
        try:
            resp, status = nova.status(node_id)
        except NotFound:
            self.logger.info(
                'Node {0} no longer exists, removing from list'
                .format(node_id)
            )
            self.node_list.delete(node_id)
            return
        except exceptions.ClientException as exc:
            self.logger.error(
                'Error getting status from Nova, exception {exc}'
                .format(exc=sys.exc_info()[0])
            )
            return

        if resp.status_code not in(200, 203):
            self.logger.error(
                'Error geting status from Nova, error {0}'
                .format(resp.status_code)
            )
            return
        status = status['server']
        if status['status'] == 'ACTIVE':
            name = status['name']
            body = self.build_node_data(status)
            status, response = api.add_node(body)
            if not status:
                self.logger.error(
                    'Could not upload node {name} to API server'
                    .format(name=name)
                )
            else:
                self.node_list.delete(node_id)
                self.logger.info('Node {0} added to API server'.format(name))
            return
        elif status['status'].startswith('BUILD'):
            self.logger.info(
                'Node {0} still building, ignoring'.format(node_id)
            )
            return
        else:
            self.logger.info(
                'Node {0} is bad, deleting'.format(node_id)
            )
            status, msg = nova.delete(node_id)
            if not status:
                self.logger.error(msg)
            else:
                self.logger.info('Delete successful')
                self.node_list.delete(node_id)

    def build_node_data(self, data):
        """ Build the API data from the node data """
        body = {}
        body['name'] = data['name']
        addresses = data['addresses']['private']
        for address in addresses:
            if not address['addr'].startswith('10.'):
                break
        body['publicIpAddr'] = address['addr']
        body['floatingIpAddr'] = address['addr']
        body['az'] = self.args.az
        body['type'] = "basename: {0}, image: {1}".format(
            self.args.node_basename, self.args.nova_image
        )
        return body

    def scheduler(self):
        self.logger.info('Node submit timer sleeping for {mins} minutes'
                         .format(mins=self.args.failed_interval))
        self.timer = threading.Timer(60 * int(self.args.failed_interval),
                                     self.run, ())
        self.timer.start()
