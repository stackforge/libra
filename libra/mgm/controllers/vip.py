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

from novaclient import exceptions
from libra.mgm.nova import Node


class BuildIpController(object):

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

        self.logger.info("Creating a requested floating IP")
        try:
            ip_info = nova.vip_create()
        except exceptions.ClientException:
            self.logger.exception(
                'Error getting a Floating IP'
            )
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg
        self.msg['id'] = ip_info['id']
        self.msg['ip'] = ip_info['ip']
        self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
        return self.msg


class AssignIpController(object):

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

        self.logger.info(
            "Assigning Floating IP {0} to {1}"
            .format(self.msg['ip'], self.msg['node_id'])
        )
        try:
            node_id = int(self.msg['node_id'])
            nova.vip_assign(node_id, self.msg['ip'])
        except:
            self.logger.exception(
                'Error assigning Floating IP {0} to {1}'
                .format(self.msg['ip'], node_id)
            )
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg

        self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
        return self.msg
