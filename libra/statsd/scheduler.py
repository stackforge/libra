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

import threading

from libra.statsd.admin_api import AdminAPI
from libra.statsd.gearman import GearJobs


class Sched(object):
    def __init__(self, logger, args):
        self.logger = logger
        self.args = args
        self.rlock = threading.RLock()
        self.ping_timer = None

    def start(self):
        self.ping_lbs()

    def ping_lbs(self):
        with self.rlock:
            try:
                pings, failed = self._exec_ping()
            except Exception:
                self.logger.exception('Uncaught exception during LB ping')
        # Need to restart timer after every ping cycle
        self.logger.info('{pings} loadbalancers pinged, {failed} failed'
                         .format(pings=pings, failed=failed))
        self.start_ping_sched()

    def _exec_ping(self):
        pings = 0
        failed = 0
        node_list = []
        self.logger.info('Running ping check')
        api = AdminAPI(self.args.api_server, self.logger)
        if api.is_online():
            lb_list = api.get_ping_list()
            pings = len(lb_list)
            for lb in lb_list:
                node_list.append(lb['name'])
            gearman = GearJobs(self.logger, self.args)
            failed_nodes = gearman.send_pings(node_list)
            failed = len(failed_nodes)
            if failed > 0:
                self._send_fails(lb_list, failed_nodes)
        else:
            self.logger.error('No working API server found')
            return (0, 0)

        return pings, failed

    def _send_fails(self):
        # TODO: send failure messages to plugins here
        pass

    def start_ping_sched(self):
        self.logger.info('LB ping check timer sleeping for {secs} seconds'
                         .format(secs=self.args.ping_interval))
        self.ping_timer = threading.Timer(self.args.ping_interval,
                                          self.ping_lbs, ())
        self.ping_timer.start()
