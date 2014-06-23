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
from libra.common.api.lbaas import LoadBalancer, Device, db_session
from libra.common.api.lbaas import Billing, Stats
from libra.admin_api.stats.stats_gearman import GearJobs
from libra.openstack.common import timeutils
from libra.openstack.common import log as logging
from sqlalchemy.sql import func


LOG = logging.getLogger(__name__)


class UsageStats(object):

    STATS_SECONDS = cfg.CONF['admin_api'].stats_timer_seconds

    def __init__(self, drivers):
        self.drivers = drivers
        self.stats_timer = None
        self.server_id = cfg.CONF['admin_api']['server_id']
        self.number_of_servers = cfg.CONF['admin_api']['number_of_servers']
        self.stats_freq = cfg.CONF['admin_api'].stats_freq

        self.start_stats_sched()

    def shutdown(self):
        if self.stats_timer:
            self.stats_timer.cancel()

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
            delta = datetime.timedelta(minutes=self.stats_freq)
            exp = timeutils.utcnow() - delta
            exp_time = exp.strftime('%Y-%m-%d %H:%M:%S')

            updated = session.query(
                Billing.last_update
            ).filter(Billing.name == "stats").\
                filter(Billing.last_update > exp_time).\
                first()

            if updated is not None:
                # Not time yet
                LOG.info('Not time to gather stats yet {0}'.format(exp_time))
                session.rollback()
                return 0, 0

            # Update the stats timestamp
            session.query(Billing).\
                filter(Billing.name == "stats").\
                update({"last_update": func.now()},
                       synchronize_session='fetch')

            # Get all the online devices to query for stats
            devices = session.query(
                Device.id, Device.name
            ).filter(Device.status == 'ONLINE').all()

            if devices is None or len(devices) == 0:
                LOG.error('No ONLINE devices to gather usage stats from')
                session.rollback()
                return 0, 0
            total = len(devices)

            for device in devices:
                node_list.append(device.name)
            gearman = GearJobs()
            failed_list, results = gearman.get_stats(node_list)
            failed = len(failed_list)

            if failed > 0:
                self._send_fails(failed_list)

            if total > failed:
                # We have some success
                self._update_stats(results, failed_list)
                session.commit()
            else:
                # Everything failed. Retry these on the next timer firing
                session.rollback()

        return failed, total

    def _update_stats(self, results, failed_list):
        with db_session() as session:
            lbs = session.query(
                LoadBalancer.id,
                LoadBalancer.protocol,
                LoadBalancer.status,
                Device.name
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
                    if lb.name not in failed_list:
                        LOG.error(
                            'No stats results found for Device {0}, LBID {1}'
                            .format(lb.name, lb.id))
                    continue

                result = results[lb.name]
                protocol = lb.protocol.lower()
                if protocol != "http":
                    # GALERA or TCP = TCP at the worker
                    protocol = "tcp"

                bytes_out = -1
                for data in result["loadBalancers"]:
                    if data["protocol"] == protocol:
                        bytes_out = data["bytes_out"]

                if bytes_out == -1:
                    LOG.error(
                        'No stats found for Device {0}, '
                        'LBID {1}, protocol {2}'
                        .format(lb.name, lb.id, protocol))
                    continue

                new_entry = Stats()
                new_entry.lbid = lb.id
                new_entry.period_start = result["utc_start"]
                new_entry.period_end = result["utc_end"]
                new_entry.bytes_out = bytes_out
                new_entry.status = lb.status
                session.add(new_entry)
                session.flush
                added += 1
            session.commit()
            LOG.info(
                '{total} loadbalancers stats queried, {fail} failed'
                .format(total=total, fail=total - added))

    def _send_fails(self, failed_list):
        with db_session() as session:
            for device_name in failed_list:
                data = self._get_lb(device_name, session)
                if not data:
                    LOG.error(
                        'Device {0} has no Loadbalancer attached during '
                        'statistics gathering'.format(device_name)
                    )
                    continue

                LOG.error(
                    'Load balancer failed statistics gathering request '
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
