import unittest
from libra.worker.drivers.haproxy.driver import HAProxyDriver


class TestHAProxyDriver(unittest.TestCase):
    def setUp(self):
        self.driver = HAProxyDriver()

    def tearDown(self):
        pass

    def testBind(self):
        """ Test the HAProxy bind() method """
        bind_address = '9.8.7.6'
        bind_port = 9999
        self.driver.bind(bind_address, bind_port)
        self.assertEqual(self.driver._config['bind_address'], bind_address)
        self.assertEqual(self.driver._config['bind_port'], bind_port)

    def testAddServer(self):
        """ Test the HAProxy add_server() method """
        self.driver.add_server('1.2.3.4', 7777)
        self.driver.add_server('5.6.7.8', 8888)
        self.assertIn('servers', self.driver._config)
        servers = self.driver._config['servers']
        self.assertEqual(len(servers), 2)
        self.assertEqual(servers[0], ('1.2.3.4', 7777))
        self.assertEqual(servers[1], ('5.6.7.8', 8888))
