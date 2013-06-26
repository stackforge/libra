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
from libra.common.json_gearman import JSONGearmanClient


class GearJobs(object):
    def __init__(self, logger, args):
        self.logger = logger
        self.poll_timeout = args.poll_timeout
        self.poll_timeout_retry = args.poll_timeout_retry

        if all([args.gearman_ssl_ca, args.gearman_ssl_cert,
                args.gearman_ssl_key]):
            # Use SSL connections to each Gearman job server.
            ssl_server_list = []
            for server in args.server:
                host, port = server.split(':')
                ssl_server_list.append({'host': host,
                                        'port': port,
                                        'keyfile': args.gearman_ssl_key,
                                        'certfile': args.gearman_ssl_cert,
                                        'ca_certs': args.gearman_ssl_ca})
            self.gm_client = JSONGearmanClient(ssl_server_list)
        else:
            self.gm_client = JSONGearmanClient(args.server)

    def send_pings(self, node_list):
        # TODO: lots of duplicated code that needs cleanup
        list_of_jobs = []
        failed_list = []
        retry_list = []
        job_data = {"hpcs_action": "STATS"}
        for node in node_list:
            list_of_jobs.append(dict(task=str(node), data=job_data))
        submitted_pings = self.gm_client.submit_multiple_jobs(
            list_of_jobs, background=False, wait_until_complete=True,
            poll_timeout=self.poll_timeout
        )
        for ping in submitted_pings:
            if ping.state == JOB_UNKNOWN:
                # TODO: Gearman server failed, ignoring for now
                self.logger.error('Gearman Job server fail')
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

        list_of_jobs = []
        if len(retry_list) > 0:
            self.logger.info(
                "{0} pings timed out, retrying".format(len(retry_list))
            )
            for node in retry_list:
                list_of_jobs.append(dict(task=str(node), data=job_data))
            submitted_pings = self.gm_client.submit_multiple_jobs(
                list_of_jobs, background=False, wait_until_complete=True,
                poll_timeout=self.poll_timeout_retry
            )
            for ping in submitted_pings:
                if ping.state == JOB_UNKNOWN:
                    # TODO: Gearman server failed, ignoring for now
                    self.logger.error('Gearman Job server fail')
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

        return failed_list

    def send_repair(self, node_list):
        list_of_jobs = []
        repaired_list = []
        job_data = {"hpcs_action": "STATS"}
        for node in node_list:
            list_of_jobs.append(dict(task=str(node), data=job_data))
        submitted_pings = self.gm_client.submit_multiple_jobs(
            list_of_jobs, background=False, wait_until_complete=True,
            poll_timeout=self.poll_timeout
        )
        for ping in submitted_pings:
            if ping.state == JOB_UNKNOWN:
                # TODO: Gearman server failed, ignoring for now
                self.logger.error('Gearman Job server fail')
                continue
            elif ping.timed_out:
                # Ping timeout
                continue
            elif ping.result['hpcs_response'] == 'FAIL':
                # Error returned by Gearman
                continue
            else:
                repaired_list.append(ping.job.task)

        return repaired_list
