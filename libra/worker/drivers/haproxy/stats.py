# Copyright 2012 Hewlett-Packard Development Company, L.P.
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
import simplejson


class StatisticsManager(object):
    """
    Class for managing statistics storage.

    Since HAProxy statistics are reset whenever the haproxy process is
    restarted, we need a reliable way of maintaining these values across
    restarts. This class attempts to manage the storage of the values.

    There are two types of statistics we record:

      * Unreported stats
        These are stats that we need to save because a state change in
        the HAProxy service is causing it to restart. Since HAProxy stores
        its stats in memory, they would otherwise be lost. We save them here
        for consideration in the next STATS request.

      * Last queried stats
        These are total bytes out as reported from HAProxy the last time we
        queried it for that information.
    """

    # UNREPORTED_* values are for unreported statistics due to a restart
    UNREPORTED_START_FIELD = 'unreported_start'
    UNREPORTED_END_FIELD = 'unreported_end'
    UNREPORTED_TCP_BYTES_FIELD = 'unreported_tcp_bytes_out'
    UNREPORTED_HTTP_BYTES_FIELD = 'unreported_http_bytes_out'

    # LAST_* values are for values from our last query
    LAST_START_FIELD = 'last_start'
    LAST_END_FIELD = 'last_end'
    LAST_TCP_BYTES_FIELD = 'last_tcp_bytes_out'
    LAST_HTTP_BYTES_FIELD = 'last_http_bytes_out'

    def __init__(self, filename):
        self.filename = filename
        self._object = {}

    def _do_save(self, obj):
        with open(self.filename, "w") as fp:
            simplejson.dump(obj, fp)

    def _format_timestamp(self, ts):
        return datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S.%f')

    def save_unreported(self, start, end, tcp_bytes_out=0, http_bytes_out=0):
        """ Save unreported values, overwriting any existing data """
        if None in [start, end]:
            raise Exception('Cannot save None value')

        if type(start) != datetime.datetime or type(end) != datetime.datetime:
            raise TypeError('Timestamps must be datetime.datetime')

        obj = {
            self.UNREPORTED_START_FIELD: str(start),
            self.UNREPORTED_END_FIELD: str(end),
            self.UNREPORTED_TCP_BYTES_FIELD: tcp_bytes_out,
            self.UNREPORTED_HTTP_BYTES_FIELD: http_bytes_out
        }
        self._do_save(obj)

    def save_last_queried(self, start, end,
                          tcp_bytes_out=0, http_bytes_out=0):
        """
        Save last queried values, overwriting any existing data.

        tcp_bytes_out
            TOTAL bytes out of the TCP backend, as reported by haproxy.

        http_bytes_out
            TOTAL bytes out of the HTTP backend, as reported by haproxy.
        """
        if None in [start, end]:
            raise Exception('Cannot save None value')

        if type(start) != datetime.datetime or type(end) != datetime.datetime:
            raise TypeError('Timestamps must be datetime.datetime')

        obj = {
            self.LAST_START_FIELD: str(start),
            self.LAST_END_FIELD: str(end),
            self.LAST_TCP_BYTES_FIELD: tcp_bytes_out,
            self.LAST_HTTP_BYTES_FIELD: http_bytes_out
        }
        self._do_save(obj)

    def read(self):
        """ Read the current values from the file """
        if not os.path.exists(self.filename):
            return
        with open(self.filename, "r") as fp:
            self._object = simplejson.load(fp)

    def get_unreported_start(self):
        """ Return start timestamp for unreported data as datetime object """
        if self.UNREPORTED_START_FIELD in self._object:
            return self._format_timestamp(
                self._object[self.UNREPORTED_START_FIELD]
            )
        return None

    def get_unreported_end(self):
        """ Return end timestamp for unreported data as datetime object """
        if self.UNREPORTED_END_FIELD in self._object:
            return self._format_timestamp(
                self._object[self.UNREPORTED_END_FIELD]
            )
        return None

    def get_unreported_tcp_bytes(self):
        """ Return TCP unreported bytes out """
        if self.UNREPORTED_TCP_BYTES_FIELD in self._object:
            return int(self._object[self.UNREPORTED_TCP_BYTES_FIELD])
        return 0

    def get_unreported_http_bytes(self):
        """ Return HTTP unreported bytes out """
        if self.UNREPORTED_HTTP_BYTES_FIELD in self._object:
            return int(self._object[self.UNREPORTED_HTTP_BYTES_FIELD])
        return 0

    def get_last_start(self):
        """ Return last start timestamp as datetime object """
        if self.LAST_START_FIELD in self._object:
            return self._format_timestamp(
                self._object[self.LAST_START_FIELD]
            )
        return None

    def get_last_end(self):
        """ Return last end timestamp as datetime object """
        if self.LAST_END_FIELD in self._object:
            return self._format_timestamp(
                self._object[self.LAST_END_FIELD]
            )
        return None

    def get_last_tcp_bytes(self):
        """ Return TCP last reported bytes out """
        if self.LAST_TCP_BYTES_FIELD in self._object:
            return int(self._object[self.LAST_TCP_BYTES_FIELD])
        return 0

    def get_last_http_bytes(self):
        """ Return HTTP last reported bytes out """
        if self.LAST_HTTP_BYTES_FIELD in self._object:
            return int(self._object[self.LAST_HTTP_BYTES_FIELD])
        return 0
