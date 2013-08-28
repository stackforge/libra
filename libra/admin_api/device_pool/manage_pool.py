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
from gearman.constants import JOB_UNKNOWN
from libra.admin_api.model.lbaas import Device, PoolBuilding, db_session
# TODO: move sig handler to main thread so it can cycle through classes to
# terminate


class Pool(object):

    PROBE_SECONDS = 30

    def __init__(self, logger, args):
        self.logger = logger
        self.args = args
        self.probe_timer = None

        self.start_pool_sched()

    def shutdown(self):
        if self.probe_timer:
            self.probe_timer.cancel()

    def probe_devices(self):
        minute = datetime.now().minute
        if self.args.server_id != minute % self.args.number_of_servers:
            self.logger.info('Not our turn to run probe check, sleeping')
            self.start_probe_sched()
            return
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
                built = session.query(PoolBuilding.qty).sum()
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
        status, response = self._send_multi_message(message)

    def _send_multi_message(self, message):
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

        self.logger.info('Pool probe check timer sleep for {secs} seconds'
                         .format(secs=sleeptime))
        self.probe_timer = threading.Timer(sleeptime, self.probe_devices, ())
        self.probe_timer.start()
