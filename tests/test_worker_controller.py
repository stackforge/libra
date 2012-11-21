import logging
import mock_objects
import unittest
from libra.worker.controller import LBaaSController as c
from libra.worker.drivers.haproxy.driver import HAProxyDriver


class TestWorkerController(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger('test_worker_controller')
        self.lh = mock_objects.MockLoggingHandler()
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.lh)
        self.driver = HAProxyDriver('mock_objects.FakeOSServices')

    def tearDown(self):
        pass

    def testBadAction(self):
        msg = {
            c.ACTION_FIELD: 'BOGUS'
        }
        controller = c(self.logger, self.driver, msg)
        response = controller.run()
        self.assertIn(c.RESPONSE_FIELD, response)
        self.assertEquals(response[c.RESPONSE_FIELD], c.RESPONSE_FAILURE)

    def testUpdate(self):
        msg = {
            c.ACTION_FIELD: 'UPDATE',
            'loadbalancers': [
                {
                   'protocol': 'http',
                   'nodes': [
                        {
                            'address': '10.0.0.1',
                            'port': 80
                        }
                    ]
                }
            ]
        }
        controller = c(self.logger, self.driver, msg)
        response = controller.run()
        self.assertIn(c.RESPONSE_FIELD, response)
        self.assertEquals(response[c.RESPONSE_FIELD], c.RESPONSE_SUCCESS)

    def testSuspend(self):
        msg = {
            c.ACTION_FIELD: 'SUSPEND'
        }
        controller = c(self.logger, self.driver, msg)
        response = controller.run()
        self.assertIn(c.RESPONSE_FIELD, response)
        self.assertEquals(response[c.RESPONSE_FIELD], c.RESPONSE_SUCCESS)

    def testEnable(self):
        msg = {
            c.ACTION_FIELD: 'ENABLE'
        }
        controller = c(self.logger, self.driver, msg)
        response = controller.run()
        self.assertIn(c.RESPONSE_FIELD, response)
        self.assertEquals(response[c.RESPONSE_FIELD], c.RESPONSE_SUCCESS)

    def testDelete(self):
        msg = {
            c.ACTION_FIELD: 'DELETE'
        }
        controller = c(self.logger, self.driver, msg)
        response = controller.run()
        self.assertIn(c.RESPONSE_FIELD, response)
        self.assertEquals(response[c.RESPONSE_FIELD], c.RESPONSE_SUCCESS)

    def testCreateMissingLBs(self):
        msg = {
            c.ACTION_FIELD: 'UPDATE'
        }
        controller = c(self.logger, self.driver, msg)
        response = controller.run()
        self.assertIn('badRequest', response)

    def testCreateMissingNodes(self):
        msg = {
            c.ACTION_FIELD: 'UPDATE',
            'loadbalancers': [ { 'protocol': 'http' } ]
        }
        controller = c(self.logger, self.driver, msg)
        response = controller.run()
        self.assertIn('badRequest', response)

    def testCreateMissingProto(self):
        msg = {
            c.ACTION_FIELD: 'UPDATE',
            'loadbalancers': [
                {
                   'nodes': [
                        {
                            'address': '10.0.0.1',
                            'port': 80
                        }
                    ]
                }
            ]
        }
        controller = c(self.logger, self.driver, msg)
        response = controller.run()
        self.assertIn('badRequest', response)

    def testBadAlgorithm(self):
        msg = {
            c.ACTION_FIELD: 'UPDATE',
            'loadbalancers': [
                {
                    'protocol': 'http',
                    'algorithm': 'BOGUS',
                    'nodes': [
                        {
                            'address': '10.0.0.1',
                            'port': 80
                        }
                    ]
                }
            ]
        }
        controller = c(self.logger, self.driver, msg)
        response = controller.run()
        self.assertIn(c.RESPONSE_FIELD, response)
        self.assertEquals(response[c.RESPONSE_FIELD], c.RESPONSE_FAILURE)
