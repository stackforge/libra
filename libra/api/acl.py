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


def install(app, args):
    """Install ACL check on application."""
    config = ConfigParser.SafeConfigParser()
    config.read([args.config])
    module_details = args.keystone_module.split(':')
    keystone = importlib.import_module(module_details[0])
    auth_class = getattr(keystone, module_details[1])
    return auth_class(app, config._sections['keystone'])


def get_limited_to_project(headers):
    """Return the tenant the request should be limited to."""
    return headers.get('X-Tenant-Id')
