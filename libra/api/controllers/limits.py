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

from pecan import expose, request
from pecan.rest import RestController
from libra.api.acl import get_limited_to_project
from libra.common.api.lbaas import Limits, TenantLimits, db_session


class LimitsController(RestController):
    @expose('json')
    def get(self):
        resp = {}
        tenant_id = get_limited_to_project(request.headers)

        with db_session() as session:
            limits = session.query(Limits).all()

            # Get per-tenant values
            tenant_lblimit = session.query(TenantLimits.loadbalancers).\
                filter(TenantLimits.tenantid == tenant_id).scalar()

            for limit in limits:
                resp[limit.name] = limit.value

            # Set per-tenant values
            if tenant_lblimit:
                resp['maxLoadBalancers'] = tenant_lblimit

            resp = {"limits": {"absolute": {"values": resp}}}
            session.rollback()
            return resp
