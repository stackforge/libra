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
import signal
import sys
from datetime import datetime
from libra.admin_api.model.lbaas import LoadBalancer, Device, db_session
from libra.admin_api.stats.stats_gearman import GearJobs


class NodeNotFound(Exception):
    pass


class Stats(object):
    def __init__(self, logger, args, drivers):
        self.logger = logger
        self.args = args
        self.drivers = drivers
        self.ping_timer = None
        self.repair_timer = None

        signal.signal(signal.SIGINT, self.exit_handler)
        signal.signal(signal.SIGTERM, self.exit_handler)
        logger.info("Selected stats drivers: {0}".format(args.stats_driver))

        self.ping_lbs()
        self.repair_lbs()

    def exit_handler(self, signum, frame):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        self.shutdown(False)

    def shutdown(self, error):
        if self.ping_timer:
            self.ping_timer.cancel()
        if self.repair_timer:
            self.repair_timer.cancel()

        if not error:
            self.logger.info('Safely shutting down')
            sys.exit(0)
        else:
            self.logger.info('Shutting down due to error')
            sys.exit(1)

    def repair_lbs(self):
        # Work out if it is our turn to run
        minute = datetime.now().minute
        if self.args.server_id != minute % self.args.number_of_servers:
            self.logger.info('Not our turn to run ping check, sleeping')
            self.start_repair_sched()
        tested = 0
        repaired = 0
        try:
            tested, repaired = self._exec_repair()
        except Exception:
            self.logger.exception('Uncaught exception during LB repair')
        # Need to restart timer after every ping cycle
        self.logger.info('{tested} loadbalancers tested, {repaired} repaired'
                         .format(tested=tested, repaired=repaired))
        self.start_repair_sched()

    def ping_lbs(self):
        # Work out if it is our turn to run
        minute = datetime.now().minute
        if self.args.server_id != minute % self.args.number_of_servers:
            self.logger.info('Not our turn to run ping check, sleeping')
            self.start_ping_sched()
        pings = 0
        failed = 0
        try:
            pings, failed = self._exec_ping()
        except Exception:
            self.logger.exception('Uncaught exception during LB ping')
        # Need to restart timer after every ping cycle
        self.logger.info('{pings} loadbalancers pinged, {failed} failed'
                         .format(pings=pings, failed=failed))
        self.start_ping_sched()

    def _exec_ping(self):
        pings = 0
        failed = 0
        node_list = []
        self.logger.info('Running ping check')
        with db_session() as session:
            devices = session.query(
                Device.id, Device.name
            ).filter(Device.status == 'ONLINE').all()
            pings = len(devices)
            if pings == 0:
                self.logger.info('No LBs to ping')
                return (0, 0)
            for lb in devices:
                node_list.append(lb.name)
            gearman = GearJobs(self.logger, self.args)
            failed_nodes = gearman.send_pings(node_list)
            failed = len(failed_nodes)
            if failed > 0:
                self._send_fails(failed_nodes, session)
            session.commit()
        return pings, failed

    def _exec_repair(self):
        tested = 0
        repaired = 0
        node_list = []
        self.logger.info('Running repair check')
        with db_session() as session:
            devices = session.query(
                Device.id, Device.name
            ).filter(Device.status == 'ERROR').all()

            tested = len(devices)
            if tested == 0:
                self.logger.info('No LBs need repair')
                return (0, 0)
            for lb in devices:
                node_list.append(lb.name)
            gearman = GearJobs(self.logger, self.args)
            repaired_nodes = gearman.send_repair(node_list)
            repaired = len(repaired_nodes)
            if repaired > 0:
                self._send_repair(repaired_nodes, session)
            session.commit()
        return tested, repaired

    def _send_fails(self, failed_nodes, session):
        for node in failed_nodes:
            data = self._get_node(node, session)
            if not len(data['loadBalancers']):
                self.logger.error(
                    'Device {0} has no Loadbalancer attached'.
                    format(data.id)
                )
                continue
            message = (
                'Load balancer failed\n'
                'ID: {0}\n'
                'IP: {1}\n'
                'tenant: {2}\n'.format(
                    data.id, data.floatingIpAddr,
                    data.tenantid
                )
            )
            for driver in self.drivers:
                instance = driver(self.logger, self.args)
                self.logger.info(
                    'Sending failure of {0} to {1}'.format(
                        node, instance.__class__.__name__
                    )
                )
                instance.send_alert(message, data.id)

    def _send_repair(self, repaired_nodes, session):
        for node in repaired_nodes:
            data = self._get_node(node, session)
            message = (
                'Load balancer repaired\n'
                'ID: {0}\n'
                'IP: {1}\n'
                'tenant: {2}\n'.format(
                    data.id, data.floatingIpAddr,
                    data.tenantid
                )
            )
            for driver in self.drivers:
                instance = driver(self.logger, self.args)
                self.logger.info(
                    'Sending repair of {0} to {1}'.format(
                        node, instance.__class__.__name__
                    )
                )
                instance.send_repair(message, data.id)

    def _get_node(self, node, session):
        lb = session.query(
            LoadBalancer.tenantid, Device.floatingIpAddr, Device.id
        ).join(LoadBalancer.devices).\
            filter(Device.name == node).first()

        return lb

    def start_ping_sched(self):
        self.logger.info('LB ping check timer sleeping for {secs} seconds'
                         .format(secs=self.args.stats_ping_timer))
        self.ping_timer = threading.Timer(self.args.stats_ping_timer,
                                          self.ping_lbs, ())
        self.ping_timer.start()

    def start_repair_sched(self):
        self.logger.info('LB repair check timer sleeping for {secs} seconds'
                         .format(secs=self.args.stats_repair_timer))
        self.repair_timer = threading.Timer(self.args.stats_repair_timer,
                                            self.repair_lbs, ())
        self.repair_timer.start()
