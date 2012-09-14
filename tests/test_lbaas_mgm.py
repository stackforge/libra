import unittest
import logging

import mock

from libra.mgm.listener import Listener


class TestLBaaSMgmTask(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger('lbass_mgm_test')
        self.lh = mock.MockLoggingHandler()
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.lh)

    def tearDown(self):
        pass

    def testTaskGet(self):
        listener = Listener(self.logger)
        data = {'command': 'get'}
        job = mock.FakeJob(data)
        result = listener.task(None, job)
        self.assertIn('Command: get', self.lh.messages['debug'])
        self.assertEqual(result['command'], data['command'])

    def testTaskBad(self):
        listener = Listener(self.logger)
        data = {'command': 'bad'}
        job = mock.FakeJob(data)
        result = listener.task(None, job)
        self.assertIn("badRequest", result)
        self.assertIn("validationErrors", result['badRequest'])
        self.assertEqual(
            "Invalid command",
            result['badRequest']['validationErrors']['message']
        )
