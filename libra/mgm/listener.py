#!/usr/bin/env python
# Copyright 2012 Hewlett-Packard Development Company, L.P.
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

import json
import socket

from libra.common.json_gearman import JSONGearmanWorker
from libra.common.faults import BadRequest


class Listener(object):
    def __init__(self, logger):
        self.logger = logger

    def run(self):
        my_ip = socket.gethostbyname(socket.gethostname())
        task_name = "lbaas-mgm-%s" % my_ip
        self.logger.debug("Registering task %s" % task_name)

        worker = JSONGearmanWorker(['localhost:4730'])
        worker.set_client_id(my_ip)
        worker.register_task(task_name, self.task)

    def task(self, worker, job):
        data = json.loads(job.data)

        if 'command' not in data:
            return BadRequest("Missing 'command' element").to_json()

        command = data['command']
        self.logger.debug('Command: {cmd}'.format(cmd=command))
        if command == 'get':
            self.logger.debug('Get one node from pool')
        else:
            return BadRequest("Invalid command").to_json()

        return data
