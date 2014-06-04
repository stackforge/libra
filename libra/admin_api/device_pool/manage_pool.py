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
from oslo.config import cfg
from sqlalchemy import func

from libra.common.api.lbaas import Device, PoolBuilding, Vip, db_session
from libra.common.api.lbaas import Counters
from libra.common.json_gearman import JsonJob
from libra.openstack.common import log
import gear

# TODO: Lots of duplication of code here, need to cleanup

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

        self.gear = GearmanWork()  # set up the async gearman

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
            with db_session() as session:
                devices = session.query(Device). \
                    filter(Device.status == 'DELETED').all()

                for device in devices:
                    job_data = {
                        'action': 'DELETE_DEVICE',
                        'name': device.name
                    }
                    self.gear.send_delete_message(job_data)

                counter = session.query(Counters). \
                    filter(Counters.name == 'devices_deleted').first()
                counter.value += len(devices)
                session.commit()
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
                vip_count = session.query(Vip). \
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
                session.query(PoolBuilding). \
                    filter(PoolBuilding.server_id == self.server_id). \
                    delete()
                session.flush()
                dev_count = session.query(Device). \
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
                session.query(PoolBuilding). \
                    filter(PoolBuilding.server_id == self.server_id). \
                    delete()
                session.commit()
        except:
            LOG.exception("Uncaught exception during pool expansion")
        self.start_probe_sched()

    def _build_nodes(self, count):
        job_data = {'action': 'BUILD_DEVICE'}
        for it in range(0, count):
            self.gear.send_create_message(job_data)

    def _build_vips(self, count):
        job_data = {'action': 'BUILD_IP'}
        for it in range(0, count):
            self.gear.send_vips_message(job_data)

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

    class VIPClient(gear.Client):
        def handleWorkComplete(self, packet):
            job = super(GearmanWork.VIPClient, self).handleWorkComplete(packet)
            try:
                if job.msg['response'] == 'FAIL':
                    LOG.error('Pool manager failed to build a vip')
                else:
                    self._add_vip(job.msg)
            except:
                LOG.exception(
                    'Could not add vip to DB, node data: {0}'
                    .format(job.msg)
                )

        def _add_vip(self, data):
            LOG.info('Adding vip {0} to DB'.format(data['ip']))
            vip = Vip()
            vip.ip = int(ipaddress.IPv4Address(unicode(data['ip'])))
            with db_session() as session:
                session.add(vip)
                counter = session.query(Counters). \
                    filter(Counters.name == 'vips_built').first()
                counter.value += 1
                session.commit()

    class DeleteClient(gear.Client):
        def handleWorkComplete(self, packet):
            job = super(GearmanWork.DeleteClient,
                        self).handleWorkComplete(packet)

            if job.msg['response'] == 'FAIL':
                LOG.error(
                    'Pool manager failed to delete a device, removing from DB')

            self._delete_from_db(job.msg)

        def _delete_from_db(self, msg):
            with db_session() as session:
                session.query(Device). \
                    filter(Device.name == msg['name']).delete()
                session.commit()
                LOG.info("Delete device %s" % msg['name'])

    class CreateClient(gear.Client):
        def handleWorkComplete(self, packet):
            job = super(GearmanWork.CreateClient,
                        self).handleWorkComplete(packet)
            try:
                if job.msg['response'] == 'FAIL':
                    LOG.error('Pool manager failed to build a device')
                    if 'name' in job.msg:
                        self._add_bad_node(job.msg)
                else:
                    self._add_node(job.msg)
            except:
                LOG.exception(
                    'Could not add node to DB, node data: {0}'
                    .format(job.msg)
                )

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
                counter = session.query(Counters). \
                    filter(Counters.name == 'devices_built').first()
                counter.value += 1
                session.commit()

        def _add_bad_node(self, data):
            LOG.info(
                "Adding bad device {0} to DB to be deleted" % (data['name']))
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
                counter = session.query(Counters). \
                    filter(Counters.name == 'devices_bad_built').first()
                counter.value += 1
                session.commit()

    def __init__(self):
        self.vip_client = GearmanWork.VIPClient("Vip Client")
        self.delete_client = GearmanWork.DeleteClient("Delete Client")
        self.create_client = GearmanWork.CreateClient("Create Client")

        for x in [self.vip_client, self.create_client, self.delete_client]:
            self._init_client(x)

    def _init_client(self, client):
        client.log = LOG
        for server in cfg.CONF['gearman']['servers']:
            host, port = server.split(':')
            client.addServer(host, port, cfg.CONF['gearman']['ssl_key'],
                             cfg.CONF['gearman']['ssl_cert'],
                             cfg.CONF['gearman']['ssl_ca'])

    def send_delete_message(self, message, name='libra_pool_mgm'):
        self.delete_client.submitJob(JsonJob(name, message))

    def send_vips_message(self, message, name='libra_pool_mgm'):
        self.vip_client.submitJob(JsonJob(name, message))

    def send_create_message(self, message, name='libra_pool_mgm'):
        self.create_client.submitJob(JsonJob(name, message))
