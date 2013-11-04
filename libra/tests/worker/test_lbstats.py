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
from libra.tests.base import TestCase
from libra.common.lbstats import LBStatistics


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
