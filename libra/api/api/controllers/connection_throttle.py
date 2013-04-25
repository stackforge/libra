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

from pecan import expose, redirect, abort, response
from pecan.rest import RestController

from api.model.responses import Responses


class ConnectionThrottleController(RestController):
    """functions for /loadbalancers/{loadBalancerId}/connectionthrottle/* routing"""

    @expose('json')
    def get(self, load_balancer_id):
        """List connection throttling configuration.

        :param load_balancer_id: id of lb

        Url:
           GET /loadbalancers/{load_balancer_id}/connectionthrottle

        Returns: dict
        """
        response.status = 201
        return Responses.LoadBalancers.ConnectionThrottle.get

    @expose('json')
    def post(self, load_balancer_id, *args):
        """Update throttling configuration.

        :param load_balancer_id: id of lb
        :param *args: holds the posted json or xml

        Url:
           PUT /loadbalancers/loadBalancerId/connectionthrottle

        Returns: dict
        """
        response.status = 201
        return Responses.LoadBalancers.ConnectionThrottle.get

    @expose()
    def delete(self, loadbalancer_id):
        """Remove connection throttling configurations.

        :param load_balancer_id: id of lb

        Url:
           DELETE /loadbalancers/loadBalancerId/connectionthrottle

        Returns: void
        """
        response.status = 201

