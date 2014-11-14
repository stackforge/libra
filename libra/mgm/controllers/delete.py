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
from libra.openstack.common import log
from libra.common.api.lbaas import db_session


LOG = log.getLogger(__name__)


class DeleteController(object):

    RESPONSE_FIELD = 'response'
    RESPONSE_SUCCESS = 'PASS'
    RESPONSE_FAILURE = 'FAIL'

    def __init__(self, msg):
        self.msg = msg

    def run(self):

        # TODO rate-limit this action with the following algorithm,
        # using the options:
        # - rate_limit_delete_device_period ("period"): seconds to look back
        # - rate_limit_delete_device_max_count ("max_count"): actions allowed
        #
        # 1. INSERT a row into rate_limited_actions for the 'DELETE_DEVICE'
        # resource, with use_time set to the current time; store the
        # inserted_primary_key.
        #
        # 2. SELECT the COUNT() of rows in that table for that resource with
        # use_time within the last period seconds;
        #   2a. if that count > max_count, DELETE the row we just inserted,
        #   pause a short randomly-fuzzed number of seconds (roughly
        #   period/max_count), then return to step 1.
        #
        # 3. if that count <= max_count, proceed with the delete action.

        try:
            nova = Node()
        except Exception:
            LOG.exception("Error initialising Nova connection")
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg

        LOG.info(
            "Deleting a requested Nova instance {0}".format(self.msg['name'])
        )
        try:
            node_id = nova.get_node(self.msg['name'])
        except NotFound:
            LOG.error(
                "No node found for {0}".format(self.msg['name'])
            )
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg
        nova.delete(node_id)
        self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
        LOG.info(
            'Deleted node {0}, id {1}'.format(self.msg['name'], node_id)
        )
        return self.msg
