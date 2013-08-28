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
import ipaddress
from libra.common.json_gearman import JSONGearmanClient
from libra.api.model.lbaas import LoadBalancer, db_session, Device, Node, Vip
from libra.api.model.lbaas import HealthMonitor
from libra.api.model.lbaas import loadbalancers_devices
from sqlalchemy.exc import OperationalError
from pecan import conf


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


def submit_vip_job(job_type, device, vip):
    logger = logging.getLogger(__name__)
    eventlet.spawn_n(
        client_job, logger, job_type, "libra_pool_mgm", device, vip
    )


def client_job(logger, job_type, host, data, lbid):
    for x in xrange(5):
        try:
            client = GearmanClientThread(logger, host, lbid)
            logger.info(
                "Sending Gearman job {0} to {1} for loadbalancer {2}".format(
                    job_type, host, lbid
                )
            )
            if job_type == 'UPDATE':
                client.send_update(data)
            if job_type == 'DELETE':
                client.send_delete(data)
            if job_type == 'ARCHIVE':
                client.send_archive(data)
            if job_type == 'ASSIGN':
                client.send_assign(data)
            if job_type == 'REMOVE':
                client.send_remove(data)
            return
        except OperationalError:
            # Auto retry on galera locking error
            logger.warning(
                "Galera deadlock in gearman, retry {0}".format(x+1)
            )
        except:
            logger.exception("Gearman thread unhandled exception")

    logger.error("Gearman thread could not talk to DB")


class GearmanClientThread(object):
    def __init__(self, logger, host, lbid):
        self.logger = logger
        self.host = host
        self.lbid = lbid

        if all([conf.gearman.ssl_key, conf.gearman.ssl_cert,
                conf.gearman.ssl_ca]):
            # Use SSL connections to each Gearman job server.
            ssl_server_list = []
            for server in conf.gearman.server:
                ghost, gport = server.split(':')
                ssl_server_list.append({'host': ghost,
                                        'port': int(gport),
                                        'keyfile': conf.gearman.ssl_key,
                                        'certfile': conf.gearman.ssl_cert,
                                        'ca_certs': conf.gearman.ssl_ca})
            self.gearman_client = JSONGearmanClient(ssl_server_list)
        else:
            self.gearman_client = JSONGearmanClient(conf.gearman.server)

    def send_assign(self, data):
        job_data = {
            'action': 'ASSIGN_IP',
            'name': data,
            'ip': self.lbid
        }
        status, response = self._send_message(job_data, 'response')
        if not status:
            self.logger.error(
                "Failed to assign IP {0} to device {1}".format(self.lbid, data)
            )

    def send_remove(self, data):
        job_data = {
            'action': 'REMOVE_IP',
            'name': data,
            'ip': self.lbid
        }
        status, response = self._send_message(job_data, 'response')
        if not status:
            self.logger.error(
                "Failed to remove IP {0} from device {1}"
                .format(self.lbid, data)
            )

    def send_delete(self, data):
        with db_session() as session:
            count = session.query(
                LoadBalancer
            ).join(LoadBalancer.devices).\
                filter(Device.id == data).\
                filter(LoadBalancer.status != 'DELETED').\
                filter(LoadBalancer.status != 'PENDING_DELETE').\
                count()
            if count >= 1:
                # This is an update message because we want to retain the
                # remaining LB
                keep_lb = session.query(LoadBalancer).\
                    join(LoadBalancer.nodes).\
                    join(LoadBalancer.devices).\
                    filter(Device.id == data).\
                    filter(LoadBalancer.id != self.lbid).\
                    filter(LoadBalancer.status != 'DELETED').\
                    filter(LoadBalancer.status != 'PENDING_DELETE').\
                    first()
                job_data = {
                    'hpcs_action': 'UPDATE',
                    'loadBalancers': [{
                        'name': keep_lb.name,
                        'protocol': keep_lb.protocol,
                        'algorithm': keep_lb.algorithm,
                        'port': keep_lb.port,
                        'nodes': []
                    }]
                }
                for node in keep_lb.nodes:
                    if not node.enabled:
                        continue
                    condition = 'ENABLED'
                    node_data = {
                        'id': node.id, 'port': node.port,
                        'address': node.address, 'weight': node.weight,
                        'condition': condition
                    }
                    job_data['loadBalancers'][0]['nodes'].append(node_data)
            else:
                # This is a delete
                vip = session.query(Vip).filter(Vip.device == data)
                submit_vip_job(
                    'REMOVE', data, str(ipaddress.IPv4Address(vip.ip))
                )
                vip.device = None
                job_data = {"hpcs_action": "DELETE"}

            status, response = self._send_message(job_data, 'hpcs_response')
            lb = session.query(LoadBalancer).\
                filter(LoadBalancer.id == self.lbid).\
                first()
            if not status:
                self.logger.error(
                    "Failed Gearman delete for LB {0}".format(lb.id)
                )
                self._set_error(data, response, session)
            lb.status = 'DELETED'
            if count == 0:
                # Device should never be used again
                device = session.query(Device).\
                    filter(Device.id == data).first()
                device.status = 'DELETED'
            # Remove LB-device join
            session.execute(loadbalancers_devices.delete().where(
                loadbalancers_devices.c.loadbalancer == lb.id
            ))
            session.query(Node).\
                filter(Node.lbid == lb.id).delete()
            session.query(HealthMonitor).\
                filter(HealthMonitor.lbid == lb.id).delete()
            session.commit()

    def _set_error(self, device_id, errmsg, session):
        lbs = session.query(
            LoadBalancer
        ).join(LoadBalancer.nodes).\
            join(LoadBalancer.devices).\
            filter(Device.id == device_id).\
            filter(LoadBalancer.status != 'DELETED').\
            all()
        device = session.query(Device).\
            filter(Device.id == device_id).\
            first()
        device.status = 'ERROR'
        for lb in lbs:
            lb.status = 'ERROR'
            lb.errmsg = errmsg

    def send_archive(self, data):
        with db_session() as session:
            lb = session.query(LoadBalancer).\
                filter(LoadBalancer.id == self.lbid).\
                first()
            job_data = {
                'hpcs_action': 'ARCHIVE',
                'hpcs_object_store_basepath': data['objectStoreBasePath'],
                'hpcs_object_store_endpoint': data['objectStoreEndpoint'],
                'hpcs_object_store_token': data['authToken'],
                'hpcs_object_store_type': data['objectStoreType'],
                'loadBalancers': [{
                    'id': str(lb.id),
                    'name': lb.name,
                    'protocol': lb.protocol
                }]
            }
            status, response = self._send_message(job_data, 'hpcs_response')
            device = session.query(Device).\
                filter(Device.id == data['deviceid']).\
                first()
            if status:
                device.errmsg = 'Log archive successful'
            else:
                device.errmsg = 'Log archive failed: {0}'.format(response)
            lb.status = 'ACTIVE'
            session.commit()

    def send_update(self, data):
        with db_session() as session:
            lbs = session.query(
                LoadBalancer
            ).join(LoadBalancer.nodes).\
                join(LoadBalancer.devices).\
                filter(Device.id == data).\
                filter(LoadBalancer.status != 'DELETED').\
                all()
            job_data = {
                'hpcs_action': 'UPDATE',
                'loadBalancers': []
            }
            for lb in lbs:
                lb_data = {
                    'name': lb.name,
                    'protocol': lb.protocol,
                    'algorithm': lb.algorithm,
                    'port': lb.port,
                    'nodes': [],
                    'monitor': {}
                }
                for node in lb.nodes:
                    if not node.enabled:
                        continue
                    condition = 'ENABLED'
                    node_data = {
                        'id': node.id, 'port': node.port,
                        'address': node.address, 'weight': node.weight,
                        'condition': condition
                    }
                    lb_data['nodes'].append(node_data)

                # Add a default health monitor if one does not exist
                monitor = session.query(HealthMonitor).\
                    filter(HealthMonitor.lbid == lb.id).first()

                if monitor is None:
                    # Set it to a default configuration
                    monitor = HealthMonitor(
                        lbid=lb.id, type="CONNECT", delay=30,
                        timeout=30, attempts=2, path=None
                    )
                    session.add(monitor)
                    session.flush()

                monitor_data = {
                    'type': monitor.type,
                    'delay': monitor.delay,
                    'timeout': monitor.timeout,
                    'attempts': monitor.attempts
                }
                if monitor.path is not None:
                    monitor_data['path'] = monitor.path

                lb_data['monitor'] = monitor_data
                job_data['loadBalancers'].append(lb_data)

            # Update the worker
            status, response = self._send_message(job_data, 'hpcs_response')
            lb = session.query(LoadBalancer).\
                filter(LoadBalancer.id == self.lbid).\
                first()
            if not status:
                self._set_error(data, response, session)
            else:
                lb.status = 'ACTIVE'
            session.commit()

    def _send_message(self, message, response_name):
        job_status = self.gearman_client.submit_job(
            self.host, message, background=False, wait_until_complete=True,
            max_retries=10, poll_timeout=120.0
        )
        if job_status.state == 'UNKNOWN':
            # Gearman server connection failed
            self.logger.error('Could not talk to gearman server')
            return False, "System error communicating with load balancer"
        if job_status.timed_out:
            # Job timed out
            self.logger.warning(
                'Gearman timeout talking to {0}'.format(self.host)
            )
            return False, "Timeout error communicating with load balancer"
        self.logger.debug(job_status.result)
        if 'badRequest' in job_status.result:
            error = job_status.result['badRequest']['validationErrors']
            return False, error['message']
        if job_status.result[response_name] == 'FAIL':
            # Worker says 'no'
            if 'hpcs_error' in job_status.result:
                error = job_status.result['hpcs_error']
            else:
                error = 'Load Balancer error'
            self.logger.error(
                'Gearman error response from {0}: {1}'.format(self.host, error)
            )
            return False, error
        self.logger.info('Gearman success from {0}'.format(self.host))
        return True, job_status.result
