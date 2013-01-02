import datetime
import testtools
from libra.common.lbstats import LBStatistics


class TestLBStatistics(testtools.TestCase):
    def setUp(self):
        super(TestLBStatistics, self).setUp()
        self.stats = LBStatistics()

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
        e = self.assertRaises(TypeError, setattr, self.stats, 'bytes_in', "NaN")
        self.assertEqual("Must be a long integer: 'NaN'", e.message)

    def testSetBytesOut(self):
        self.stats.bytes_out = 100L
        self.assertEquals(self.stats.bytes_out, 100L)
        e = self.assertRaises(TypeError, setattr, self.stats,
                              'bytes_out', "NaN")
        self.assertEqual("Must be a long integer: 'NaN'", e.message)

    def testSetUTCTimestamp(self):
        ts = datetime.datetime.utcnow()
        self.stats.utc_timestamp = ts
        self.assertEquals(self.stats.utc_timestamp, ts)
        e = self.assertRaises(TypeError, setattr, self.stats,
                              'utc_timestamp', "NaN")
        self.assertEqual("Must be a datetime.datetime: 'NaN'", e.message)
