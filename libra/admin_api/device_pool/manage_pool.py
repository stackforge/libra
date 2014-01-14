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

import ipaddress
import threading

from datetime import datetime
from gearman.constants import JOB_UNKNOWN
from oslo.config import cfg
from sqlalchemy import func

from libra.common.api.lbaas import Device, PoolBuilding, Vip, db_session
from libra.common.api.lbaas import Counters
from libra.common.json_gearman import JSONGearmanClient
from libra.openstack.common import log

#TODO: Lots of duplication of code here, need to cleanup

LOG = log.getLogger(__name__)


class Pool(object):

    DELETE_SECONDS = cfg.CONF['admin_api'].delete_timer_seconds
    PROBE_SECONDS = cfg.CONF['admin_api'].probe_timer_seconds
    VIPS_SECONDS = cfg.CONF['admin_api'].vips_timer_seconds

    def __init__(self):
        self.probe_timer = None
        self.delete_timer = None
        self.vips_time = None
        self.server_id = cfg.CONF['admin_api']['server_id']
        self.number_of_servers = cfg.CONF['admin_api']['number_of_servers']
        self.vip_pool_size = cfg.CONF['admin_api']['vip_pool_size']
        self.node_pool_size = cfg.CONF['admin_api']['node_pool_size']

        self.start_delete_sched()
        self.start_probe_sched()
        self.start_vips_sched()

    def shutdown(self):
        if self.probe_timer:
            self.probe_timer.cancel()
        if self.delete_timer:
            self.delete_timer.cancel()
        if self.vips_timer:
            self.vips_timer.cancel()

    def delete_devices(self):
        """ Searches for all devices in the DELETED state and removes them """
        minute = datetime.now().minute
        if self.server_id != minute % self.number_of_servers:
            LOG.info('Not our turn to run delete check, sleeping')
            self.start_delete_sched()
            return
        LOG.info('Running device delete check')
        try:
            message = []
            with db_session() as session:
                devices = session.query(Device).\
                    filter(Device.status == 'DELETED').all()

                for device in devices:
                    job_data = {
                        'action': 'DELETE_DEVICE',
                        'name': device.name
                    }
                    message.append(dict(task='libra_pool_mgm', data=job_data))

                counter = session.query(Counters).\
                    filter(Counters.name == 'devices_deleted').first()
                counter.value += len(devices)
                session.commit()
            if not message:
                LOG.info("No devices to delete")
            else:
                gear = GearmanWork()
                gear.send_delete_message(message)
        except:
            LOG.exception("Exception when deleting devices")

        self.start_delete_sched()

    def probe_vips(self):
        minute = datetime.now().minute
        if self.server_id != minute % self.number_of_servers:
            LOG.info('Not our turn to run vips check, sleeping')
            self.start_vips_sched()
            return
        LOG.info('Running vips count probe check')
        try:
            with db_session() as session:
                NULL = None  # For pep8
                vip_count = session.query(Vip).\
                    filter(Vip.device == NULL).count()
                if vip_count >= self.vip_pool_size:
                    LOG.info("Enough vips exist, no work to do")
                    session.commit()
                    self.start_vips_sched()
                    return

                build_count = self.vip_pool_size - vip_count
                self._build_vips(build_count)
        except:
            LOG.exception(
                "Uncaught exception during vip pool expansion"
            )
        self.start_vips_sched()

    def probe_devices(self):
        minute = datetime.now().minute
        if self.server_id != minute % self.number_of_servers:
            LOG.info('Not our turn to run probe check, sleeping')
            self.start_probe_sched()
            return
        LOG.info('Running device count probe check')
        try:
            with db_session() as session:
                # Double check we have no outstanding builds assigned to us
                session.query(PoolBuilding).\
                    filter(PoolBuilding.server_id == self.server_id).\
                    delete()
                session.flush()
                dev_count = session.query(Device).\
                    filter(Device.status == 'OFFLINE').count()
                if dev_count >= self.node_pool_size:
                    LOG.info("Enough devices exist, no work to do")
                    session.commit()
                    self.start_probe_sched()
                    return

                build_count = self.node_pool_size - dev_count
                built = session.query(func.sum(PoolBuilding.qty)).first()
                if not built[0]:
                    built = 0
                else:
                    built = built[0]
                if build_count - built <= 0:
                    LOG.info(
                        "Other servers are building enough nodes"
                    )
                    session.commit()
                    self.start_probe_sched()
                    return
                build_count -= built
                building = PoolBuilding()
                building.server_id = self.server_id
                building.qty = build_count
                session.add(building)
                session.commit()

            # Closed the DB session because we don't want it hanging around
            # for a long time locking tables
            self._build_nodes(build_count)
            with db_session() as session:
                session.query(PoolBuilding).\
                    filter(PoolBuilding.server_id == self.server_id).\
                    delete()
                session.commit()
        except:
            LOG.exception("Uncaught exception during pool expansion")
        self.start_probe_sched()

    def _build_nodes(self, count):
        message = []
        it = 0
        job_data = {'action': 'BUILD_DEVICE'}
        while it < count:
            message.append(dict(task='libra_pool_mgm', data=job_data))
            it += 1
        gear = GearmanWork()
        gear.send_create_message(message)

    def _build_vips(self, count):
        message = []
        it = 0
        job_data = {'action': 'BUILD_IP'}
        while it < count:
            message.append(dict(task='libra_pool_mgm', data=job_data))
            it += 1
        gear = GearmanWork()
        gear.send_vips_message(message)

    def start_probe_sched(self):
        seconds = datetime.now().second
        if seconds < self.PROBE_SECONDS:
            sleeptime = self.PROBE_SECONDS - seconds
        else:
            sleeptime = 60 - (seconds - self.PROBE_SECONDS)

        LOG.info('Pool probe check timer sleeping for %d seconds', sleeptime)
        self.probe_timer = threading.Timer(sleeptime, self.probe_devices, ())
        self.probe_timer.start()

    def start_vips_sched(self):
        seconds = datetime.now().second
        if seconds < self.VIPS_SECONDS:
            sleeptime = self.VIPS_SECONDS - seconds
        else:
            sleeptime = 60 - (seconds - self.VIPS_SECONDS)

        LOG.info('Pool vips check timer sleeping for %d seconds', sleeptime)
        self.vips_timer = threading.Timer(sleeptime, self.probe_vips, ())
        self.vips_timer.start()

    def start_delete_sched(self):
        seconds = datetime.now().second
        if seconds < self.DELETE_SECONDS:
            sleeptime = self.DELETE_SECONDS - seconds
        else:
            sleeptime = 60 - (seconds - self.DELETE_SECONDS)

        LOG.info('Pool delete check timer sleeping for %d seconds', sleeptime)
        self.delete_timer = threading.Timer(sleeptime, self.delete_devices, ())
        self.delete_timer.start()


class GearmanWork(object):

    def __init__(self):
        server_list = []
        for server in cfg.CONF['gearman']['servers']:
            host, port = server.split(':')
            server_list.append({'host': host,
                                'port': int(port),
                                'keyfile': cfg.CONF['gearman']['ssl_key'],
                                'certfile': cfg.CONF['gearman']['ssl_cert'],
                                'ca_certs': cfg.CONF['gearman']['ssl_ca'],
                                'keepalive': cfg.CONF['gearman']['keepalive'],
                                'keepcnt': cfg.CONF['gearman']['keepcnt'],
                                'keepidle': cfg.CONF['gearman']['keepidle'],
                                'keepintvl': cfg.CONF['gearman']['keepintvl']
                                })
        self.gearman_client = JSONGearmanClient(server_list)

    def send_delete_message(self, message):
        LOG.info("Sending %d gearman messages", len(message))
        job_status = self.gearman_client.submit_multiple_jobs(
            message, background=False, wait_until_complete=True,
            max_retries=10, poll_timeout=30.0
        )
        delete_count = 0
        for status in job_status:
            if status.state == JOB_UNKNOWN:
                LOG.error('Gearman Job server fail')
                continue
            if status.timed_out:
                LOG.error('Gearman timeout whilst deleting device')
                continue
            if status.result['response'] == 'FAIL':
                LOG.error(
                    'Pool manager failed to delete a device, removing from DB'
                )

            delete_count += 1
            with db_session() as session:
                session.query(Device).\
                    filter(Device.name == status.result['name']).delete()
                session.commit()

        LOG.info('%d freed devices delete from pool', delete_count)

    def send_vips_message(self, message):
        # TODO: make this gearman part more async, not wait for all builds
        LOG.info("Sending %d gearman messages", len(message))
        job_status = self.gearman_client.submit_multiple_jobs(
            message, background=False, wait_until_complete=True,
            max_retries=10, poll_timeout=3600.0
        )
        built_count = 0
        for status in job_status:
            if status.state == JOB_UNKNOWN:
                LOG.error('Gearman Job server fail')
                continue
            if status.timed_out:
                LOG.error('Gearman timeout whilst building vip')
                continue
            if status.result['response'] == 'FAIL':
                LOG.error('Pool manager failed to build a vip')
                continue

            built_count += 1
            try:
                self._add_vip(status.result)
            except:
                LOG.exception(
                    'Could not add vip to DB, node data: {0}'
                    .format(status.result)
                )
        LOG.info(
            '{vips} vips built and added to pool'.format(vips=built_count)
        )

    def send_create_message(self, message):
        # TODO: make this gearman part more async, not wait for all builds
        LOG.info("Sending {0} gearman messages".format(len(message)))
        job_status = self.gearman_client.submit_multiple_jobs(
            message, background=False, wait_until_complete=True,
            max_retries=10, poll_timeout=3600.0
        )
        built_count = 0
        for status in job_status:
            if status.state == JOB_UNKNOWN:
                LOG.error('Gearman Job server fail')
                continue
            if status.timed_out:
                LOG.error('Gearman timeout whilst building device')
                continue
            if status.result['response'] == 'FAIL':
                LOG.error('Pool manager failed to build a device')
                if 'name' in status.result:
                    self._add_bad_node(status.result)
                continue

            built_count += 1
            try:
                self._add_node(status.result)
            except:
                LOG.exception(
                    'Could not add node to DB, node data: {0}'
                    .format(status.result)
                )
        LOG.info(
            '{nodes} devices built and added to pool'.format(nodes=built_count)
        )

    def _add_vip(self, data):
        LOG.info('Adding vip {0} to DB'.format(data['ip']))
        vip = Vip()
        vip.ip = int(ipaddress.IPv4Address(unicode(data['ip'])))
        with db_session() as session:
            session.add(vip)
            counter = session.query(Counters).\
                filter(Counters.name == 'vips_built').first()
            counter.value += 1
            session.commit()

    def _add_node(self, data):
        LOG.info('Adding device {0} to DB'.format(data['name']))
        device = Device()
        device.name = data['name']
        device.publicIpAddr = data['addr']
        # TODO: kill this field, make things use publicIpAddr instead
        device.floatingIpAddr = data['addr']
        device.az = data['az']
        device.type = data['type']
        device.pingCount = 0
        device.status = 'OFFLINE'
        device.created = None
        with db_session() as session:
            session.add(device)
            counter = session.query(Counters).\
                filter(Counters.name == 'devices_built').first()
            counter.value += 1
            session.commit()

    def _add_bad_node(self, data):
        LOG.info(
            'Adding bad device {0} to DB to be deleted'.format(data['name'])
        )
        device = Device()
        device.name = data['name']
        device.publicIpAddr = data['addr']
        # TODO: kill this field, make things use publicIpAddr instead
        device.floatingIpAddr = data['addr']
        device.az = data['az']
        device.type = data['type']
        device.pingCount = 0
        device.status = 'DELETED'
        device.created = None
        with db_session() as session:
            session.add(device)
            counter = session.query(Counters).\
                filter(Counters.name == 'devices_bad_built').first()
            counter.value += 1
            session.commit()
