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


class SessionPersistenceController(RestController):
    """SessionPersistenceController
    functions for /loadbalancers/{loadBalancerId}/sessionpersistence/* routing
    """

    @expose('json')
    def get(self, load_balancer_id):
        """List session persistence configuration.get

        :param load_balancer_id: id of lb

        Url:
           GET /loadbalancers/{load_balancer_id}/sessionpersistence

        Returns: dict
        """
        response.status = 201
        return Responses.LoadBalancers.SessionPersistence.get

    @expose('json')  
    def post(self, load_balancer_id):
        """Enable session persistence.

        :param load_balancer_id: id of lb

        Url:
            PUT /loadbalancers/{load_balancer_id}/sessionpersistence

        Returns: dict
        """
        response.status = 201
        return Responses.LoadBalancers.SessionPersistence.get

    @expose('json')
    def delete(self, load_balancer_id):
        """Disable session persistence.

        :param load_balancer_id: id of lb

        Url:
           DELETE /loadbalancers/{load_balancer_id}/sessionpersistence

        Returns: dict
        """
        response.status = 201

