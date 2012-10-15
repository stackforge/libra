import unittest
from libra.worker.drivers.haproxy.driver import HAProxyDriver


class TestHAProxyDriver(unittest.TestCase):
    def setUp(self):
        self.driver = HAProxyDriver('mock_objects.FakeOSServices')

    def tearDown(self):
        pass

    def testInit(self):
        """ Test the HAProxy init() method """
        self.driver.init()
        self.assertIsInstance(self.driver._config, dict)
        self.assertEqual(self.driver._config['mode'], 'http')
        self.assertEqual(self.driver._config['bind_address'], '0.0.0.0')
        self.assertEqual(self.driver._config['bind_port'], 80)

    def testSetProtocol(self):
        """ Test the HAProxy set_protocol() method """
        self.driver.set_protocol('http', None)
        self.assertEqual(self.driver._config['bind_address'], '0.0.0.0')
        self.assertEqual(self.driver._config['bind_port'], 80)
        self.assertEqual(self.driver._config['mode'], 'http')

        self.driver.set_protocol('http', 8080)
        self.assertEqual(self.driver._config['bind_address'], '0.0.0.0')
        self.assertEqual(self.driver._config['bind_port'], 8080)
        self.assertEqual(self.driver._config['mode'], 'http')

        self.driver.set_protocol('tcp', 443)
        self.assertEqual(self.driver._config['bind_address'], '0.0.0.0')
        self.assertEqual(self.driver._config['bind_port'], 443)
        self.assertEqual(self.driver._config['mode'], 'tcp')

        with self.assertRaises(Exception):
            self.driver.set_protocol('tcp', None)

    def testAddServer(self):
        """ Test the HAProxy add_server() method """
        self.driver.add_server('1.2.3.4', 7777)
        self.driver.add_server('5.6.7.8', 8888)
        self.assertIn('servers', self.driver._config)
        servers = self.driver._config['servers']
        self.assertEqual(len(servers), 2)
        self.assertEqual(servers[0], ('1.2.3.4', 7777))
        self.assertEqual(servers[1], ('5.6.7.8', 8888))

    def testSetAlgorithm(self):
        """ Test the HAProxy set_algorithm() method """
        self.driver.set_algorithm(self.driver.ROUNDROBIN)
        self.assertEqual(self.driver._config['algorithm'], 'roundrobin')
        self.driver.set_algorithm(self.driver.LEASTCONN)
        self.assertEqual(self.driver._config['algorithm'], 'leastconn')
        with self.assertRaises(Exception):
            self.driver.set_protocol(99)
