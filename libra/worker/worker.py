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

import gearman.errors
import json
import socket
import time

from libra.common.json_gearman import JSONGearmanWorker
from libra.worker.controller import LBaaSController


class CustomJSONGearmanWorker(JSONGearmanWorker):
    """ Custom class we will use to pass arguments to the Gearman task. """
    logger = None
    driver = None
    args = None


def handler(worker, job):
    """
    Main Gearman worker task.

    This is the function executed by the Gearman worker for incoming requests
    from the Gearman job server. It will be executed once per request. Data
    comes in as a JSON object, and a JSON object is returned in response.
    """
    logger = worker.logger
    driver = worker.driver
    args = worker.args

    # Hide information that should not be logged
    copy = job.data.copy()
    if LBaaSController.OBJ_STORE_TOKEN_FIELD in copy:
        copy[LBaaSController.OBJ_STORE_TOKEN_FIELD] = "*****"

    logger.debug("Received JSON message: %s" % json.dumps(copy))

    controller = LBaaSController(logger, driver, job.data, args.server)
    response = controller.run()

    # Hide information that should not be logged
    copy = response.copy()
    if LBaaSController.OBJ_STORE_TOKEN_FIELD in copy:
        copy[LBaaSController.OBJ_STORE_TOKEN_FIELD] = "*****"

    logger.debug("Return JSON message: %s" % json.dumps(copy))
    return copy


def config_thread(logger, driver, args):
    """ Worker thread function. """
    # Hostname should be a unique value, like UUID
    hostname = socket.gethostname()
    logger.info("[worker] Registering task %s" % hostname)

    server_list = []
    for host_port in args.server:
        host, port = host_port.split(':')
        server_list.append({'host': host,
                            'port': int(port),
                            'keyfile': args.gearman_ssl_key,
                            'certfile': args.gearman_ssl_cert,
                            'ca_certs': args.gearman_ssl_ca,
                            'keepalive': args.gearman_keepalive,
                            'keepcnt': args.gearman_keepcnt,
                            'keepidle': args.gearman_keepidle,
                            'keepintvl': args.gearman_keepintvl})

    worker = CustomJSONGearmanWorker(server_list)
    worker.set_client_id(hostname)
    worker.register_task(hostname, handler)
    worker.logger = logger
    worker.driver = driver
    worker.args = args

    retry = True

    while (retry):
        try:
            worker.work(args.gearman_poll)
        except KeyboardInterrupt:
            retry = False
        except gearman.errors.ServerUnavailable:
            logger.error("[worker] Job server(s) went away. Reconnecting.")
            time.sleep(args.reconnect_sleep)
            retry = True
        except Exception as e:
            logger.critical("[worker] Exception: %s, %s" % (e.__class__, e))
            retry = False

    logger.debug("[worker] Worker process terminated.")
