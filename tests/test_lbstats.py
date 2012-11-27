import datetime
import unittest
from libra.common.lbstats import LBStatistics


class TestLBStatistics(unittest.TestCase):
    def setUp(self):
        self.stats = LBStatistics()

    def tearDown(self):
        pass

    def testInitValues(self):
        now = datetime.datetime.utcnow()
        ts = self.stats.utc_timestamp
        self.assertEquals(ts.year, now.year)
        self.assertEquals(ts.month, now.month)
        self.assertEquals(ts.day, now.day)
        self.assertEquals(ts.hour, now.hour)
        self.assertEquals(self.stats.bytes_out, 0L)
        self.assertEquals(self.stats.bytes_in, 0L)

    def testSetBytesIn(self):
        self.stats.bytes_in = 99L
        self.assertEquals(self.stats.bytes_in, 99L)
        with self.assertRaises(TypeError):
            self.stats.bytes_in = "NaN"

    def testSetBytesOut(self):
        self.stats.bytes_out = 100L
        self.assertEquals(self.stats.bytes_out, 100L)
        with self.assertRaises(TypeError):
            self.stats.bytes_out = "NaN"

    def testSetUTCTimestamp(self):
        ts = datetime.datetime.utcnow()
        self.stats.utc_timestamp = ts
        self.assertEquals(self.stats.utc_timestamp, ts)
        with self.assertRaises(TypeError):
            self.stats.utc_timestamp = "2012-01-01 12:00:00"