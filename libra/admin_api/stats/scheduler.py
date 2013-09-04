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
from libra.admin_api.model.lbaas import LoadBalancer, Device, Node, db_session
from libra.admin_api.stats.stats_gearman import GearJobs


class NodeNotFound(Exception):
    pass


class Stats(object):

    PING_SECONDS = 15
    REPAIR_SECONDS = 45

    def __init__(self, logger, args, drivers):
        self.logger = logger
        self.args = args
        self.drivers = drivers
        self.ping_timer = None
        self.repair_timer = None

        signal.signal(signal.SIGINT, self.exit_handler)
        signal.signal(signal.SIGTERM, self.exit_handler)
        logger.info("Selected stats drivers: {0}".format(args.stats_driver))

        self.start_ping_sched()
        self.start_repair_sched()

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
            self.logger.info('Not our turn to run repair check, sleeping')
            self.start_repair_sched()
            return
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
            return
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
            failed_lbs, node_status = gearman.send_pings(node_list)
            failed = len(failed_lbs)
            if failed > 0:
                self._send_fails(failed_lbs, session)
            session.commit()

            # Process node status after lb status
            self._update_nodes(node_status, session)

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
            repaired_lbs, node_status = gearman.send_repair(node_list)
            repaired = len(repaired_lbs)
            if repaired > 0:
                self._send_repair(repaired_lbs, session)
            session.commit()

            # Process node status after lb status
            self._update_nodes(node_status, session)

        return tested, repaired

    def _send_fails(self, failed_lbs, session):
        for lb in failed_lbs:
            data = self._get_lb(lb, session)
            if not data:
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
                        lb, instance.__class__.__name__
                    )
                )
                instance.send_alert(message, data.id)

    def _send_repair(self, repaired_nodes, session):
        for lb in repaired_nodes:
            data = self._get_lb(lb, session)
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
                        lb, instance.__class__.__name__
                    )
                )
                instance.send_repair(message, data.id)

    def _get_lb(self, lb, session):
        lb = session.query(
            LoadBalancer.tenantid, Device.floatingIpAddr, Device.id
        ).join(LoadBalancer.devices).\
            filter(Device.name == lb).first()

        return lb

    def _update_nodes(self, node_status, session):
        lbids = []
        degraded = []
        failed_nodes = dict()
        repaired_nodes = dict()
        errormsg = dict()
        for lb, nodes in node_status.iteritems():
            data = self._get_lb(lb, session)
            if not data:
                self.logger.error(
                    'Device {0} has no Loadbalancer attached'.
                    format(lb)
                )
                continue

            # Iterate the list of nodes returned from the worker
            # and track any status changes
            for node in nodes:
                # Get the last known status from the nodes table
                node_data = session.query(Node).\
                    filter(Node.id == node['id']).first()

                # Note all degraded LBs
                if (node['status'] == 'DOWN' and
                        node_data.lbid not in degraded):
                    degraded.append(node_data.lbid)

                new_status = None
                # Compare node status to the workers status
                if (node['status'] == 'DOWN' and node_data.status == 'ONLINE'):
                    new_status = 'ERROR'
                    if node_data.lbid not in failed_nodes:
                        failed_nodes[node_data.lbid] = []
                    failed_nodes[node_data.lbid].append(node['id'])
                elif (node['status'] == 'UP' and node_data.status == 'ERROR'):
                    new_status = 'ONLINE'
                    if node_data.lbid not in repaired_nodes:
                        repaired_nodes[node_data.lbid] = []
                    repaired_nodes[node_data.lbid].append(node['id'])
                else:
                    # No change
                    continue

                # Note all LBs with node status changes
                if node_data.lbid not in lbids:
                    lbids.append(node_data.lbid)
                    errormsg[node_data.lbid] =\
                        'Node status change ID: {0}, IP: {1}, tenant: {2}'.\
                        format(
                            node_data.lbid, data.floatingIpAddr, data.tenantid
                        )

                # Change the node status in the node table
                session.query(Node).\
                    filter(Node.id == node['id']).\
                    update({"status": new_status},
                           synchronize_session='fetch')
                session.flush()

            session.commit()

        # Generate a status message per LB for the alert.
        for lbid in lbids:
            message = errormsg[lbid]
            if lbid in failed_nodes:
                message += ' failed:'
                message += ','.join(str(x) for x in failed_nodes[lbid])
                message += '\n'

            if lbid in repaired_nodes:
                message += ' repaired: '
                message += ','.join(str(x) for x in repaired_nodes[lbid])

            # Send the LB node change alert
            if lbid in degraded:
                is_degraded = True
            else:
                is_degraded = False
            for driver in self.drivers:
                instance = driver(self.logger, self.args)
                self.logger.info(
                    'Sending change of node status on LB {0} to {1}'.format(
                        lbid, instance.__class__.__name__)
                )

                try:
                    instance.send_node_change(message, lbid, is_degraded)
                except NotImplementedError:
                    pass

    def start_ping_sched(self):
        # Always try to hit the expected second mark for pings
        seconds = datetime.now().second
        if seconds < self.PING_SECONDS:
            sleeptime = self.PING_SECONDS - seconds
        else:
            sleeptime = 60 - (seconds - self.PING_SECONDS)

        self.logger.info('LB ping check timer sleeping for {secs} seconds'
                         .format(secs=sleeptime))
        self.ping_timer = threading.Timer(sleeptime, self.ping_lbs, ())
        self.ping_timer.start()

    def start_repair_sched(self):
        # Always try to hit the expected second mark for repairs
        seconds = datetime.now().second
        if seconds < self.REPAIR_SECONDS:
            sleeptime = self.REPAIR_SECONDS - seconds
        else:
            sleeptime = 60 - (seconds - self.REPAIR_SECONDS)

        self.logger.info('LB repair check timer sleeping for {secs} seconds'
                         .format(secs=sleeptime))
        self.repair_timer = threading.Timer(sleeptime, self.repair_lbs, ())
        self.repair_timer.start()
