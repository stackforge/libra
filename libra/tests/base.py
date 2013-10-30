from libra.openstack.common.test import BaseTestCase
from libra.openstack.common.fixture import config
from libra.openstack.common import log
from libra.common import options


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

        self.CONF([], project='libra')

        log.setup('libra')