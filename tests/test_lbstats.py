import unittest
from libra.common.lbstats import LBStatistics


class TestLBStatistics(unittest.TestCase):
    def setUp(self):
        self.stats = LBStatistics()

    def tearDown(self):
        pass

    def testInitValues(self):
        self.assertEquals(self.stats.bytes_out, 0)
        self.assertEquals(self.stats.bytes_in, 0)

    def testSetBytesIn(self):
        self.stats.bytes_in = 99
        self.assertEquals(self.stats.bytes_in, 99)
        with self.assertRaises(TypeError):
            self.stats.bytes_in = "NaN"

    def testSetBytesOut(self):
        self.stats.bytes_out = 100
        self.assertEquals(self.stats.bytes_out, 100)
        with self.assertRaises(TypeError):
            self.stats.bytes_out = "NaN"
