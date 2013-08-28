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

from libra.mgm.controllers.build import BuildController
from libra.mgm.controllers.delete import DeleteController
from libra.mgm.controllers.vip import BuildIpController, AssignIpController
from libra.mgm.controllers.vip import RemoveIpController


class PoolMgmController(object):

    ACTION_FIELD = 'action'
    RESPONSE_FIELD = 'response'
    RESPONSE_SUCCESS = 'PASS'
    RESPONSE_FAILURE = 'FAIL'

    def __init__(self, logger, args, json_msg):
        self.logger = logger
        self.msg = json_msg
        self.args = args

    def run(self):
        if self.ACTION_FIELD not in self.msg:
            self.logger.error("Missing `{0}` value".format(self.ACTION_FIELD))
            self.msg[self.RESPONSE_FILED] = self.RESPONSE_FAILURE
            return self.msg

        action = self.msg[self.ACTION_FIELD].upper()

        try:
            if action == 'BUILD_DEVICE':
                controller = BuildController(self.logger, self.args, self.msg)
            elif action == 'DELETE_DEVICE':
                controller = DeleteController(self.logger, self.args, self.msg)
            elif action == 'BUILD_IP':
                controller = BuildIpController(
                    self.logger, self.args, self.msg
                )
            elif action == 'ASSIGN_IP':
                controller = AssignIpController(
                    self.logger, self.args, self.msg
                )
            elif action == 'REMOVE_IP':
                controller = RemoveIpController(
                    self.logger, self.args, self.msg
                )
            else:
                self.logger.error(
                    "Invalid `{0}` value: {1}".format(
                        self.ACTION_FIELD, action
                    )
                )
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                return self.msg
            return controller.run()
        except Exception:
            self.logger.exception("Controller exception")
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg
