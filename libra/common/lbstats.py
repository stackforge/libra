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
