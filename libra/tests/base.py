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

from libra.openstack.common.test import BaseTestCase
from libra.openstack.common.fixture import config
from libra.openstack.common import log
from libra.common import options

# NOTE: Tests fail due to diverse options being required.
options.CONF.import_group('api', 'libra.api')
options.CONF.import_group('mgm', 'libra.mgm')


class TestBase(BaseTestCase):
    def setUp(self):
        super(TestBase, self).setUp()
        options.add_common_opts()
        self.CONF = self.useFixture(config.Config(options.CONF)).conf

        # NOTE: Provide some fun defaults for testing
        self.CONF.set_override('az', 'default', group='mgm')
        self.CONF.set_override('nova_secgroup', 'default', group='mgm')
        self.CONF.set_override('nova_image', 'image', group='mgm')
        self.CONF.set_override('nova_image_size', 'm1.small', group='mgm')
        self.CONF.set_override('nova_keyname', 'key', group='mgm')
        self.CONF.set_override('nova_user', 'user', group='mgm')
        self.CONF.set_override('nova_pass', 'secret', group='mgm')
        self.CONF.set_override('nova_auth_url', 'http://localhost:35357/2.0',
                               group='mgm')
        self.CONF.set_override('nova_region', 'region', group='mgm')

        self.CONF.set_override('db_sections', 'test', group='api')
        self.CONF.set_override('swift_endpoint', 'test', group='api')
        self.CONF.set_override('swift_basepath', 'test', group='api')

        self.CONF.set_override('driver', 'gearman_fake', group='gearman')

        self.CONF([], project='libra')

        log.setup('libra')
