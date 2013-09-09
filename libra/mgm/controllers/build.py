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

from time import sleep
from novaclient import exceptions
from libra.mgm.nova import Node, BuildError, NotFound


class BuildController(object):

    RESPONSE_FIELD = 'response'
    RESPONSE_SUCCESS = 'PASS'
    RESPONSE_FAILURE = 'FAIL'

    def __init__(self, logger, args, msg):
        self.logger = logger
        self.msg = msg
        self.args = args

    def run(self):
        try:
            nova = Node(self.args)
        except Exception:
            self.logger.exception("Error initialising Nova connection")
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg

        self.logger.info("Building a requested Nova instance")
        try:
            node_id = nova.build()
            self.logger.info("Build command sent to Nova")
        except BuildError as exc:
            self.logger.exception(
                "{0}, node {1}".format(exc.msg, exc.node_name)
            )
            name = exc.node_name
            # Node may have built despite error
            try:
                node_id = self.get_node(name)
            except NotFound:
                self.logger.error(
                    "No node found for {0}, giving up on it".format(name)
                )
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                return self.msg
            except exceptions.ClientException:
                self.logger.exception(
                    'Error getting failed node info from Nova for {0}'
                    .format(name)
                )
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                return self.msg
        if node_id > 0:
            return self._wait_until_node_ready(nova, node_id)
        else:
            self.logger.error(
                'Node build did not return an ID, cannot find it'
            )
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg

    def _wait_until_node_ready(self, nova, node_id):
        for x in xrange(1, 10):
            try:
                resp, status = nova.status(node_id)
            except NotFound:
                self.logger.error(
                    'Node {0} can no longer be found'.format(node_id)
                )
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                return self.msg
            except exceptions.ClientException:
                self.logger.exception(
                    'Error getting status from Nova'
                )
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                return self.msg
            if resp.status_code not in(200, 203):
                self.logger.error(
                    'Error geting status from Nova, error {0}'
                    .format(resp.status_code)
                )
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                return self.msg
            status = status['server']
            if status['status'] == 'ACTIVE':
                self.msg['name'] = status['name']
                addresses = status['addresses'].itervalues().next()
                for address in addresses:
                    if not address['addr'].startswith('10.'):
                        break
                self.msg['addr'] = address['addr']
                self.msg['type'] = "basename: {0}, image: {1}".format(
                    self.args.node_basename, self.args.nova_image
                )
                self.msg['az'] = self.args.az
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
                self.logger.info('Node {0} returned'.format(status['name']))
                return self.msg
            sleep(60)

        nova.delete(node_id)
        self.logger.error(
            "Node {0} didn't come up after 10 minutes, deleted"
        ).format(node_id)
        self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        return self.msg
