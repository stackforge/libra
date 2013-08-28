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
from libra.common.json_gearman import JSONGearmanClient
from gearman.constants import JOB_UNKNOWN
from sqlalchemy import func
from libra.admin_api.model.lbaas import Device, PoolBuilding, db_session


class Pool(object):

    DELETE_SECONDS = 05
    PROBE_SECONDS = 30

    def __init__(self, logger, args):
        self.logger = logger
        self.args = args
        self.probe_timer = None
        self.delete_timer = None

        if all([args.gearman_ssl_key, args.gearman_ssl_cert,
                args.gearman_ssl_ca]):
            # Use SSL connections to each Gearman job server.
            ssl_server_list = []
            for server in args.gearman:
                ghost, gport = server.split(':')
                ssl_server_list.append({'host': ghost,
                                        'port': int(gport),
                                        'keyfile': args.gearman_ssl_key,
                                        'certfile': args.gearman_ssl_cert,
                                        'ca_certs': args.gearman_ssl_ca})
            self.gearman_client = JSONGearmanClient(ssl_server_list)
        else:
            self.gearman_client = JSONGearmanClient(args.gearman)

        self.start_delete_sched()
        self.start_probe_sched()

    def shutdown(self):
        if self.probe_timer:
            self.probe_timer.cancel()
        if self.delete_timer:
            self.delete_time.cancel()

    def delete_devices(self):
        """ Searches for all devices in the DELETED state and removes them """
        minute = datetime.now().minute
        if self.args.server_id != minute % self.args.number_of_servers:
            self.logger.info('Not our turn to run delete check, sleeping')
            self.start_delete_sched()
            return
        self.logger.info('Running device delete check')
        try:
            with db_session() as session:
                devices = session.query(Device).\
                    filter(Device.status == 'DELETED').all()

                for device in devices:
                    if self._send_delete_message(device.name):
                        session.query(Device).\
                            filer(Device.name == device.name).delete()

                session.commit()
        except:
            self.logger.exception("Exception when deleting devices")

        self.start_delete_sched()

    def _send_delete_message(self, name):
        message = {
            'action': 'DELETE_DEVICE',
            'name': name
        }
        job_status = self.gearman_client.submit_job(
            'libra_pool_mgm', message, background=False,
            wait_until_complete=True, max_retries=10, poll_timeout=30.0
        )
        if job_status.state == JOB_UNKNOWN:
            self.logger.error('Gearman Job server fail')
            return False
        if job_status.timed_out:
            self.logger.error('Gearman timeout whilst deleting device')
            return False
        if job_status.result['response'] == 'FAIL':
            self.logger.error('Pool manager failed to delete a device')
            return False

        return True

    def probe_devices(self):
        minute = datetime.now().minute
        if self.args.server_id != minute % self.args.number_of_servers:
            self.logger.info('Not our turn to run probe check, sleeping')
            self.start_probe_sched()
            return
        self.logger.info('Running device count probe check')
        try:
            with db_session() as session:
                # Double check we have no outstanding builds assigned to us
                session.query(PoolBuilding).\
                    filter(PoolBuilding.server_id == self.args.server_id).\
                    delete()
                session.flush()
                dev_count = session.query(Device).\
                    filter(Device.status == 'OFFLINE').count()
                if dev_count >= self.args.node_pool_size:
                    self.logger.info("Enough devices exist, no work to do")
                    session.commit()
                    self.start_probe_sched()
                    return

                build_count = self.args.node_pool_size - dev_count
                built = session.query(func.sum(PoolBuilding.qty)).first()
                if not built[0]:
                    built = 0
                else:
                    built = built[0]
                if build_count - built <= 0:
                    self.logger.info(
                        "Other servers are building enough nodes"
                    )
                    session.commit()
                    self.start_probe_sched()
                    return
                build_count -= built
                building = PoolBuilding()
                building.server_id = self.args.server_id
                building.qty = build_count
                session.add(building)
                session.commit()

            # Closed the DB session because we don't want it hanging around
            # for a long time locking tables
            self._build_nodes(build_count)
            with db_session() as session:
                session.query(PoolBuilding).\
                    filter(PoolBuilding.server_id == self.args.server_id).\
                    delete()
                session.commit()
        except:
            self.logger.exception("Uncaught exception during pool expansion")
        self.start_probe_sched()

    def _build_nodes(self, count):
        message = []
        it = 0
        job_data = {'action': 'BUILD_DEVICE'}
        while it < count:
            message.append(dict(task='libra_pool_mgm', data=job_data))
            it += 1
        self._send_multi_message(message)

    def _send_multi_message(self, message):
        # TODO: make this gearman part more async, not wait for all builds
        self.logger.info("Sending {0} gearman messages".format(len(message)))
        job_status = self.gearman_client.submit_multiple_jobs(
            message, background=False, wait_until_complete=True,
            max_retries=10, poll_timeout=3600.0
        )
        built_count = 0
        for status in job_status:
            if status.state == JOB_UNKNOWN:
                self.logger.error('Gearman Job server fail')
                continue
            if status.timed_out:
                self.logger.error('Gearman timeout whilst building device')
                continue
            if status.result['response'] == 'FAIL':
                self.logger.error('Pool manager failed to build a device')
                continue

            built_count += 1
            try:
                self._add_node(status.result)
            except:
                self.logger.exception(
                    'Could not add node to DB, node data: {0}'
                    .format(status.result)
                )
        self.logger.info(
            '{nodes} devices built and added to pool'.format(nodes=built_count)
        )

    def _add_node(self, data):
        self.logger.info('Adding device {0} to DB'.format(data['name']))
        device = Device()
        device.name = data['name']
        device.publicIpAddr = data['addr']
        # TODO: kill this field, make things use publicIpAddr instead
        device.floatingIpAddr = data['addr']
        device.az = data['az']
        device.type = data['type']
        device.status = 'OFFLINE'
        device.created = None
        with db_session() as session:
            session.add(device)
            session.commit()

    def start_probe_sched(self):
        seconds = datetime.now().second
        if seconds < self.PROBE_SECONDS:
            sleeptime = self.PROBE_SECONDS - seconds
        else:
            sleeptime = 60 - (seconds - self.PROBE_SECONDS)

        self.logger.info('Pool probe check timer sleeping for {secs} seconds'
                         .format(secs=sleeptime))
        self.probe_timer = threading.Timer(sleeptime, self.probe_devices, ())
        self.probe_timer.start()

    def start_delete_sched(self):
        seconds = datetime.now().second
        if seconds < self.DELETE_SECONDS:
            sleeptime = self.DELETE_SECONDS - seconds
        else:
            sleeptime = 60 - (seconds - self.DELETE_SECONDS)

        self.logger.info('Pool delete check timer sleeping for {secs} seconds'
                         .format(secs=sleeptime))
        self.delete_timer = threading.Timer(sleeptime, self.delete_devices, ())
        self.delete_timer.start()
