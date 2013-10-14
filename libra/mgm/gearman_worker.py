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

import gearman.errors
import json
import socket
import time

from oslo.config import cfg

from libra.common.json_gearman import JSONGearmanWorker
from libra.mgm.controllers.root import PoolMgmController


def handler(worker, job):
    logger = worker.logger
    logger.debug("Received JSON message: {0}".format(json.dumps(job.data)))
    controller = PoolMgmController(logger, job.data)
    response = controller.run()
    logger.debug("Return JSON message: {0}".format(json.dumps(response)))
    return response


def worker_thread(logger):
    logger.info("Registering task libra_pool_mgm")
    hostname = socket.gethostname()

    server_list = []
    for host_port in cfg.CONF['gearman']['servers']:
        host, port = host_port.split(':')
        server_list.append({'host': host,
                            'port': int(port),
                            'keyfile': cfg.CONF['gearman']['ssl_key'],
                            'certfile': cfg.CONF['gearman']['ssl_cert'],
                            'ca_certs': cfg.CONF['gearman']['ssl_ca'],
                            'keepalive': cfg.CONF['gearman']['keepalive'],
                            'keepcnt': cfg.CONF['gearman']['keepcnt'],
                            'keepidle': cfg.CONF['gearman']['keepidle'],
                            'keepintvl': cfg.CONF['gearman']['keepintvl']})
    worker = JSONGearmanWorker(server_list)

    worker.set_client_id(hostname)
    worker.register_task('libra_pool_mgm', handler)
    worker.logger = logger

    retry = True

    while (retry):
        try:
            worker.work(cfg.CONF['gearman']['poll'])
        except KeyboardInterrupt:
            retry = False
        except gearman.errors.ServerUnavailable:
            logger.error("Job server(s) went away. Reconnecting.")
            time.sleep(cfg.CONF['gearman']['reconnect_sleep'])
            retry = True
        except Exception:
            logger.exception("Exception in worker")
            retry = False

    logger.debug("Pool manager process terminated.")
