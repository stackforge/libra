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

import threading
import datetime

from oslo.config import cfg
from libra.common.api.lbaas import LoadBalancer, Device, Billing, db_session
from libra.admin_api.stats.stats_gearman import GearJobs
from libra.openstack.common import timeutils
from libra.openstack.common import log as logging
from sqlalchemy.sql import func


LOG = logging.getLogger(__name__)


class UsageStats(object):

    STATS_SECONDS = 0

    def __init__(self, drivers):
        self.drivers = drivers
        self.stats_timer = None
        self.server_id = cfg.CONF['admin_api']['server_id']
        self.number_of_servers = cfg.CONF['admin_api']['number_of_servers']
        self.stats_freq = cfg.CONF['admin_api'].stats_freq
        self.billing_enable = cfg.CONF['admin_api'].billing_enable

        self.start_stats_sched()

    def shutdown(self):
        if self.billing_timer:
            self.billing_timer.cancel()

    def gather_stats(self):
        # Work out if it is our turn to run
        minute = datetime.datetime.now().minute
        if self.server_id != minute % self.number_of_servers:
            self.start_stats_sched()
            return
        total = 0
        fail = 0
        try:
            fail, total = self._exec_stats()
        except Exception:
            LOG.exception('Uncaught exception during stats collection')

        # Need to restart timer after every stats cycle
        LOG.info('{total} lb device stats queried, {fail} failed'
                 .format(total=total, fail=fail))
        self.start_stats_sched()

    def _exec_stats(self):
        failed = 0
        node_list = []
        with db_session() as session:
            delta = datetime.timedelta(mins=self.stats_freq)
            exp = timeutils.utcnow() - delta
            exp_time = exp.strftime('%Y-%m-%d %H:%M:%S')

            updated = session.query(
                Billing.stats_updated
            ).\
                filter(Billing.stats_updated > exp_time).\
                with_lockmode('update').\
                first()

            if updated is None:
                #Update the stats timestamp right away
                session.query(Billing).update({"stats_updated": func.now()},
                                              synchronize_session='fetch')
                session.commit()
            else:
                session.rollback()
                return 0

        with db_session() as session:
            devices = session.query(
                Device.id, Device.name
            ).filter(Device.status == 'ONLINE').all()
            total = len(devices)
            if total == 0:
                LOG.info('No LBs to gather stats from')
                return (0, 0)
            for lb in devices:
                node_list.append(lb.name)
            gearman = GearJobs()

            failed_list, results = gearman.get_stats(node_list)
            failed = len(failed_list)

            if failed > 0:
                self._send_fails(failed_list)

            # Process node status after lb status
            self._update_stats(results)
            session.commit()

        return failed, total

    def _update_stats(self, results):
        with db_session() as session:
            lbs = session.query(
                LoadBalancer.id, LoadBalancer.protocol, Device.name
            ).join(LoadBalancer.devices).\
                filter(Device.status == 'ONLINE').all()

            if lbs is None:
                session.rollback()
                LOG.error('No Loadbalancers found when updating stats')
                return

            total = len(lbs)
            added = 0
            for lb in lbs:
                if lb.name not in results:
                    LOG.error(
                        'No stats results found for Device {0}, LBID {1}'
                        .format(lb.name, lb.id))
                    continue

                result = results[lb.name]
                protocol = lb.protocol
                if protocol != "HTTP":
                    # GALERA or TCP = TCP at the worker
                    protocol = "TCP"

                bytes_out = -1
                for data in result["loadbalancers"]:
                    if data["protocol"] == protocol:
                        bytes_out = data["bytes_out"]

                if bytes_out == -1:
                    LOG.error(
                        'No stats found for Device {0}, '
                        'LBID {1}, protocol {2}'
                        .format(lb.name, lb.id, protocol))
                    continue

                new_entry = Billing()
                new_entry.lbid = lb.id
                new_entry.period_start = result["utc_start"]
                new_entry.period_end = result["utc_end"]
                new_entry.bytes_out = bytes_out

                session.add(new_entry)
                session.flush
                added += 1

            LOG.info(
                '{total} loadbalancers stats queried, {fail} failed'
                .format(total=total, fail=total - added))

    def _send_fails(self, failed_list):
        with db_session() as session:
            for device_name in failed_list:
                data = self._gget_lb(device_name, session)
                if not data:
                    LOG.error(
                        'Device {0} has no Loadbalancer attached during STATS'.
                        format(device_name)
                    )
                    continue

                LOG.error(
                    'Load balancer failed STATS request '
                    'ID: {0}\n'
                    'IP: {1}\n'
                    'tenant: {2}\n'.format(
                        data.id, data.floatingIpAddr,
                        data.tenantid))

    def _get_lb(self, lb, session):
        lb = session.query(
            LoadBalancer.tenantid, Device.floatingIpAddr, Device.id
        ).join(LoadBalancer.devices).\
            filter(Device.name == lb).first()

        return lb

    def start_stats_sched(self):
        # Always try to hit the expected second mark for stats
        seconds = datetime.datetime.now().second
        if seconds < self.STATS_SECONDS:
            sleeptime = self.STATS_SECONDS - seconds
        else:
            sleeptime = 60 - (seconds - self.STATS_SECONDS)

        LOG.info('LB stats timer sleeping for {secs} seconds'
                 .format(secs=sleeptime))
        self.stats_timer = threading.Timer(sleeptime, self.gather_stats, ())
        self.stats_timer.start()
