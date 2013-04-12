import logging
import testtools
import libra.tests.mock_objects
from libra import __version__ as libra_version
from libra import __release__ as libra_release
from libra.worker.controller import LBaaSController as c
from libra.worker.drivers.base import LoadBalancerDriver
from libra.worker.drivers.haproxy.driver import HAProxyDriver


class TestWorkerController(testtools.TestCase):
    def setUp(self):
        super(TestWorkerController, self).setUp()
        self.logger = logging.getLogger('test_worker_controller')
        self.lh = libra.tests.mock_objects.MockLoggingHandler()
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.lh)
        self.driver = HAProxyDriver('libra.tests.mock_objects.FakeOSServices',
                                    None, None)

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
            'LoAdBaLaNcErS': [{'protocol': 'http'}]
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
            c.LBLIST_FIELD: [{'protocol': 'http'}]
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
        msg = {
            c.ACTION_FIELD: 'DISCOVER'
        }
        controller = c(self.logger, self.driver, msg)
        response = controller.run()
        self.assertIn('version', response)
        self.assertIn('release', response)
        self.assertEquals(response[c.RESPONSE_FIELD], c.RESPONSE_SUCCESS)
        self.assertEquals(response['version'], libra_version)
        self.assertEquals(response['release'], libra_release)

    def testArchiveMissingMethod(self):
        msg = {
            c.ACTION_FIELD: 'ARCHIVE'
        }
        null_driver = LoadBalancerDriver()
        controller = c(self.logger, null_driver, msg)
        response = controller.run()
        self.assertIn('badRequest', response)

    def testArchiveInvalidMethod(self):
        msg = {
            c.ACTION_FIELD: 'ARCHIVE',
            c.OBJ_STORE_TYPE_FIELD: 'bad'
        }
        null_driver = LoadBalancerDriver()
        controller = c(self.logger, null_driver, msg)
        response = controller.run()
        self.assertIn('badRequest', response)

    def testArchiveSwiftRequiredParams(self):
        null_driver = LoadBalancerDriver()

        # Missing basepath field
        msg = {
            c.ACTION_FIELD: 'ARCHIVE',
            c.OBJ_STORE_TYPE_FIELD: 'Swift',
            c.OBJ_STORE_ENDPOINT_FIELD: "https://example.com",
            c.OBJ_STORE_TOKEN_FIELD: "XXXX",
            c.LBLIST_FIELD: [{'protocol': 'http', 'id': '123'}]
        }
        controller = c(self.logger, null_driver, msg)
        response = controller.run()
        self.assertIn('badRequest', response)

        # Missing endpoint field
        msg = {
            c.ACTION_FIELD: 'ARCHIVE',
            c.OBJ_STORE_TYPE_FIELD: 'Swift',
            c.OBJ_STORE_BASEPATH_FIELD: "/lbaaslogs",
            c.OBJ_STORE_TOKEN_FIELD: "XXXX",
            c.LBLIST_FIELD: [{'protocol': 'http', 'id': '123'}]
        }
        controller = c(self.logger, null_driver, msg)
        response = controller.run()
        self.assertIn('badRequest', response)

        # Missing token field
        msg = {
            c.ACTION_FIELD: 'ARCHIVE',
            c.OBJ_STORE_TYPE_FIELD: 'Swift',
            c.OBJ_STORE_BASEPATH_FIELD: "/lbaaslogs",
            c.OBJ_STORE_ENDPOINT_FIELD: "https://example.com",
            c.LBLIST_FIELD: [{'protocol': 'http', 'id': '123'}]
        }
        controller = c(self.logger, null_driver, msg)
        response = controller.run()
        self.assertIn('badRequest', response)

        # Missing load balancer field
        msg = {
            c.ACTION_FIELD: 'ARCHIVE',
            c.OBJ_STORE_TYPE_FIELD: 'Swift',
            c.OBJ_STORE_BASEPATH_FIELD: "/lbaaslogs",
            c.OBJ_STORE_ENDPOINT_FIELD: "https://example.com",
            c.OBJ_STORE_TOKEN_FIELD: "XXXX"
        }
        controller = c(self.logger, null_driver, msg)
        response = controller.run()
        self.assertIn('badRequest', response)

    def testArchiveNotImplemented(self):
        msg = {
            c.ACTION_FIELD: 'ARCHIVE',
            c.OBJ_STORE_TYPE_FIELD: 'Swift',
            c.OBJ_STORE_BASEPATH_FIELD: "/lbaaslogs",
            c.OBJ_STORE_ENDPOINT_FIELD: "https://example.com",
            c.OBJ_STORE_TOKEN_FIELD: "XXXX",
            c.LBLIST_FIELD: [{'protocol': 'http', 'id': '123'}]
        }
        null_driver = LoadBalancerDriver()
        controller = c(self.logger, null_driver, msg)
        response = controller.run()
        self.assertEquals(response[c.RESPONSE_FIELD], c.RESPONSE_FAILURE)
        self.assertIn(c.ERROR_FIELD, response)
        self.assertEquals(response[c.ERROR_FIELD],
                          "Selected driver does not support ARCHIVE action.")
