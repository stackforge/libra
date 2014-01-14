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

import ipaddress
from pecan import response, expose, request
from pecan.rest import RestController
from libra.common.api.lbaas import LoadBalancer, Vip, Device, db_session
from libra.common.api.lbaas import Counters
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
                message="Bad Request",
                details="Load Balancer ID not provided"
            )
        with db_session() as session:
            vip = session.query(
                Vip.id, Vip.ip
            ).join(LoadBalancer.devices).\
                join(Device.vip).\
                filter(LoadBalancer.id == self.lbid).\
                filter(LoadBalancer.tenantid == tenant_id).first()

            if not vip:
                session.rollback()
                response.status = 404
                return dict(
                    message="Not Found",
                    details="Load Balancer ID not valid"
                )
            resp = {
                "virtualIps": [{
                    "id": vip.id,
                    "address": str(ipaddress.IPv4Address(vip.ip)),
                    "type": "PUBLIC",
                    "ipVersion": "IPV4"
                }]
            }
            counter = session.query(Counters).\
                filter(Counters.name == 'api_vips_get').first()
            counter.value += 1
            session.rollback()
            return resp
