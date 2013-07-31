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

    def show_stat(self, proxy_iid=-1, object_type=-1, server_id=-1):
        """
        Get and parse output from 'show status' command.

        proxy_iid
          Proxy ID (column 27 in CSV output). -1 for all.

        object_type
          Select the type of dumpable object. Values can be ORed.
             -1 - everything
              1 - backends
              2 - frontents
              4 - servers

        server_id
          Server ID (column 28 in CSV output?), or -1 for everything.
        """
        results = self._query('show stat %d %d %d'
                              % (proxy_iid, object_type, server_id))
        list_results = results.split('\n')
        return list_results

    def get_server_status(self, protocol=None):
        """
        Get status for each server for a protocol backend.
        Return a list of tuples containing server name and status.
        """

        if protocol:
            filter_string = protocol.lower() + "-servers"

        results = self.show_stat(object_type=4)  # servers only

        final_results = []
        for line in results[1:]:
            elements = line.split(',')
            if protocol and elements[0] != filter_string:
                next
            else:
                # 1 - server name, 17 - status
                # Here we look for the new server name form of "id-NNNN"
                # where NNNN is the unique node ID. The old form could
                # be "serverX", in which case we leave it alone.
                if elements[1][0:3] == "id-":
                    junk, node_id = elements[1].split('-')
                else:
                    node_id = elements[1]

                # All the way up is UP, otherwise call it DOWN
                if elements[17] != "UP":
                    elements[17] = "DOWN"

                final_results.append((node_id, elements[17]))
        return final_results
