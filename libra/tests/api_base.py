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


from libra.tests import base
import pecan
import pecan.testing

from oslo.config import cfg


class TestCase(base.TestCase):
    """Used for functional tests of Pecan controllers where you need to
    test your literal application and its integration with the
    framework.
    """
    def _make_app(self, config=None, enable_acl=False):
        # Determine where we are so we can set up paths in the config
        root_dir = self.path_get()
        self.config = config or self.config
        return pecan.testing.load_test_app(self.config)

    def tearDown(self):
        super(FunctionalTest, self).tearDown()
        self.app = None
        pecan.set_config({}, overwrite=True)
