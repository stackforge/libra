# vim: tabstop=4 shiftwidth=4 softtabstop=4
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

from pecan import expose, response
from libra.admin_api.model.lbaas import Device, session
from libra.admin_api.model.responses import Responses
from pecan.rest import RestController


class UsageController(RestController):

    @expose('json')
    def get(self):
        """Reports the device usage statistics for total, taken, and free
            :param None
            Url:
                GET /devices/usage
            Returns: dict
        """
        total = session.query(Device).count()
        free = session.query(Device).filter(Device.status == 'OFFLINE').\
            count()
        session.commit()
        response.status = 200

        return dict(
            total=total,
            free=free,
            taken=total - free
        )

    @expose('json')
    def _default(self):
        """default route.. acts as catch all for any wrong urls.
            For now it returns a 404 because no action is defined for /"""
        response.status = 404
        return Responses._default
