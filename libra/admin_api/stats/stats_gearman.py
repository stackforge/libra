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

from oslo.config import cfg
from libra.openstack.common import log
from libra import gear #TODO
from libra.common.json_gearman import JsonJob
import time


LOG = log.getLogger(__name__)


class GearJobs(object):
    class DisconnectClient(gear.Client):
        def handleDisconnect(self, job):
            job.disconnect = True

    class DisconnectJob(JsonJob):
        def __init__(self, name, msg, unique=None):
            super(GearJobs.DisconnectJob, self).__init__(name, msg, unique)
            self.disconnect = False

    def __init__(self):
        self.poll_timeout = cfg.CONF['admin_api']['stats_poll_timeout']
        self.poll_retry = cfg.CONF['admin_api']['stats_poll_timeout_retry']

        self.gm_client = gear.Client("stats")
        self.gm_client.log = LOG
        for server in cfg.CONF['gearman']['servers']:
            host, port = server.split(':')
            self.gm_client.addServer(host, port,
                                     cfg.CONF['gearman']['ssl_key'],
                                     cfg.CONF['gearman']['ssl_cert'],
                                     cfg.CONF['gearman']['ssl_ca'])

    def _all_complete(self, jobs):
        for job in jobs:
            if not (job.complete or job.disconnect):
                return False
        return True

    def _wait(self, pings):
        poll_count = 0
        while not self._all_complete(pings) and poll_count < self.poll_retry:
            # wait for jobs
            time.sleep(self.poll_timeout)
            poll_count += 1

    def send_pings(self, node_list):
        failed_list = []
        node_status = dict()
        retry_list = []
        submitted_pings = []
        # The message name is STATS for historical reasons. Real
        # data statistics are gathered with METRICS messages.
        job_data = {"hpcs_action": "STATS"}
        for node in node_list:
            job = GearJobs.DisconnectJob(str(node), job_data)
            self.gm_client.submitJob(job)
            submitted_pings.append(job)

        self._wait(submitted_pings)

        for ping in submitted_pings:
            if ping.disconnect:
                # TODO: Gearman server failed, ignoring for now
                LOG.error('Gearman Job server fail')
                continue
            if not ping.complete:
                # Ping timeout
                retry_list.append(ping)
                continue
            if ping.msg['hpcs_response'] == 'FAIL':
                if (
                    'status' in ping.result and
                    ping.msg['status'] == 'DELETED'
                ):
                    continue
                # Error returned by Gearman
                failed_list.append(ping)
                continue
            else:
                if 'nodes' in ping.msg:
                    node_status[ping.name] = ping.msg['nodes']

        submitted_pings = []
        if len(retry_list) > 0:
            LOG.info(
                "{0} pings timed out, retrying".format(len(retry_list))
            )
            for node in retry_list:
                job = GearJobs.DisconnectJob(node.name, node.msg)
                self.gm_client.submitJob(job)
                submitted_pings.append(job)

            self._wait(submitted_pings)

            for ping in submitted_pings:
                if ping.disconnect:
                    # TODO: Gearman server failed, ignoring for now
                    LOG.error('Gearman Job server fail')
                    continue
                if not ping.complete:
                    # Ping timeout
                    failed_list.append(ping.name)
                    continue
                if ping.msg['hpcs_response'] == 'FAIL':
                    if (
                        'status' in ping.msg and
                        ping.msg['status'] == 'DELETED'
                    ):
                        continue
                    # Error returned by Gearman
                    failed_list.append(ping.name)
                    continue
                else:
                    if 'nodes' in ping.result:
                        node_status[ping.name] = ping.msg['nodes']

        return failed_list, node_status

    def offline_check(self, node_list):
        failed_list = []
        submitted_pings = []
        job_data = {"hpcs_action": "DIAGNOSTICS"}
        for node in node_list:
            job = GearJobs.DisconnectJob(str(node), job_data)
            self.gm_client.submitJob(job)
            submitted_pings.append(job)

        self._wait(submitted_pings)

        for ping in submitted_pings:
            if ping.disconnect:
                LOG.error(
                    "Gearman Job server failed during OFFLINE check of {0}".
                    format(ping.job.task)
                )
            elif not ping.complete:
                failed_list.append(ping.name)
            elif ping.msg['network'] == 'FAIL':
                failed_list.append(ping.name)
            else:
                gearman_count = 0
                gearman_fail = 0
                for gearman_test in ping.msg['gearman']:
                    gearman_count += 1
                    if gearman_test['status'] == 'FAIL':
                        gearman_fail += 1
                # Need 2/3rds gearman up
                max_fail_count = gearman_count / 3
                if gearman_fail > max_fail_count:
                    failed_list.append(ping.name)
        return failed_list

    def get_discover(self, name):
        # Used in the v2 devices controller
        job_data = {"hpcs_action": "DISCOVER"}
        job = GearJobs.DisconnectJob(str(name), job_data)
        self.gm_client.submitJob(job, gear.PRECEDENCE_HIGH)

        poll_count = 0
        while not job.complete and not job.disconnect \
                and poll_count < self.poll_retry:
            # wait for jobs TODO make sure right unit/value
            time.sleep(self.poll_timeout)
            poll_count += 1

        if not job.complete:
            return None

        if job.result['hpcs_response'] == 'FAIL':
            # Fail response is a fail
            return None

        return job.result

    def get_stats(self, node_list):
        # TODO: lots of duplicated code that needs cleanup
        failed_list = []
        retry_list = []
        submitted_stats = []
        results = {}
        job_data = {"hpcs_action": "METRICS"}
        for node in node_list:
            job = GearJobs.DisconnectJob(str(node), job_data)
            self.gm_client.submitJob(job)
            submitted_stats.append(job)

        self._wait(submitted_stats)

        for stats in submitted_stats:
            if stats.disconnect:
                # TODO: Gearman server failed, ignoring for now
                retry_list.append(stats)
            elif not stats.complete:
                # Timeout
                retry_list.append(stats)
            elif stats.msg['hpcs_response'] == 'FAIL':
                # Error returned by Gearman
                failed_list.append(stats.name)
            else:
                # Success
                results[stats.name] = stats.msg

        submitted_stats = []
        if len(retry_list) > 0:
            LOG.info(
                "{0} Statistics gathering timed out, retrying".
                format(len(retry_list))
            )
            for node in retry_list:
                job = GearJobs.DisconnectJob(node.name, node.msg)
                self.gm_client.submitJob(job)
                submitted_stats.append(job)

            self._wait(submitted_stats)

            for stats in submitted_stats:
                if stats.disconnect:
                    # TODO: Gearman server failed, ignoring for now
                    LOG.error(
                        "Gearman Job server failed gathering statistics "
                        "on {0}".format(stats.job.task)
                    )
                    failed_list.append(stats.name)
                elif not stats.complete:
                    # Timeout
                    failed_list.append(stats.name)
                elif stats.msg['hpcs_response'] == 'FAIL':
                    # Error returned by Gearman
                    failed_list.append(stats.name)
                else:
                    # Success
                    results[stats.name] = stats.msg

        return failed_list, results
