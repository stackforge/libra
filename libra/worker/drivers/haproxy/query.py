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

import subprocess


class HAProxyQuery(object):
    """ Class used for querying the HAProxy statistics socket. """

    def __init__(self, stats_socket):
        """
        stats_socket
            Path to the HAProxy statistics socket file.
        """
        self.socket = stats_socket

    def _query(self, query):
        """
        Send the given query to the haproxy statistics socket.

        Return the output of a successful query as a string with trailing
        newlines removed, or raise an Exception if the query fails.
        """
        cmd = 'echo "%s" | /usr/bin/socat stdio %s' % \
              (query, self.socket)

        try:
            output = subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError:
            raise Exception("HAProxy '%s' query failed." % query)

        return output.rstrip()

    def show_info(self):
        """ Get and parse output from 'show info' command. """
        results = self._query('show info')
        list_results = results.split('\n')
        # TODO: Parse the results into a well defined format.
        return list_results
