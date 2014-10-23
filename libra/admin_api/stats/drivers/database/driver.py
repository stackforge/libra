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

from libra.admin_api.stats.drivers.base import AlertDriver
from libra.common.api.lbaas import Device, LoadBalancer, db_session
from libra.common.api.lbaas import loadbalancers_devices
from libra.admin_api.library.rebuild import rebuild_device
from libra.openstack.common import log
from oslo.config import cfg


LOG = log.getLogger(__name__)


class DbDriver(AlertDriver):
    def send_alert(self, message, device_id, device_ip, device_name, device_tenant):
        with db_session() as session:
            device = session.query(Device).\
                filter(Device.id == device_id).first()

            device.status = "ERROR"
            errmsg = "Load Balancer has failed, attempting rebuild"

            lbs = session.query(
                loadbalancers_devices.c.loadbalancer).\
                filter(loadbalancers_devices.c.device == device_id).\
                all()

            # TODO: make it so that we don't get stuck in LB ERROR here when
            # a rebuild fails due to something like a bad device.  Maybe have
            # an attempted rebuild count?
            for lb in lbs:
                session.query(LoadBalancer).\
                    filter(LoadBalancer.id == lb[0]).\
                    update({"status": "ERROR", "errmsg": errmsg},
                           synchronize_session='fetch')

                session.flush()

            session.commit()
            self._rebuild_device(device_id)

    def send_delete(self, message, device_id, device_ip, device_name):
        OFFLINE_FAILED_SAVE = cfg.CONF['admin_api'].offline_failed_save
        with db_session() as session:
            saved_count = session.query(Device).\
                filter(Device.status == 'SAVED-OFFLINE').count()
            if OFFLINE_FAILED_SAVE > 0 and saved_count < OFFLINE_FAILED_SAVE:
                session.query(Device).\
                    filter(Device.id == device_id).\
                    update({"status": "SAVED-OFFLINE"},\
                           synchronize_session='fetch')
            else:
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
            elif lb.status == 'ACTIVE' and degraded:
                lb.errmsg = "A node on the load balancer has failed"
                lb.status = 'DEGRADED'
            elif lb.status == 'DEGRADED' and not degraded:
                lb.errmsg = "A node on the load balancer has recovered"
                lb.status = 'ACTIVE'

            session.commit()

    def _rebuild_device(self, device_id):
        rebuild_device(device_id)
