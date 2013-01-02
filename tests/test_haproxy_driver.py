import testtools
import tests.mock_objects
from libra.worker.drivers.haproxy.driver import HAProxyDriver


class TestHAProxyDriver(testtools.TestCase):
    def setUp(self):
        super(TestHAProxyDriver, self).setUp()
        self.driver = HAProxyDriver('tests.mock_objects.FakeOSServices')

    def testInit(self):
        """ Test the HAProxy init() method """
        self.driver.init()
        self.assertIsInstance(self.driver._config, dict)

    def testAddProtocol(self):
        """ Test the HAProxy set_protocol() method """
        proto = 'http'
        self.driver.add_protocol(proto, None)
        self.assertIn(proto, self.driver._config)
        self.assertEqual(self.driver._config[proto]['bind_address'], '0.0.0.0')
        self.assertEqual(self.driver._config[proto]['bind_port'], 80)

        proto = 'tcp'
        self.driver.add_protocol(proto, 443)
        self.assertIn(proto, self.driver._config)
        self.assertEqual(self.driver._config[proto]['bind_address'], '0.0.0.0')
        self.assertEqual(self.driver._config[proto]['bind_port'], 443)

    def testAddTCPRequiresPort(self):
        e = self.assertRaises(Exception, self.driver.add_protocol, 'tcp', None)
        self.assertEqual("Port is required for TCP protocol.", e.message)

    def testAddServer(self):
        """ Test the HAProxy add_server() method """
        proto = 'http'
        self.driver.add_protocol(proto, None)
        self.driver.add_server(proto, '1.2.3.4', 7777)
        self.driver.add_server(proto, '5.6.7.8', 8888)
        self.assertIn(proto, self.driver._config)
        self.assertIn('servers', self.driver._config[proto])
        servers = self.driver._config[proto]['servers']
        self.assertEqual(len(servers), 2)
        self.assertEqual(servers[0], ('1.2.3.4', 7777))
        self.assertEqual(servers[1], ('5.6.7.8', 8888))

    def testSetAlgorithm(self):
        """ Test the HAProxy set_algorithm() method """
        proto = 'http'
        self.driver.add_protocol(proto, None)
        self.driver.set_algorithm(proto, self.driver.ROUNDROBIN)
        self.assertIn(proto, self.driver._config)
        self.assertIn('algorithm', self.driver._config[proto])
        self.assertEqual(self.driver._config[proto]['algorithm'], 'roundrobin')
        self.driver.set_algorithm(proto, self.driver.LEASTCONN)
        self.assertEqual(self.driver._config[proto]['algorithm'], 'leastconn')
        e = self.assertRaises(Exception, self.driver.set_algorithm, proto, 99)
        self.assertEqual("Invalid algorithm: http", e.message)
