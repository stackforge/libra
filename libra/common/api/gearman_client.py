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
import gear
import json

eventlet.monkey_patch()
import ipaddress
from libra.common.api.lbaas import LoadBalancer, db_session, Device, Node, Vip
from libra.common.api.lbaas import HealthMonitor, Counters
from libra.common.api.lbaas import loadbalancers_devices
from libra.common.api.mnb import update_mnb
from libra.openstack.common import log
from pecan import conf
from time import sleep

LOG = log.getLogger(__name__)
POLL_COUNT = 10
POLL_SLEEP = 10

gearman_workers = [
    'UPDATE',  # Create/Update a Load Balancer.
    'SUSPEND',  # Suspend a Load Balancer.
    'ENABLE',  # Enable a suspended Load Balancer.
    'DELETE',  # Delete a Load Balancer.
    'DISCOVER',  # Return service discovery information.
    'ARCHIVE',  # Archive LB log files.
    'METRICS',  # Get load balancer statistics.
    'STATS'     # Ping load balancers
]


class DisconnectClient(gear.Client):
    def handleDisconnect(self, job):
        job.disconnect = True


class DisconnectJob(gear.Job):
    def __init__(self, name, arguments):
        super(DisconnectJob, self).__init__(name, arguments)
        self.disconnect = False


def submit_job(job_type, host, data, lbid):
    eventlet.spawn_n(client_job, job_type, str(host), data, lbid)


def submit_vip_job(job_type, device, vip):
    eventlet.spawn_n(
        client_job, job_type, "libra_pool_mgm", device, vip
    )


def client_job(job_type, host, data, lbid):
    try:
        client = GearmanClientThread(host, lbid)
        LOG.info(
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
            # Try the assign 5 times
            for x in xrange(0, 5):
                status = client.send_assign(data)
                if status:
                    break
            with db_session() as session:
                device = session.query(Device).\
                    filter(Device.name == data).first()
                if device is None:
                    LOG.error(
                        "Device {0} not found in ASSIGN, this shouldn't happen"
                        .format(data)
                    )
                    return
                mnb_data = {}
                if not status:
                    LOG.error(
                        "Giving up vip assign for device {0}".format(data)
                    )
                    errmsg = 'Floating IP assign failed'
                    client._set_error(device.id, errmsg, session)
                else:
                    lbs = session.query(
                        LoadBalancer
                    ).join(LoadBalancer.nodes).\
                        join(LoadBalancer.devices).\
                        filter(Device.id == device.id).\
                        filter(LoadBalancer.status != 'DELETED').\
                        all()
                    for lb in lbs:
                        if lb.status == 'BUILD':
                            # Only send a create message to MnB if we
                            # are going from BUILD to ACTIVE. After the
                            # DB is updated.
                            mnb_data["lbid"] = lb.id
                            mnb_data["tenantid"] = lb.tenantid
                        lb.status = 'ACTIVE'
                    device.status = 'ONLINE'
                session.commit()

                # Send the MnB create if needed
                if "lbid" in mnb_data:
                    update_mnb('lbaas.instance.create',
                               mnb_data["lbid"],
                               mnb_data["tenantid"])

        if job_type == 'REMOVE':
            client.send_remove(data)
        return
    except:
        LOG.exception("Gearman thread unhandled exception")


class GearmanClientThread(object):
    def __init__(self, host, lbid):
        self.host = host
        self.lbid = lbid

        self.gear_client = DisconnectClient()

        for server in conf.gearman.server:
            ghost, gport = server.split(':')
            self.gear_client.addServer(ghost,
                                       int(gport),
                                       conf.gearman.ssl_key,
                                       conf.gearman.ssl_cert,
                                       conf.gearman.ssl_ca)

    def send_assign(self, data):
        NULL = None  # For pep8
        with db_session() as session:
            device = session.query(Device).\
                filter(Device.name == data).first()
            if device is None:
                LOG.error(
                    "VIP assign have been given non existent device {0}"
                    .format(data)
                )
                session.rollback()
                return False
            if not self.lbid:
                vip = session.query(Vip).\
                    filter(Vip.device == NULL).\
                    with_lockmode('update').\
                    first()
                if vip is None:
                    errmsg = 'Floating IP assign failed (none available)'
                    LOG.error(
                        "Failed to assign IP to device {0} (none available)"
                        .format(data)
                    )
                    self._set_error(device.id, errmsg, session)
                    session.commit()
                    return False
            else:
                vip = session.query(Vip).\
                    filter(Vip.id == self.lbid).first()
                if vip is None:
                    errmsg = 'Cannot find existing floating IP'
                    LOG.error(
                        "Failed to assign IP to device {0}"
                        .format(data)
                    )
                    self._set_error(device.id, errmsg, session)
                    session.commit()
                    return False
            vip.device = device.id
            vip_id = vip.id
            vip_ip = vip.ip
            session.commit()
        ip_str = str(ipaddress.IPv4Address(vip_ip))

        job_data = {
            'action': 'ASSIGN_IP',
            'name': data,
            'ip': ip_str
        }
        status, response = self._send_message(job_data, 'response')
        if status:
            return True
        elif self.lbid:
            LOG.error(
                "Failed to assign IP {0} to device {1}"
                .format(ip_str, data)
            )
        else:
            LOG.error(
                "Failed to assign IP {0} to device {1}"
                .format(ip_str, data)
            )
            # set to device 0 to make sure it won't be used again
            with db_session() as session:
                vip = session.query(Vip).filter(Vip.id == vip_id).first()
                vip.device = 0
                session.commit()
            submit_vip_job('REMOVE', None, ip_str)
        return False

    def send_remove(self, data=None):
        job_data = {
            'action': 'DELETE_IP',
            'ip': self.lbid
        }
        ip_int = int(ipaddress.IPv4Address(unicode(self.lbid)))
        for x in xrange(0, 5):
            LOG.info(
                'Attempt to delete IP {0} #{1}'
                .format(self.lbid, x)
            )
            status, response = self._send_message(job_data, 'response')
            if status:
                break
        with db_session() as session:
            if not status:
                LOG.error(
                    "Failed to delete IP {0}"
                    .format(self.lbid)
                )
                # Set to 0 to mark as something that needs cleaning up
                # but cannot be used again
                vip = session.query(Vip).\
                    filter(Vip.ip == ip_int).first()
                vip.device = 0
            else:
                session.query(Vip).\
                    filter(Vip.ip == ip_int).delete()
                counter = session.query(Counters).\
                    filter(Counters.name == 'vips_deleted').first()
                counter.value += 1
            session.commit()

    def send_delete(self, data):
        with db_session() as session:
            count = session.query(
                LoadBalancer
            ).join(LoadBalancer.devices).\
                filter(Device.id == data).\
                filter(LoadBalancer.id != self.lbid).\
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
                dev = session.query(Device.name).\
                    filter(Device.id == data).first()
                vip = session.query(Vip).\
                    filter(Vip.device == data).first()
                if vip:
                    submit_vip_job(
                        'REMOVE', dev.name, str(ipaddress.IPv4Address(vip.ip))
                    )
                job_data = {"hpcs_action": "DELETE"}

            status, response = self._send_message(job_data, 'hpcs_response')
            lb = session.query(LoadBalancer).\
                filter(LoadBalancer.id == self.lbid).\
                first()
            if not status:
                LOG.error(
                    "Failed Gearman delete for LB {0}".format(lb.id)
                )
                self._set_error(data, response, session)
            lb.status = 'DELETED'
            tenant_id = lb.tenantid

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
            counter = session.query(Counters).\
                filter(Counters.name == 'loadbalancers_deleted').first()
            counter.value += 1
            session.commit()

            # Notify billing of the LB deletion
            update_mnb('lbaas.instance.delete', self.lbid, tenant_id)

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
        if device is None:
            # Device already deleted, probably a race between the OFFLINE check
            # and auto-failover
            return
        device.status = 'ERROR'
        counter = session.query(Counters).\
            filter(Counters.name == 'loadbalancers_error').first()
        for lb in lbs:
            counter.value += 1
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
            counter = session.query(Counters).\
                filter(Counters.name == 'log_archives').first()
            counter.value += 1
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

            degraded = []
            if lbs is None:
                LOG.error(
                    'Attempting to send empty LB data for device {0} ({1}), '
                    'something went wrong'.format(data, self.host)
                )
                self._set_error(data, "LB config error", session)
                session.commit()
                return

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
                    backup = 'FALSE'
                    if node.backup != 0:
                        backup = 'TRUE'
                    node_data = {
                        'id': node.id, 'port': node.port,
                        'address': node.address, 'weight': node.weight,
                        'condition': condition, 'backup': backup
                    }

                    lb_data['nodes'].append(node_data)
                    # Track if we have a DEGRADED LB
                    if node.status == 'ERROR':
                        degraded.append(lb.id)

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

                # All new LBs created since these options were supported
                # will have default values in the DB. Pre-existing LBs will
                # not have any values, so we need to check for that.
                if any([lb.timeout, lb.retries]):
                    lb_data['options'] = {
                        'client_timeout': lb.timeout,
                        'server_timeout': lb.timeout,
                        'connect_timeout': lb.timeout,
                        'connect_retries': lb.retries
                    }

                lb_data['monitor'] = monitor_data
                job_data['loadBalancers'].append(lb_data)

            # Update the worker
            mnb_data = {}
            status, response = self._send_message(job_data, 'hpcs_response')
            if not status:
                self._set_error(data, response, session)
            else:
                for lb in lbs:
                    if lb.id in degraded:
                        lb.status = 'DEGRADED'
                        lb.errmsg = "A node on the load balancer has failed"
                    elif lb.status == 'ERROR':
                        # Do nothing because something else failed in the mean
                        # time
                        pass
                    elif lb.status == 'BUILD':
                        # Do nothing if a new device, stay in BUILD state until
                        # floating IP assign finishes
                        if len(lbs) > 1:
                            lb.status = 'ACTIVE'
                            if lb.id == self.lbid:
                                # This is the new LB being added to a device.
                                # We don't have to assign a vip so we can
                                # notify billing of the LB creation (once the
                                # DB is updated)
                                mnb_data["lbid"] = lb.id
                                mnb_data["tenantid"] = lb.tenantid
                    else:
                        lb.status = 'ACTIVE'
                        lb.errmsg = None
            device = session.query(Device).\
                filter(Device.id == data).\
                first()
            if device is None:
                # Shouldn't hit here, but just to be safe
                session.commit()
                return
            if device.status == 'BUILD' and len(lbs) > 1:
                device.status = 'ONLINE'
            device_name = device.name
            device_status = device.status
            counter = session.query(Counters).\
                filter(Counters.name == 'loadbalancers_updated').first()
            counter.value += 1
            session.commit()
            if device_status == 'BUILD':
                submit_vip_job(
                    'ASSIGN', device_name, None
                )

            # Send the MnB create if needed
            if "lbid" in mnb_data:
                update_mnb('lbaas.instance.create',
                           mnb_data["lbid"],
                           mnb_data["tenantid"])

    def _send_message(self, message, response_name):

        self.gear_client.waitForServer()

        job = DisconnectJob(self.host, json.dumps(message))

        self.gear_client.submitJob(job)

        pollcount = 0
        # Would like to make these config file settings
        while not job.complete and pollcount < POLL_COUNT:
            sleep(POLL_SLEEP)
            pollcount += 1

        if job.disconnect:
            LOG.error('Gearman Job server fail - disconnect')
            return False, "Gearman Job server fail - "\
                "disconnect communicating with load balancer"

        # We timed out waiting for the job to finish
        if not job.complete:
            LOG.warning('Gearman timeout talking to {0}'.format(self.host))
            return False, "Timeout error communicating with load balancer"

        result = json.loads(job.data[0])

        LOG.debug(result)

        if 'badRequest' in result:
            error = result['badRequest']['validationErrors']
            return False, error['message']
        if result[response_name] == 'FAIL':
            # Worker says 'no'
            if 'hpcs_error' in result:
                error = result['hpcs_error']
            else:
                error = 'Load Balancer error'
            LOG.error(
                'Gearman error response from {0}: {1}'.format(self.host, error)
            )
            return False, error
        LOG.info('Gearman success from {0}'.format(self.host))
        return True, result