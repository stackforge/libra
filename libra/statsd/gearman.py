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

from libra.common.json_gearman import JSONGearmanClient


class GearJobs(object):
    def __init__(self, logger, args):
        self.logger = logger
        self.gm_client = JSONGearmanClient(args.server)

    def send_pings(self, node_list):
        list_of_jobs = []
        failed_list = []
        job_data = {"hpcs_action": "STATS"}
        for node in node_list:
            list_of_jobs.append(dict(task=str(node), data=job_data))
        submitted_pings = self.gm_client.submit_multiple_jobs(
            list_of_jobs, background=False, wait_until_complete=True,
            poll_timeout=5.0
        )
        for ping in submitted_pings:
            if ping.state == 'UNKNOWN':
                # TODO: Gearman server failed, ignoring for now
                self.logger.error('Gearman Job server fail')
                continue
            if ping.timed_out:
                # Ping timeout
                failed_list.append(ping.job.task)
                continue
            if ping.result['hpcs_response'] == 'FAIL':
                # Error returned by Gearman
                failed_list.append(ping.job.task)
                continue

        return failed_list
