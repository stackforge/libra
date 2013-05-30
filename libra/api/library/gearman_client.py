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

import eventlet
eventlet.monkey_patch()
import logging
from libra.common.json_gearman import JSONGearmanClient
from libra.api.model.lbaas import LoadBalancer, session
from pecan import conf


gearman_client = JSONGearmanClient(conf.gearman.server)

gearman_workers = [
    'UPDATE',  # Create/Update a Load Balancer.
    'SUSPEND',  # Suspend a Load Balancer.
    'ENABLE',  # Enable a suspended Load Balancer.
    'DELETE',  # Delete a Load Balancer.
    'DISCOVER',  # Return service discovery information.
    'ARCHIVE',  # Archive LB log files.
    'STATS'  # Get load balancer statistics.
]


def submit_job(job_type, host, data, lbid):
    logger = logging.getLogger(__name__)
    eventlet.spawn_n(client_job, logger, job_type, host, data, lbid)


def client_job(logger, job_type, host, data, lbid):
    client = GearmanClientThread(logger, host, lbid)
    if job_type == 'UPDATE':
        client.send_update(data)


class GearmanClientThread(object):
    def __init__(self, logger, host, lbid):
        self.logger = logger
        self.host = host
        self.lbid = lbid
        self.gearman_client = JSONGearmanClient(conf.gearman.server)

    def send_update(self, data):
        status, response = self._send_message(data)
        lb = session.query(LoadBalancer).\
            filter(LoadBalancer.id == self.lbid).\
            first()
        if not status:
            lb.status = 'ERROR'
            lb.errmsg = response
            pass
        else:
            lb.status = 'ACTIVE'
            pass
        session.commit()

    def _send_message(self, message):
        job_status = self.gearman_client.submit_job(
            self.host, message, background=False, wait_until_complete=True,
            max_retries=3, poll_timeout=30.0
        )
        if job_status.state == 'UNKNOWN':
            # Gearman server connection failed
            return False, "System error communicating with load balancer"
        if job_status.timed_out:
            # Job timed out
            return False, "Timeout error communicating with load balancer"
        self.logger.debug(job_status.result)
        if 'badRequest' in job_status.result:
            error = job_status.result['badRequest']['validationErrors']
            return False, error['message']
        if job_status.result['hpcs_response'] == 'FAIL':
            # Worker says 'no'
            if 'hpcs_error' in job_status.result:
                error = job_status.result['hpcs_error']
            else:
                error = 'Load Balancer error'
            return False, error
        return True, job_status.result
