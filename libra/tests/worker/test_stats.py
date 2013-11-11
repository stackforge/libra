# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import datetime
import os.path
import tempfile

from libra.tests.base import TestCase
from libra.worker.drivers.haproxy.stats import LBStatistics
from libra.worker.drivers.haproxy.stats import StatisticsManager


class TestLBStatistics(TestCase):
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
        e = self.assertRaises(TypeError, setattr, self.stats,
                              'bytes_in', "NaN")
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


class TestStatisticsManager(TestCase):

    def setUp(self):
        super(TestStatisticsManager, self).setUp()
        self.tmpfile = tempfile.gettempdir() + "/tstLibraTestStatsMgr.tmp"
        self.mgr = StatisticsManager(self.tmpfile)

    def tearDown(self):
        if os.path.exists(self.tmpfile):
            os.remove(self.tmpfile)
        super(TestStatisticsManager, self).tearDown()

    def testSaveLastReported(self):
        start_ts = datetime.datetime(2013, 1, 31, 12, 10, 30)
        end_ts = start_ts + datetime.timedelta(minutes=5)
        bytes_out = 1024
        self.mgr.save_last_reported(str(start_ts), str(end_ts), bytes_out)
        self.mgr.read()
        self.assertEquals(self.mgr.get_last_start(), str(start_ts))
        self.assertEquals(self.mgr.get_last_end(), str(end_ts))
        self.assertEquals(self.mgr.get_last_bytes(), bytes_out)

    def testSaveUnreported(self):
        start_ts = datetime.datetime(2013, 1, 31, 12, 10, 30)
        end_ts = start_ts + datetime.timedelta(minutes=5)
        bytes_out = 1024
        self.mgr.save_unreported(str(start_ts), str(end_ts), bytes_out)
        self.mgr.read()
        self.assertEquals(self.mgr.get_unreported_start(), str(start_ts))
        self.assertEquals(self.mgr.get_unreported_end(), str(end_ts))
        self.assertEquals(self.mgr.get_unreported_bytes(), bytes_out)
