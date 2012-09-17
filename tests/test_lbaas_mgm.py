import unittest
import logging

import mock


class TestLBaaSMgmTask(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger('lbass_mgm_test')
        self.lh = mock.MockLoggingHandler()
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.lh)

    def tearDown(self):
        pass
