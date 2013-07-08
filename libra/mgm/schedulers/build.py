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

import threading
from novaclient import exceptions
from libra.mgm.nova import Node, BuildError, NotFound


class BuildNodes(object):
    def __init__(self, driver, lock, logger, node_list, args):
        self.driver = driver
        self.lock = lock
        self.args = args
        self.logger = logger
        self.node_list = node_list
        self.timer = None

    def run(self):
        """ check if known nodes are used """
        with self.lock:
            try:
                self.logger.info('Checking if new nodes are needed')
                api = self.driver(self.args.api_server, self.logger)
                if api.is_online():
                    self.logger.info(
                        'Connected to {url}'.format(url=api.get_url())
                    )
                    free_count = api.get_free_count()
                    if free_count is None:
                        self.scheduler()
                        return
                    if free_count < self.args.nodes:
                        # we need to build new nodes
                        nodes_required = self.args.nodes - free_count
                        self.logger.info(
                            '{nodes} nodes required'
                            .format(nodes=nodes_required)
                        )
                        self.build_nodes(nodes_required, api)
                    else:
                        self.logger.info('No new nodes required')
                else:
                    self.logger.error('No working API server found')
            except Exception:
                self.logger.exception('Uncaught exception during node check')

            self.scheduler()

    def build_nodes(self, count, api):
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
            self.logger.error('Error initialising Nova connection {exc}'
                .format(exc=exc)
            )
            return
        # Remove number of nodes we are still waiting on build status from
        build_count = len(self.node_list.get())
        count = count - build_count
        if count > 0:
            self.logger.info(
                '{0} nodes already building, attempting to build {1} more'
                .format(build_count, count)
            )
        else:
            self.logger.info(
                '{0} nodes already building, no more needed'
                .format(build_count)
            )
        while count > 0:
            count = count - 1
            try:
                node_id = nova.build()
            except BuildError as exc:
                self.logger.exception('{0}, node {1}'
                    .format(exc.msg, exc.node_name)
                )
                self.logger.info(
                    'Node build did not return ID for {0}, trying to find'
                    .format(exc.node_name)
                )
                self.find_unknown(exc.node_name, nova)
                continue

            if node_id > 0:
                self.logger.info(
                    'Storing node {0} to add later'.format(node_id)
                )
                self.node_list.add(node_id)
            else:
                self.logger.error(
                    'Node build did not return ID, cannot find it'
                )

    def find_unknown(self, name, nova):
        """
            Nova can tell us a node failed to build when it didn't
            This does a check and if it did start to build adds it to the
            failed node list.
        """
        try:
            node_id = nova.get_node(name)
            self.logger.info('Storing node {0} to add later'.format(node_id))
            self.node_list.add(node_id)
        except NotFound:
            # Node really didn't build
            self.logger.info(
                'No node found for {0}, giving up on it'.format(name)
            )
            return
        except exceptions.ClientException:
            self.logger.exception(
                'Error getting failed node info from Nova for {0}'.format(name)
            )

    def scheduler(self):
        self.logger.info('Node check timer sleeping for {mins} minutes'
                         .format(mins=self.args.check_interval))
        self.timer = threading.Timer(60 * int(self.args.check_interval),
                                     self.run, ())
        self.timer.start()
