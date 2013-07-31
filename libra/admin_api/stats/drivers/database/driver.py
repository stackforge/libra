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

from libra.admin_api.model.lbaas import Device, LoadBalancer, db_session
from libra.admin_api.model.lbaas import loadbalancers_devices
from libra.admin_api.stats.drivers.base import AlertDriver


class DbDriver(AlertDriver):
    def send_alert(self, message, device_id):
        self.update_status(message, device_id, 'ERROR')

    def send_repair(self, message, device_id):
        self.update_status(message, device_id, 'ONLINE')

    def update_status(self, message, device_id, status):
        with db_session() as session:
            device = session.query(Device).\
                filter(Device.id == device_id).first()

            device.status = status

            lb_status = 'ACTIVE' if status == 'ONLINE' else status

            lbs = session.query(
                loadbalancers_devices.c.loadbalancer).\
                filter(loadbalancers_devices.c.device == device_id).\
                all()

            for lb in lbs:
                session.query(LoadBalancer).\
                    filter(LoadBalancer.id == lb[0]).\
                    update({"status": lb_status, "errmsg": message},
                           synchronize_session='fetch')

                session.flush()

            session.commit()

    def send_node_change(self, message, lbid, degraded):

        with db_session() as session:
            lb = session.query(LoadBalancer).\
                filter(LoadBalancer.id == lbid).first()

            if lb.status == 'ERROR':
                lb_status = lb.status
            else:
                lb_status = 'DEGRADED' if degraded else 'ACTIVE'

            session.query(LoadBalancer).\
                filter(LoadBalancer.id == lbid).\
                update({"status": lb_status, "errmsg": message},
                       synchronize_session='fetch')

            session.commit()
