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
from load_balancers import LoadBalancersController
from limits import LimitsController
from libra.api.model.responses import Responses


class V1Controller(object):
    """v1 control object."""

    @expose('json')
    def index(self):
        response.status = 200
        return Responses.v1_1

    @expose('json')
    def protocols(self):
        """Lists all supported load balancing protocols.

        Url:
           GET /protocols

        Returns: dict
        """
        response.status = 200
        return Responses.protocols

    @expose('json')
    def algorithms(self):
        """List all supported load balancing algorithms.

        Url:
           GET /algorithms

        Returns: dict
        """
        response.status = 200
        return Responses.algorithms

    #pecan uses this controller class for urls that start with /loadbalancers
    loadbalancers = LoadBalancersController()
    limits = LimitsController()
