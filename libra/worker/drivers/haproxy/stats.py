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


class LBStatistics(object):
    """ Load balancer statistics class. """

    def __init__(self):
        self.stats = {}
        self.bytes_out = 0L
        self.bytes_in = 0L
        self.nodes = dict()
        self.utc_timestamp = datetime.datetime.utcnow()

    @property
    def bytes_out(self):
        return self.stats['bytes_out']

    @bytes_out.setter
    def bytes_out(self, value):
        if not isinstance(value, long):
            raise TypeError("Must be a long integer: '%s'" % value)
        self.stats['bytes_out'] = value

    @property
    def bytes_in(self):
        return self.stats['bytes_in']

    @bytes_in.setter
    def bytes_in(self, value):
        if not isinstance(value, long):
            raise TypeError("Must be a long integer: '%s'" % value)
        self.stats['bytes_in'] = value

    @property
    def utc_timestamp(self):
        """ UTC timestamp for when these statistics are generated. """
        return self._utc_ts

    @utc_timestamp.setter
    def utc_timestamp(self, value):
        if not isinstance(value, datetime.datetime):
            raise TypeError("Must be a datetime.datetime: '%s'" % value)
        self._utc_ts = value

    def add_node_status(self, node, status):
        self.nodes[node] = status

    def node_status_map(self):
        """ Return a dictionary, indexed by node ID, of the node status """
        return self.nodes


class StatisticsManager(object):
    """
    Class for managing statistics storage.

    There are two types of statistics we record:

      * Unreported stats
        These are stats that we need to save because a state change in
        the HAProxy service is causing it to restart. Since HAProxy stores
        its stats in memory, they would otherwise be lost. We save them here
        for consideration in the next STATS request.

      * Last reported stats
        These are stats that we reported as a response to the previous STATS
        request. We use them to calculate differences in bytes output since
        HAProxy only knows about cumulative usage information.
    """

    # UNREPORTED_* values are for unreported statistics due to a restart
    UNREPORTED_START_FIELD = 'unreported_start'
    UNREPORTED_END_FIELD = 'unreported_end'
    TCP_UNREPORTED_BYTES_FIELD = 'tcp_unreported_bytes_out'
    HTTP_UNREPORTED_BYTES_FIELD = 'http_unreported_bytes_out'

    # LAST_* values are for values we reported back from last query
    LAST_START_FIELD = 'last_start'
    LAST_END_FIELD = 'last_end'
    TCP_LAST_BYTES_FIELD = 'tcp_last_bytes_out'
    HTTP_LAST_BYTES_FIELD = 'http_last_bytes_out'

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
            self.TCP_UNREPORTED_BYTES_FIELD: tcp_bytes_out,
            self.HTTP_UNREPORTED_BYTES_FIELD: http_bytes_out
        }
        self._do_save(obj)

    def save_last_reported(self, start, end,
                           tcp_bytes_out=0, http_bytes_out=0):
        """ Save last reported values, overwriting any existing data """
        if None in [start, end]:
            raise Exception('Cannot save None value')

        if type(start) != datetime.datetime or type(end) != datetime.datetime:
            raise TypeError('Timestamps must be datetime.datetime')

        obj = {
            self.LAST_START_FIELD: str(start),
            self.LAST_END_FIELD: str(end),
            self.TCP_LAST_BYTES_FIELD: tcp_bytes_out,
            self.HTTP_LAST_BYTES_FIELD: http_bytes_out
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

    def get_tcp_unreported_bytes(self):
        """ Return TCP unreported bytes out """
        if self.TCP_UNREPORTED_BYTES_FIELD in self._object:
            return int(self._object[self.TCP_UNREPORTED_BYTES_FIELD])
        return 0

    def get_http_unreported_bytes(self):
        """ Return HTTP unreported bytes out """
        if self.HTTP_UNREPORTED_BYTES_FIELD in self._object:
            return int(self._object[self.HTTP_UNREPORTED_BYTES_FIELD])
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

    def get_tcp_last_bytes(self):
        """ Return TCP last reported bytes out """
        if self.TCP_LAST_BYTES_FIELD in self._object:
            return int(self._object[self.TCP_LAST_BYTES_FIELD])
        return 0

    def get_http_last_bytes(self):
        """ Return HTTP last reported bytes out """
        if self.HTTP_LAST_BYTES_FIELD in self._object:
            return int(self._object[self.HTTP_LAST_BYTES_FIELD])
        return 0
