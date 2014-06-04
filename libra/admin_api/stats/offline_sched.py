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

from datetime import datetime
from oslo.config import cfg

from libra.common.api.lbaas import Counters, Device, db_session
from libra.admin_api.stats.stats_gearman import GearJobs
from libra.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class OfflineStats(object):

    OFFLINE_SECONDS = cfg.CONF['admin_api'].offline_timer_seconds

    def __init__(self, drivers):
        self.drivers = drivers
        self.offline_timer = None
        self.ping_limit = cfg.CONF['admin_api']['stats_offline_ping_limit']
        self.error_limit = cfg.CONF['admin_api']['stats_device_error_limit']
        self.server_id = cfg.CONF['admin_api']['server_id']
        self.number_of_servers = cfg.CONF['admin_api']['number_of_servers']

        self.gearman = GearJobs()
        self.start_offline_sched()

    def shutdown(self):
        if self.offline_timer:
            self.offline_timer.cancel()

    def check_offline_lbs(self):
        # Work out if it is our turn to run
        minute = datetime.now().minute
        if self.server_id != minute % self.number_of_servers:
            LOG.info('Not our turn to run OFFLINE check, sleeping')
            self.start_offline_sched()
            return
        tested = 0
        failed = 0
        try:
            tested, failed = self._exec_offline_check()
        except Exception:
            LOG.exception('Uncaught exception during OFFLINE check')
        # Need to restart timer after every ping cycle
        LOG.info(
            '{tested} OFFLINE loadbalancers tested, {failed} failed'
            .format(tested=tested, failed=failed)
        )
        self.start_offline_sched()

    def _exec_offline_check(self):
        tested = 0
        failed = 0
        node_list = []
        LOG.info('Running OFFLINE check')
        with db_session() as session:
            # Join to ensure device is in-use
            devices = session.query(
                Device.id, Device.name
            ).filter(Device.status == 'OFFLINE').all()

            tested = len(devices)
            if tested == 0:
                LOG.info('No OFFLINE Load Balancers to check')
                return (0, 0)
            for lb in devices:
                node_list.append(lb.name)
            failed_lbs = self.gearman.offline_check(node_list)
            failed = len(failed_lbs)
            if failed > self.error_limit:
                LOG.error(
                    'Too many simultaneous Load Balancer Failures.'
                    ' Aborting deletion attempt'
                )
                return tested, failed

            if failed > 0:
                self._send_delete(failed_lbs)

            # Clear the ping counts for all devices not in
            # the failed list
            succeeded = list(set(node_list) - set(failed_lbs))
            session.query(Device.name, Device.pingCount).\
                filter(Device.name.in_(succeeded)).\
                update({"pingCount": 0}, synchronize_session='fetch')

            session.commit()

        return tested, failed

    def _send_delete(self, failed_nodes):
        with db_session() as session:
            for lb in failed_nodes:
                # Get the current ping count
                data = session.query(
                    Device.id, Device.pingCount).\
                    filter(Device.name == lb).first()

                if not data:
                    LOG.error(
                        'Device {0} no longer exists'.format(data.id)
                    )
                    continue

                if data.pingCount < self.ping_limit:
                    data.pingCount += 1
                    LOG.error(
                        'Offline Device {0} has failed {1} ping attempts'.
                        format(lb, data.pingCount)
                    )
                    session.query(Device).\
                        filter(Device.name == lb).\
                        update({"pingCount": data.pingCount},
                               synchronize_session='fetch')
                    session.flush()
                    continue

                message = (
                    'Load balancer {0} unreachable and marked for deletion'.
                    format(lb)
                )
                for driver in self.drivers:
                    instance = driver()
                    LOG.info(
                        'Sending delete request for {0} to {1}'.format(
                            lb, instance.__class__.__name__
                        )
                    )
                    instance.send_delete(message, data.id)
                counter = session.query(Counters).\
                    filter(Counters.name == 'devices_offline_failed').first()
                counter.value += 1
            session.commit()

    def start_offline_sched(self):
        # Always try to hit the expected second mark for offline checks
        seconds = datetime.now().second
        if seconds < self.OFFLINE_SECONDS:
            sleeptime = self.OFFLINE_SECONDS - seconds
        else:
            sleeptime = 60 - (seconds - self.OFFLINE_SECONDS)

        LOG.info('LB offline check timer sleeping for {secs} seconds'
                 .format(secs=sleeptime))
        self.offline_timer = threading.Timer(
            sleeptime, self.check_offline_lbs, ()
        )
        self.offline_timer.start()
