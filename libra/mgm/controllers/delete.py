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

from libra.mgm.nova import Node, NotFound


class DeleteController(object):

    RESPONSE_FIELD = 'response'
    RESPONSE_SUCCESS = 'PASS'
    RESPONSE_FAILURE = 'FAIL'

    def __init__(self, logger, msg):
        self.logger = logger
        self.msg = msg

    def run(self):
        try:
            nova = Node()
        except Exception:
            self.logger.exception("Error initialising Nova connection")
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg

        self.logger.info(
            "Deleting a requested Nova instance {0}".format(self.msg['name'])
        )
        try:
            node_id = nova.get_node(self.msg['name'])
        except NotFound:
            self.logger.error(
                "No node found for {0}".format(self.msg['name'])
            )
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg
        nova.delete(node_id)
        self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
        self.logger.info(
            'Deleted node {0}, id {1}'.format(self.msg['name'], node_id)
        )
        return self.msg
