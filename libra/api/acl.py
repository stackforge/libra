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

from keystoneclient.middleware import auth_token


def install(app, args):
    """Install ACL check on application."""
    conf = {
        'auth_host': args.keystone_host,
        'auth_port': args.keystone_port,
        'auth_protocol': args.keystone_protocol,
        'certfile': args.keystone_certfile,
        'keyfile': args.keystone_keyfile
    }
    return auth_token.AuthProtocol(app, conf)


def get_limited_to_project(headers):
    """Return the tenant the request should be limited to."""
    return headers.get('X-Tenant-Id')
