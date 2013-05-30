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
from v1 import V1Controller
from libra.admin_api.model.responses import Responses


class RootController(object):
    """root control object."""

    @expose('json')
    def _default(self):
        """default route.. acts as catch all for any wrong urls.
           For now it returns a 404 because no action is defined for /"""
        response.status = 404
        return Responses._default

    @expose()
    def _lookup(self, primary_key, *remainder):
        if primary_key == 'v1':
            return V1Controller(), remainder
        else:
            response.status = 404
            return Responses._default

    @expose('json')
    def notfound(self):
        return Responses._default
