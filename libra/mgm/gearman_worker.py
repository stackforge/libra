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

from libra import gear #TODO
import json
import socket

from oslo.config import cfg
from libra.mgm.controllers.root import PoolMgmController
from libra.openstack.common import log


LOG = log.getLogger(__name__)


def handler(job):
    LOG.debug("Received JSON message: {0}".format(json.dumps(job.arguments)))
    controller = PoolMgmController(json.loads(job.arguments))
    response = controller.run()
    LOG.debug("Return JSON message: {0}".format(json.dumps(response)))
    job.sendWorkComplete(json.dumps(response))


def worker_thread():
    LOG.info("Registering task libra_pool_mgm")
    hostname = socket.gethostname()

    worker = gear.Worker(hostname)

    for host_port in cfg.CONF['gearman']['servers']:
        host, port = host_port.split(':')
        worker.addServer(host,
                         int(port),
                         cfg.CONF['gearman']['ssl_key'],
                         cfg.CONF['gearman']['ssl_cert'],
                         cfg.CONF['gearman']['ssl_ca'])
    worker.registerFunction('libra_pool_mgm')
    worker.logger = LOG

    retry = True

    while retry:
        try:
            job = worker.getJob()
            handler(job)
        except KeyboardInterrupt:
            retry = False
        except Exception as e:
            LOG.exception("Exception in pool manager worker: %s, %s"
                          % (e.__class__, e))
            retry = False

    LOG.debug("Pool manager process terminated.")
