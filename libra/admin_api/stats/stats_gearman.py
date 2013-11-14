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

from gearman.constants import JOB_UNKNOWN
from oslo.config import cfg
from libra.common.json_gearman import JSONGearmanClient
from libra.openstack.common import log


LOG = log.getLogger(__name__)


class GearJobs(object):
    def __init__(self):
        self.poll_timeout = cfg.CONF['admin_api']['stats_poll_timeout']
        self.poll_retry = cfg.CONF['admin_api']['stats_poll_timeout_retry']

        server_list = []
        for server in cfg.CONF['gearman']['servers']:
            host, port = server.split(':')
            server_list.append({'host': host,
                                'port': int(port),
                                'keyfile': cfg.CONF['gearman']['ssl_key'],
                                'certfile': cfg.CONF['gearman']['ssl_cert'],
                                'ca_certs': cfg.CONF['gearman']['ssl_ca'],
                                'keepalive': cfg.CONF['gearman']['keepalive'],
                                'keepcnt': cfg.CONF['gearman']['keepcnt'],
                                'keepidle': cfg.CONF['gearman']['keepidle'],
                                'keepintvl': cfg.CONF['gearman']['keepintvl']
                                })
        self.gm_client = JSONGearmanClient(server_list)

    def send_pings(self, node_list):
        # TODO: lots of duplicated code that needs cleanup
        list_of_jobs = []
        failed_list = []
        node_status = dict()
        retry_list = []
        job_data = {"hpcs_action": "PING"}
        for node in node_list:
            list_of_jobs.append(dict(task=str(node), data=job_data))
        submitted_pings = self.gm_client.submit_multiple_jobs(
            list_of_jobs, background=False, wait_until_complete=True,
            poll_timeout=self.poll_timeout
        )
        for ping in submitted_pings:
            if ping.state == JOB_UNKNOWN:
                # TODO: Gearman server failed, ignoring for now
                LOG.error('Gearman Job server fail')
                continue
            if ping.timed_out:
                # Ping timeout
                retry_list.append(ping.job.task)
                continue
            if ping.result['hpcs_response'] == 'FAIL':
                if (
                    'status' in ping.result and
                    ping.result['status'] == 'DELETED'
                ):
                    continue
                # Error returned by Gearman
                failed_list.append(ping.job.task)
                continue
            else:
                if 'nodes' in ping.result:
                    node_status[ping.job.task] = ping.result['nodes']

        list_of_jobs = []
        if len(retry_list) > 0:
            LOG.info(
                "{0} pings timed out, retrying".format(len(retry_list))
            )
            for node in retry_list:
                list_of_jobs.append(dict(task=str(node), data=job_data))
            submitted_pings = self.gm_client.submit_multiple_jobs(
                list_of_jobs, background=False, wait_until_complete=True,
                poll_timeout=self.poll_retry
            )
            for ping in submitted_pings:
                if ping.state == JOB_UNKNOWN:
                    # TODO: Gearman server failed, ignoring for now
                    LOG.error('Gearman Job server fail')
                    continue
                if ping.timed_out:
                    # Ping timeout
                    failed_list.append(ping.job.task)
                    continue
                if ping.result['hpcs_response'] == 'FAIL':
                    if (
                        'status' in ping.result and
                        ping.result['status'] == 'DELETED'
                    ):
                        continue
                    # Error returned by Gearman
                    failed_list.append(ping.job.task)
                    continue
                else:
                    if 'nodes' in ping.result:
                        node_status[ping.job.task] = ping.result['nodes']

        return failed_list, node_status

    def offline_check(self, node_list):
        list_of_jobs = []
        failed_list = []
        job_data = {"hpcs_action": "DIAGNOSTICS"}
        for node in node_list:
            list_of_jobs.append(dict(task=str(node), data=job_data))
        submitted_pings = self.gm_client.submit_multiple_jobs(
            list_of_jobs, background=False, wait_until_complete=True,
            poll_timeout=self.poll_timeout
        )
        for ping in submitted_pings:
            if ping.state == JOB_UNKNOWN:
                LOG.error(
                    "Gearman Job server failed during OFFLINE check of {0}".
                    format(ping.job.task)
                )
            elif ping.timed_out:
                failed_list.append(ping.job.task)
            elif ping.result['network'] == 'FAIL':
                failed_list.append(ping.job.task)
            else:
                gearman_count = 0
                gearman_fail = 0
                for gearman_test in ping.result['gearman']:
                    gearman_count += 1
                    if gearman_test['status'] == 'FAIL':
                        gearman_fail += 1
                # Need 2/3rds gearman up
                max_fail_count = gearman_count / 3
                if gearman_fail > max_fail_count:
                    failed_list.append(ping.job.task)
        return failed_list

    def get_stats(self, node_list):
        # TODO: lots of duplicated code that needs cleanup
        list_of_jobs = []
        failed_list = []
        retry_list = []
        results = {}
        job_data = {"hpcs_action": "STATS"}
        for node in node_list:
            list_of_jobs.append(dict(task=str(node), data=job_data))
        submitted_stats = self.gm_client.submit_multiple_jobs(
            list_of_jobs, background=False, wait_until_complete=True,
            poll_timeout=self.poll_timeout
        )
        for stats in submitted_stats:
            if stats.state == JOB_UNKNOWN:
                # TODO: Gearman server failed, ignoring for now
                retry_list.append(stats.job.task)
            if stats.timed_out:
                # Timeout
                retry_list.append(stats.job.task)
            if stats.result['hpcs_response'] == 'FAIL':
                # Error returned by Gearman
                failed_list.append(stats.job.task)
            else:
                #Success
                results[stats.job.task] = stats.result

        list_of_jobs = []
        if len(retry_list) > 0:
            LOG.info(
                "{0} stats timed out, retrying".format(len(retry_list))
            )
            for node in retry_list:
                list_of_jobs.append(dict(task=str(node), data=job_data))
            submitted_stats = self.gm_client.submit_multiple_jobs(
                list_of_jobs, background=False, wait_until_complete=True,
                poll_timeout=self.poll_retry
            )
            for stats in submitted_stats:
                if stats.state == JOB_UNKNOWN:
                    # TODO: Gearman server failed, ignoring for now
                    LOG.error(
                        "Gearman Job server failed during STATS check of {0}".
                        format(stats.job.task)
                    )
                    failed_list.append(stats.job.task)
                if stats.timed_out:
                    # Timeout
                    failed_list.append(stats.job.task)
                if stats.result['hpcs_response'] == 'FAIL':
                    # Error returned by Gearman
                    failed_list.append(stats.job.task)
                    continue
                else:
                    #Success
                    results[stats.job.task] = stats.result

        return failed_list, results
