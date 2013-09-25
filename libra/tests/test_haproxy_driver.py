import testtools
from libra.worker.drivers.haproxy.driver import HAProxyDriver


class TestHAProxyDriver(testtools.TestCase):
    def setUp(self):
        super(TestHAProxyDriver, self).setUp()
        self.driver = HAProxyDriver('libra.tests.mock_objects.FakeOSServices',
                                    None, None)

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

        proto = 'galera'
        self.driver.add_protocol(proto, 3306)
        self.assertIn(proto, self.driver._config)
        self.assertEqual(self.driver._config[proto]['bind_address'], '0.0.0.0')
        self.assertEqual(self.driver._config[proto]['bind_port'], 3306)

        proto = 'tnetennba'
        e = self.assertRaises(Exception, self.driver.add_protocol, proto, 99)
        self.assertEqual("Unsupported protocol: %s" % proto, e.message)

    def testAddGaleraRequiresPort(self):
        e = self.assertRaises(Exception, self.driver.add_protocol, 'galera', None)
        self.assertEqual("Port is required for this protocol.", e.message)

    def testAddTCPRequiresPort(self):
        e = self.assertRaises(Exception, self.driver.add_protocol, 'tcp', None)
        self.assertEqual("Port is required for this protocol.", e.message)

    def testAddServer(self):
        """ Test the HAProxy add_server() method """
        proto = 'http'
        self.driver.add_protocol(proto, None)
        self.driver.add_server(proto, 100, '1.2.3.4', 7777)
        self.driver.add_server(proto, 101, '5.6.7.8', 8888, 1, True)
        self.driver.add_server(proto, 102, '2.3.4.5', 9999,
                               weight=2, backup=True)
        self.assertIn(proto, self.driver._config)
        self.assertIn('servers', self.driver._config[proto])
        servers = self.driver._config[proto]['servers']
        self.assertEqual(len(servers), 3)
        self.assertEqual(servers[0], (100, '1.2.3.4', 7777, 1, False))
        self.assertEqual(servers[1], (101, '5.6.7.8', 8888, 1, True))
        self.assertEqual(servers[2], (102, '2.3.4.5', 9999, 2, True))

    def testAddServerMultipleGaleraPrimaries(self):
        proto = 'galera'
        self.driver.add_protocol(proto, 33306)
        self.driver.add_server(proto, 100, '1.2.3.4', 3306, backup=False)
        self.driver.add_server(proto, 101, '1.2.3.5', 3306, backup=True)
        e = self.assertRaises(Exception, self.driver.add_server,
                              proto, 101, '1.2.3.6', 3306, backup=False)
        self.assertEqual(
            "Galera protocol does not accept more than one non-backup node",
            e.message)

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

    def testServerWeightInt(self):
        """ Test setting integer server weights """
        proto = 'http'
        self.driver.add_protocol(proto, None)
        self.driver.add_server(proto, 100, '1.2.3.4', 7777, 10)
        servers = self.driver._config[proto]['servers']
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0], (100, '1.2.3.4', 7777, 10, False))

    def testServerWeightStr(self):
        """ Test setting string server weights """
        proto = 'http'
        self.driver.add_protocol(proto, None)
        self.driver.add_server(proto, 100, '1.2.3.4', 7777, "20")
        servers = self.driver._config[proto]['servers']
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0], (100, '1.2.3.4', 7777, 20, False))

    def testServerWeightInvalid(self):
        """ Test setting string server weights """
        proto = 'http'
        self.driver.add_protocol(proto, None)
        e = self.assertRaises(Exception, self.driver.add_server,
                              proto, 100, '1.2.3.4', 7777, 257)
        self.assertEqual("Server 'weight' 257 exceeds max of 256", e.message)

        e = self.assertRaises(Exception, self.driver.add_server,
                              proto, 100, '1.2.3.4', 7777, "abc")
        self.assertEqual("Non-integer 'weight' value: 'abc'", e.message)

    def testArchive(self):
        """ Test the HAProxy archive() method """

        # Test an invalid archive method
        method = 'invalid'
        e = self.assertRaises(Exception, self.driver.archive, method, None)
        self.assertEqual(
            "Driver does not support archive method '%s'" % method,
            e.message)
