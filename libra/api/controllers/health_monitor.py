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

from pecan import response
from libra.api.library.libra_rest_controller import LibraController


class HealthMonitorController(LibraController):
    """functions for /loadbalancers/{loadBalancerId}/healthmonitor/* routing"""

    def get(self, load_balancer_id):
        """Retrieve the health monitor configuration, if one exists.

        :param load_balancer_id: id of lb

        Url:
           GET /loadbalancers/{load_balancer_id}/healthmonitor

        Returns: dict
        """
        response.status = 201
        return None

    def post(self, load_balancer_id, *args):
        """Update the settings for a health monitor.

        :param load_balancer_id: id of lb
        :param *args: holds the posted json or xml data

        Url:
           PUT /loadbalancers/{load_balancer_id}/healthmonitor

        Returns: dict
        """
        response.status = 201
        return None

    def delete(self, load_balancer_id):
        """Remove the health monitor.

        :param load_balancer_id: id of lb

        Url:
           DELETE /loadbalancers/{load_balancer_id}/healthmonitor

        Returns: void
        """
        response.status = 201
