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
from libra.admin_api.model.lbaas import Device, db_session
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

        with db_session() as session:
            dev_count = session.query(Device).\
                filter(Device.status == 'OFFLINE').count()

            #TODO: have a table to count currently building nodes and check it

            if dev_count < self.args.node_pool_size:
                self._build_nodes(self.args.node_pool_size - dev_count)
            #TODO: reset count in new table
            session.commit()

    def _build_nodes(self, count):
        message = []
        it = 0
        job_data = {'action': 'BUILD_DEVICE'}
        while it < count:
            message.append(dict(task='libra_pool_mgm', data=job_data))
        #TODO: Catch exception
        status, response = self._send_multi_message(message)

    def _send_multi_message(self, message):
        job_status = self.gearman_client.submit_multiple_jobs(
            message, background=False, wait_until_complete=True,
            max_retries=10, poll_timeout=120.0
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
            self._add_node(status)
        self.logger.info(
            '{nodes} devices built and added to pool'.format(nodes=built_count)
        )

    def _add_node(status):
        pass

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
