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

import ConfigParser
import importlib

from oslo.config import cfg
from pecan import request

from libra.openstack.common import log
from libra.common.api.lbaas import db_session, AdminAuth

LOG = log.getLogger(__name__)


def get_limited_to_project(headers):
    """Return the tenant the request should be limited to."""
    tenant_id = headers.get('X-Tenant-Id')
    LOG.info(
        'Admin API {0} request {1} ({2}) from {3} tenant {4}'.format(
            request.environ.get('REQUEST_METHOD'),
            request.environ.get('PATH_INFO'),
            request.environ.get('QUERY_STRING'),
            request.environ.get('REMOTE_ADDR'),
            tenant_id
        )
    )

    return tenant_id


def tenant_is_type(headers, tenant_types):
    """ Check the tenant ID is a user of the Admin API and allowed to use the
    API command specified
    """
    tenant_id = get_limited_to_project(headers)
    if not tenant_id:
        return False
    with db_session() as session:
        is_auth = session.query(AdminAuth).\
            filter(AdminAuth.tenant_id == tenant_id).\
            filter(AdminAuth.level.in_(tenant_types)).count()
        if is_auth > 0:
            session.commit()
            return True
        session.commit()
    return False


def tenant_is_user(headers):
    return tenant_is_type(headers, ['USER', 'ADMIN'])


def tenant_is_admin(headers):
    return tenant_is_type(headers, ['ADMIN'])


class AuthDirector(object):
    """ There are some paths we want to work unauthenticated.  This class
        will direct intentionally unauthenticated requests to the relevant
        controllers. """

    def __init__(self, app):
        self.unauthed_app = app
        if not cfg.CONF['admin_api']['disable_keystone']:
            self.app = self._install()
        else:
            self.app = app

    def __call__(self, env, start_response):
        uri = env['PATH_INFO']
        if uri in ['/', '/v1', '/v1/', '/v2.0', '/v2.0/']:
            return self.unauthed_app(env, start_response)
        else:
            return self.app(env, start_response)

    def _install(self):
        """Install ACL check on application."""
        config = ConfigParser.SafeConfigParser()
        config.read(cfg.CONF['config_file'])
        module_details = cfg.CONF['admin_api']['keystone_module'].split(':')
        keystone = importlib.import_module(module_details[0])
        auth_class = getattr(keystone, module_details[1])
        return auth_class(self.unauthed_app, config._sections['keystone'])
