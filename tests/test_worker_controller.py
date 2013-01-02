import logging
import testtools
import tests.mock_objects
from libra.worker.controller import LBaaSController as c
from libra.worker.drivers.haproxy.driver import HAProxyDriver


class TestWorkerController(testtools.TestCase):
    def setUp(self):
        super(TestWorkerController, self).setUp()
        self.logger = logging.getLogger('test_worker_controller')
        self.lh = tests.mock_objects.MockLoggingHandler()
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.lh)
        self.driver = HAProxyDriver('tests.mock_objects.FakeOSServices')

    def testBadAction(self):
        msg = {
            c.ACTION_FIELD: 'BOGUS'
        }
        controller = c(self.logger, self.driver, msg)
        response = controller.run()
        self.assertIn(c.RESPONSE_FIELD, response)
        self.assertEquals(response[c.RESPONSE_FIELD], c.RESPONSE_FAILURE)

    def testCaseSensitive(self):
        msg = {
            c.ACTION_FIELD: 'UPDATE',
            'LoAdBaLaNcErS': [ { 'protocol': 'http' } ]
        }
        controller = c(self.logger, self.driver, msg)
        response = controller.run()
        self.assertIn('badRequest', response)

    def testUpdate(self):
        msg = {
            c.ACTION_FIELD: 'UPDATE',
            c.LBLIST_FIELD: [
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
            c.LBLIST_FIELD: [ { 'protocol': 'http' } ]
        }
        controller = c(self.logger, self.driver, msg)
        response = controller.run()
        self.assertIn('badRequest', response)

    def testCreateMissingProto(self):
        msg = {
            c.ACTION_FIELD: 'UPDATE',
            c.LBLIST_FIELD: [
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
            c.LBLIST_FIELD: [
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

    def testDiscover(self):
        msg = { c.ACTION_FIELD: 'DISCOVER' }
        controller = c(self.logger, self.driver, msg)
        response = controller.run()
        self.assertIn('version', response)
        self.assertEquals(response[c.RESPONSE_FIELD], c.RESPONSE_SUCCESS)
