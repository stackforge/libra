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
from libra.worker.drivers.haproxy.stats import StatisticsManager


class TestStatisticsManager(TestCase):

    def setUp(self):
        super(TestStatisticsManager, self).setUp()
        self.tmpfile = tempfile.gettempdir() + "/tstLibraTestStatsMgr.tmp"
        self.mgr = StatisticsManager(self.tmpfile)

    def tearDown(self):
        if os.path.exists(self.tmpfile):
            os.remove(self.tmpfile)
        super(TestStatisticsManager, self).tearDown()

    def testReadNoStatsFile(self):
        self.mgr.read()
        self.assertEquals(self.mgr.get_last_start(), None)
        self.assertEquals(self.mgr.get_last_end(), None)
        self.assertEquals(self.mgr.get_last_tcp_bytes(), 0)
        self.assertEquals(self.mgr.get_last_http_bytes(), 0)
        self.assertEquals(self.mgr.get_unreported_start(), None)
        self.assertEquals(self.mgr.get_unreported_end(), None)
        self.assertEquals(self.mgr.get_unreported_tcp_bytes(), 0)
        self.assertEquals(self.mgr.get_unreported_http_bytes(), 0)

    def testSaveLastQueried(self):
        start_ts = datetime.datetime(2013, 1, 31, 12, 10, 30, 123456)
        end_ts = start_ts + datetime.timedelta(minutes=5)
        tcp_bytes = 1024
        http_bytes = 2048
        self.mgr.save_last_queried(start_ts, end_ts, tcp_bytes, http_bytes)
        self.mgr.read()
        self.assertEquals(self.mgr.get_last_start(), start_ts)
        self.assertEquals(self.mgr.get_last_end(), end_ts)
        self.assertEquals(self.mgr.get_last_tcp_bytes(), tcp_bytes)
        self.assertEquals(self.mgr.get_last_http_bytes(), http_bytes)

    def testSaveUnreported(self):
        start_ts = datetime.datetime(2013, 1, 31, 12, 10, 30, 123456)
        end_ts = start_ts + datetime.timedelta(minutes=5)
        tcp_bytes = 1024
        http_bytes = 2048
        self.mgr.save_unreported(start_ts, end_ts, tcp_bytes, http_bytes)
        self.mgr.read()
        self.assertEquals(self.mgr.get_unreported_start(), start_ts)
        self.assertEquals(self.mgr.get_unreported_end(), end_ts)
        self.assertEquals(self.mgr.get_unreported_tcp_bytes(), tcp_bytes)
        self.assertEquals(self.mgr.get_unreported_http_bytes(), http_bytes)
