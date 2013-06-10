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

# Pecan Application Configurations
app = {
    'root': 'libra.admin_api.controllers.root.RootController',
    'modules': ['libra.admin_api'],
    'static_root': '%(confdir)s/public',
    'template_path': '%(confdir)s/admin_api/templates',
    'errors': {
        404: '/notfound',
        '__force_dict__': True
    }
}
