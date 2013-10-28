from libra.tests.api import base


class FunctionalTest(DBTestCase):
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
