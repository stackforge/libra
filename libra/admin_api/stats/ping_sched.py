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
from libra.common.api.lbaas import LoadBalancer, Device, Node, db_session
from libra.openstack.common import log as logging
from libra.admin_api.stats.stats_gearman import GearJobs

LOG = logging.getLogger(__name__)


class PingStats(object):

    PING_SECONDS = cfg.CONF['admin_api'].ping_timer_seconds

    def __init__(self, drivers):
        self.drivers = drivers
        self.ping_timer = None
        self.error_limit = cfg.CONF['admin_api']['stats_device_error_limit']
        self.server_id = cfg.CONF['admin_api']['server_id']
        self.number_of_servers = cfg.CONF['admin_api']['number_of_servers']
        self.stats_driver = cfg.CONF['admin_api']['stats_driver']
        LOG.info("Selected stats drivers: %s", self.stats_driver)

        self.start_ping_sched()

    def shutdown(self):
        if self.ping_timer:
            self.ping_timer.cancel()

    def ping_lbs(self):
        # Work out if it is our turn to run
        minute = datetime.now().minute
        if self.server_id != minute % self.number_of_servers:
            LOG.info('Not our turn to run ping check, sleeping')
            self.start_ping_sched()
            return
        pings = 0
        failed = 0
        try:
            pings, failed = self._exec_ping()
        except Exception:
            LOG.exception('Uncaught exception during LB ping')
        # Need to restart timer after every ping cycle
        LOG.info('{pings} loadbalancers pinged, {failed} failed'
                 .format(pings=pings, failed=failed))
        self.start_ping_sched()

    def _exec_ping(self):
        pings = 0
        failed = 0
        node_list = []
        LOG.info('Running ping check')
        with db_session() as session:
            devices = session.query(
                Device.id, Device.name
            ).filter(Device.status == 'ONLINE').all()
            pings = len(devices)
            if pings == 0:
                LOG.info('No LBs to ping')
                return (0, 0)
            for lb in devices:
                node_list.append(lb.name)
            gearman = GearJobs()
            failed_lbs, node_status = gearman.send_pings(node_list)
            failed = len(failed_lbs)
            if failed > self.error_limit:
                LOG.error(
                    'Too many simultaneous Load Balancer Failures.'
                    ' Aborting recovery attempt'
                )
                return pings, failed

            if failed > 0:
                self._send_fails(failed_lbs)

            # Process node status after lb status
            self._update_nodes(node_status)
            session.commit()

        return pings, failed

    def _send_fails(self, failed_lbs):
        with db_session() as session:
            for lb in failed_lbs:
                data = self._get_lb(lb, session)
                if not data:
                    LOG.error(
                        'Device {0} has no Loadbalancer attached'.
                        format(lb)
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
                    instance = driver()
                    LOG.info(
                        'Sending failure of {0} to {1}'.format(
                            lb, instance.__class__.__name__
                        )
                    )
                    instance.send_alert(message, data.id)
            session.commit()

    def _get_lb(self, lb, session):
        lb = session.query(
            LoadBalancer.tenantid, Device.floatingIpAddr, Device.id
        ).join(LoadBalancer.devices).\
            filter(Device.name == lb).first()

        return lb

    def _update_nodes(self, node_status):
        lbids = []
        degraded = []
        failed_nodes = dict()
        repaired_nodes = dict()
        errormsg = dict()
        with db_session() as session:
            for lb, nodes in node_status.iteritems():
                data = self._get_lb(lb, session)
                if not data:
                    LOG.error(
                        'Device {0} has no Loadbalancer attached'.
                        format(lb)
                    )
                    continue

                # Iterate the list of nodes returned from the worker
                # and track any status changes
                for node in nodes:
                    # Get the last known status from the nodes table
                    node_data = session.query(Node).\
                        filter(Node.id == int(node['id'])).first()

                    if node_data is None:
                        LOG.error(
                            'DB error getting node {0} to set status {1}'
                            .format(node['id'], node['status'])
                        )
                        continue

                    # Note all degraded LBs
                    if (node['status'] == 'DOWN' and
                            node_data.lbid not in degraded):
                        degraded.append(node_data.lbid)

                    new_status = None
                    # Compare node status to the workers status
                    if (node['status'] == 'DOWN' and
                            node_data.status == 'ONLINE'):
                        new_status = 'ERROR'
                        if node_data.lbid not in failed_nodes:
                            failed_nodes[node_data.lbid] = []
                        failed_nodes[node_data.lbid].append(node['id'])
                    elif (node['status'] == 'UP' and
                            node_data.status == 'ERROR'):
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
                            'Node status change ID:'\
                            ' {0}, IP: {1}, tenant: {2}'.\
                            format(
                                node_data.lbid,
                                data.floatingIpAddr,
                                data.tenantid
                            )

                    # Change the node status in the node table
                    session.query(Node).\
                        filter(Node.id == int(node['id'])).\
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
                instance = driver()
                LOG.info(
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

        LOG.info('LB ping check timer sleeping for %d seconds', sleeptime)
        self.ping_timer = threading.Timer(sleeptime, self.ping_lbs, ())
        self.ping_timer.start()
