# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright 2014 Hewlett-Packard Development Company, L.P.
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

import json
# pecan imports
from pecan import expose, request, response
from pecan.rest import RestController
from libra.openstack.common import log
from libra.admin_api.acl import tenant_is_user, tenant_is_admin
from libra.admin_api.acl import get_limited_to_project
from libra.common.api.lbaas import db_session, AdminAuth

LOG = log.getLogger(__name__)


class UserController(RestController):
    @expose('json')
    def get_all(self):
        """
        Get a list of users
        """
        if not tenant_is_admin(request.headers):
            response.status = 401
            return dict(
                faultcode="Client",
                faultstring="Client not authorized to access this function"
            )

        with db_session() as session:
            user = session.query(
                AdminAuth.tenant_id.label('tenant'), AdminAuth.level
            ).all()
            session.commit()
        return user

    @expose('json')
    def get_one(self, tenant_id=None):
        """
        Get a single Admin API user or details about self
        """
        if not tenant_is_user(request.headers):
            response.status = 401
            return dict(
                faultcode="Client",
                faultstring="Client not authorized to access this function"
            )

        with db_session() as session:
            user = session.query(AdminAuth).\
                filter(AdminAuth.tenant_id == tenant_id).first()
            if user is None:
                response.status = 404
                return dict(
                    faultcode="Client",
                    faultstatus="User not found"
                )
            ret = {
                "tenant": user.tenant_id,
                "level": user.level
            }
            session.commit()
        return ret

    @expose('json')
    def delete(self, tenant_id):
        """ Delete a given user from the Admin API """
        if not tenant_is_admin(request.headers):
            response.status = 401
            return dict(
                faultcode="Client",
                faultstring="Client not authorized to access this function"
            )
        with db_session() as session:
            user_test = session.query(AdminAuth).\
                filter(AdminAuth.tenant_id == tenant_id).count()
            if user_test == 0:
                response.status = 404
                return dict(
                    faultcode="Client",
                    faultstring="Tenant not found"
                )
            session.query(AdminAuth).\
                filter(AdminAuth.tenant_id == tenant_id).delete()
            session.commit()
        response.status = 204
        return None

    @expose('json')
    def post(self):
        """ Add a new user to the Admin API """
        if not tenant_is_admin(request.headers):
            response.status = 401
            return dict(
                faultcode="Client",
                faultstring="Client not authorized to access this function"
            )
        try:
           data = json.loads(request.body)
        except:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Invalid JSON received"
            )
        if data['tenant'] is None:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Tenant ID required"
            )
        tenant_id = data['tenant']
        if 'level' not in data:
            level = 'USER'
        elif data['level'] not in ['USER', 'ADMIN']:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Only USER or ADMIN levels allowed"
            )
        else:
            level = data['level']
        with db_session() as session:
            user_test = session.query(AdminAuth).\
                filter(AdminAuth.tenant_id == tenant_id).count()
            if user_test > 0:
                response.status = 400
                return dict(
                    faultcode="Client",
                    faultstring="Tenant already has an account"
                )
            user = AdminAuth()
            user.tenant_id = tenant_id
            user.level = level
            session.add(user)
            session.commit()

    @expose('json')
    def put(self, tenant_id):
        """ Change the leve for an Admin API user """
        if not tenant_is_admin(request.headers):
            response.status = 401
            return dict(
                faultcode="Client",
                faultstring="Client not authorized to access this function"
            )
        try:
           data = json.loads(request.body)
        except:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Invalid JSON received"
            )
        if tenant_id is None:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Tenant ID required"
            )
        if not data['level']:
            level = 'USER'
        elif data['level'] not in ['USER', 'ADMIN']:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Only USER or ADMIN levels allowed"
            )
        else:
            level = data['level']
        with db_session() as session:
            user = session.query(AdminAuth).\
                filter(AdminAuth.tenant_id == tenant_id).first()
            if not user:
                response.status = 404
                return dict(
                    faultcode="Client",
                    faultstring="Tenant does not have an account"
                )
            user.level = level
            session.commit()
