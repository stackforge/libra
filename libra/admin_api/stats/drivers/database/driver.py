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

import logging
import ipaddress
from libra.common.api.lbaas import Device, LoadBalancer, db_session
from libra.common.api.lbaas import loadbalancers_devices, Vip
from libra.common.api.gearman_client import submit_job, submit_vip_job
from libra.admin_api.stats.drivers.base import AlertDriver


class DbDriver(AlertDriver):
    def send_alert(self, message, device_id):
        with db_session() as session:
            device = session.query(Device).\
                filter(Device.id == device_id).first()

            device.status = "ERROR"
            errmsg = "Load Balancer has failed, attempting rebuild"

            lbs = session.query(
                loadbalancers_devices.c.loadbalancer).\
                filter(loadbalancers_devices.c.device == device_id).\
                all()

            for lb in lbs:
                session.query(LoadBalancer).\
                    filter(LoadBalancer.id == lb[0]).\
                    update({"status": "ERROR", "errmsg": errmsg},
                           synchronize_session='fetch')

                session.flush()

            session.commit()
            self._rebuild_device(device_id)

    def send_delete(self, message, device_id):
        with db_session() as session:
            session.query(Device).\
                filter(Device.id == device_id).\
                update({"status": "DELETED"}, synchronize_session='fetch')
            session.commit()

    def send_node_change(self, message, lbid, degraded):
        with db_session() as session:
            lb = session.query(LoadBalancer).\
                filter(LoadBalancer.id == lbid).first()

            if lb.status == 'ERROR':
                lb.errmsg = "Load balancer has failed"
            elif degraded:
                lb.errmsg = "A node on the load balancer has failed"
                lb.status = 'DEGRADED'
            else:
                lb.errmsg = "A node on the load balancer has recovered"
                lb.status = 'ACTIVE'

            session.commit()

    def _rebuild_device(self, device_id):
        logger = logging.getLogger(__name__)
        new_device_id = None
        new_device_name = None
        with db_session() as session:
            new_device = session.query(Device).\
                filter(~Device.id.in_(
                    session.query(loadbalancers_devices.c.device)
                )).\
                filter(Device.status == "OFFLINE").\
                with_lockmode('update').\
                first()
            if new_device is None:
                session.rollback()
                logger.error(
                    'No spare devices when trying to rebuild device {0}'
                    .format(device_id)
                )
                return
            new_device_id = new_device.id
            new_device_name = new_device.name
            logger.info(
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
            vip.device = new_device_id
            device = session.query(Device).\
                filter(Device.id == device_id).first()
            device.status = 'DELETED'
            lbs = session.query(LoadBalancer).\
                join(LoadBalancer.devices).\
                filter(Device.id == new_device_id).all()
            for lb in lbs:
                lb.errmsg = "Load Balancer rebuild on new device"
            logger.info(
                "Moving IP {0} and marking device {1} for deletion"
                .format(str(ipaddress.IPv4Address(vip.ip)), device_id)
            )
            submit_vip_job(
                'ASSIGN', new_device_name, str(ipaddress.IPv4Address(vip.ip))
            )
            new_device.status = 'ONLINE'
            session.commit()
