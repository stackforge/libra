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

import simplejson


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
    UNREPORTED_BYTES_FIELD = 'unreported_bytes_out'

    # LAST_* values are for values we reported back from last query
    LAST_START_FIELD = 'last_start'
    LAST_END_FIELD = 'last_end'
    LAST_BYTES_FIELD = 'last_bytes_out'

    def __init__(self, filename):
        self.filename = filename
        self._object = {}

    def _do_save(self, obj):
        with open(self.filename, "w") as fp:
            simplejson.dump(obj, fp)

    def save_unreported(self, start, end, bytes_out):
        """ Save unreported values, overwriting any existing data """
        if None in [start, end, bytes_out]:
            raise Exception('Cannot save None value')

        obj = {
            self.UNREPORTED_START_FIELD: start,
            self.UNREPORTED_END_FIELD: end,
            self.UNREPORTED_BYTES_FIELD: bytes_out
        }
        self._do_save(obj)

    def save_last_reported(self, start, end, bytes_out):
        """ Save last reported values, overwriting any existing data """
        if None in [start, end, bytes_out]:
            raise Exception('Cannot save None value')

        obj = {
            self.LAST_START_FIELD: start,
            self.LAST_END_FIELD: end,
            self.LAST_BYTES_FIELD: bytes_out
        }
        self._do_save(obj)

    def read(self):
        """ Read the current values from the file """
        with open(self.filename, "r") as fp:
            self._object = simplejson.load(fp)

    def get_unreported_start(self):
        """ Return start timestamp for unreported data """
        if self.UNREPORTED_START_FIELD in self._object:
            return self._object[self.UNREPORTED_START_FIELD]
        return None

    def get_unreported_end(self):
        """ Return end timestamp for unreported data """
        if self.UNREPORTED_END_FIELD in self._object:
            return self._object[self.UNREPORTED_END_FIELD]
        return None

    def get_unreported_bytes(self):
        """ Return unreported bytes out. None means nothing unreported. """
        if self.UNREPORTED_BYTES_FIELD in self._object:
            return self._object[self.UNREPORTED_BYTES_FIELD]
        return None

    def get_last_start(self):
        """ Return last start timestamp """
        if self.LAST_START_FIELD in self._object:
            return self._object[self.LAST_START_FIELD]
        return None

    def get_last_end(self):
        """ Return last end timestamp """
        if self.LAST_END_FIELD in self._object:
            return self._object[self.LAST_END_FIELD]
        return None

    def get_last_bytes(self):
        """ Return last reported bytes out """
        if self.LAST_BYTES_FIELD in self._object:
            return self._object[self.LAST_BYTES_FIELD]
        return None
