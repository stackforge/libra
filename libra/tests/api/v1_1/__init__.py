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
from libra.tests import api_base


"""
Base TestCase for V1.1 API tests.
"""


class TestCase(api_base.TestCase):
    def setUp(self):
        root_dir = self.path_get()

        config = {
            'app': {
                'root': 'libra.api.controllers.root.RootController',
                'modules': ['libra.api'],
                'static_root': '%s/public' % root_dir,
                'template_path': '%s/libra/api/templates' % root_dir,
                'enable_acl': False,
            },
            'wsme': {
                'debug': True,
            }
        }
        self.app = self._make_app(config)
