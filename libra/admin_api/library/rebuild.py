# Copyright 2014 Hewlett-Packard Development Company, L.P.
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

import ipaddress
from libra.common.api.lbaas import loadbalancers_devices, Vip, Counters
from libra.common.api.lbaas import Device, LoadBalancer, db_session
from libra.common.api.gearman_client import submit_job, submit_vip_job
from libra.openstack.common import log


LOG = log.getLogger(__name__)


def rebuild_device(device_id):
    new_device_id = None
    new_device_name = None
    with db_session() as session:
        new_device = session.query(Device).\
            filter(~Device.id.in_(
                session.query(loadbalancers_devices.c.device)
            )).\
            filter(Device.status == "OFFLINE").\
            filter(Device.pingCount == 0).\
            with_lockmode('update').\
            first()
        if new_device is None:
            session.rollback()
            LOG.error(
                'No spare devices when trying to rebuild device {0}'
                .format(device_id)
            )
            return (
                500,
                dict(
                    faultcode="Server",
                    faultstring='No spare devices when trying to rebuild '
                                'device {0}'.format(device_id)
                )
            )
        new_device_id = new_device.id
        new_device_name = new_device.name
        LOG.info(
            "Moving device {0} to device {1}"
            .format(device_id, new_device_id)
        )
        lbs = session.query(LoadBalancer).\
            join(LoadBalancer.devices).\
            filter(Device.id == device_id).all()
        for lb in lbs:
            lb.devices = [new_device]
            lb.status = "ERROR(REBUILDING)"
        new_device.status = 'BUILDING'
        lbid = lbs[0].id
        session.commit()
    submit_job(
        'UPDATE', new_device_name, new_device_id, lbid
    )
    with db_session() as session:
        new_device = session.query(Device).\
            filter(Device.id == new_device_id).first()
        vip = session.query(Vip).filter(Vip.device == device_id).first()
        if vip:
            vip.device = new_device_id
        device = session.query(Device).\
            filter(Device.id == device_id).first()
        device.status = 'DELETED'
        lbs = session.query(LoadBalancer).\
            join(LoadBalancer.devices).\
            filter(Device.id == new_device_id).all()
        for lb in lbs:
            lb.errmsg = "Load Balancer rebuild on new device"
        if vip:
            LOG.info(
                "Moving IP {0} and marking device {1} for deletion"
                .format(str(ipaddress.IPv4Address(vip.ip)), device_id)
            )
            submit_vip_job(
                'ASSIGN', new_device_name, vip.id
            )
        new_device.status = 'ONLINE'
        counter = session.query(Counters).\
            filter(Counters.name == 'loadbalancers_rebuild').first()
        counter.value += 1
        session.commit()
    return (
        200,
        dict(oldId=device_id, newId=new_device_id)
    )
