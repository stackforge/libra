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

from pecan import response, expose, request
from pecan.rest import RestController
from libra.api.model.lbaas import LoadBalancer, Device, session
from libra.api.acl import get_limited_to_project


class VipsController(RestController):
    def __init__(self, load_balancer_id=None):
        self.lbid = load_balancer_id

    @expose('json')
    def get(self):
        """Returns a list of virtual ips attached to a specific Load Balancer.

        :param load_balancer_id: id of lb

        Url:
           GET /loadbalancers/{load_balancer_id}/virtualips

        Returns: dict
        """
        tenant_id = get_limited_to_project(request.headers)
        if not self.lbid:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Load Balancer ID not provided"
            )
        device = session.query(
            Device.id, Device.floatingIpAddr
        ).join(LoadBalancer.devices).\
            filter(LoadBalancer.id == self.lbid).\
            filter(LoadBalancer.tenantid == tenant_id).first()

        if not device:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Load Balancer ID not valid"
            )
        resp = {
            "virtualIps": [{
                "id": device.id,
                "address": device.floatingIpAddr,
                "type": "PUBLIC",
                "ipVersion": "IPV4"
            }]
        }

        return resp
