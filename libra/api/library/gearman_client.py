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
from libra.api.model.lbaas import LoadBalancer, session, Device
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
    if job_type == 'DELETE':
        client.send_delete(data)


class GearmanClientThread(object):
    def __init__(self, logger, host, lbid):
        self.logger = logger
        self.host = host
        self.lbid = lbid
        self.gearman_client = JSONGearmanClient(conf.gearman.server)

    def send_delete(self, data):
        count = session.query(
            LoadBalancer
        ).join(LoadBalancer.devices).\
            filter(Device.id == data).\
            count()
        if count >= 1:
            # This is an update message because we want to retain the
            # remaining LB
            keep_lb = session.query(LoadBalancer).join(LoadBalancer.nodes).\
                join(LoadBalancer.devices).\
                filter(Device.id == data).\
                filter(LoadBalancer.id != self.lbid).\
                first()
            job_data = {
                'hpcs_action': 'UPDATE',
                'loadBalancers': [{
                    'name': keep_lb.name,
                    'protocol': keep_lb.protocol,
                    'port': keep_lb.port,
                    'nodes': []
                }]
            }
            for node in keep_lb.nodes:
                if node.enabled:
                    condition = 'ENABLED'
                else:
                    condition = 'DISABLED'
                node_data = {
                    'port': node.port, 'address': node.address,
                    'weight': node.weight, 'condition': condition
                }
                job_data['loadBalancers'][0]['nodes'].append(node_data)
        else:
            # This is a delete
            job_data = {"hpcs_action": "DELETE"}

        status, response = self._send_message(job_data)
        lb = session.query(LoadBalancer).\
            filter(LoadBalancer.id == self.lbid).\
            first()
        if not status:
            lb.status = 'ERROR'
            lb.errmsg = response
        else:
            lb.status = 'DELETED'
            if count == 0:
                device = session.query(Device).\
                    filter(Device.id == data).first()
                device.status = 'OFFLINE'
        session.commit()

    def send_update(self, data):
        lbs = session.query(
            LoadBalancer
        ).join(LoadBalancer.nodes).\
            join(LoadBalancer.devices).\
            filter(Device.id == data).\
            all()
        job_data = {
            'hpcs_action': 'UPDATE',
            'loadBalancers': []
        }
        for lb in lbs:
            lb_data = {
                'name': lb.name,
                'protocol': lb.protocol,
                'port': lb.port,
                'nodes': []
            }
            for node in lb.nodes:
                if node.enabled:
                    condition = 'ENABLED'
                else:
                    condition = 'DISABLED'
                node_data = {
                    'port': node.port, 'address': node.address,
                    'weight': node.weight, 'condition': condition
                }
                lb_data['nodes'].append(node_data)
            job_data['loadBalancers'].append(lb_data)
        status, response = self._send_message(job_data)
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
