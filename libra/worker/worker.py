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


def handler(worker, job):
    """
    Main Gearman worker task.

    This is the function executed by the Gearman worker for incoming requests
    from the Gearman job server. It will be executed once per request. Data
    comes in as a JSON object, and a JSON object is returned in response.
    """
    logger = worker.logger
    driver = worker.driver

    logger.debug("Received JSON message: %s" % json.dumps(job.data, indent=4))

    controller = LBaaSController(logger, driver, job.data)
    response = controller.run()

    logger.debug("Return JSON message: %s" % json.dumps(response, indent=4))
    return response


def config_manager(logger, driver, servers, reconnect_sleep):
    my_ip = socket.gethostbyname(socket.gethostname())
    task_name = "lbaas-%s" % my_ip
    logger.info("[worker] Registering task %s" % task_name)

    worker = CustomJSONGearmanWorker(servers)
    worker.set_client_id(my_ip)
    worker.register_task(task_name, handler)
    worker.logger = logger
    worker.driver = driver

    retry = True

    while (retry):
        try:
            worker.work()
        except KeyboardInterrupt:
            retry = False
        except gearman.errors.ServerUnavailable:
            logger.error("[worker] Job server(s) went away. Reconnecting.")
            time.sleep(reconnect_sleep)
            retry = True
        except Exception as e:
            logger.critical("[worker] Exception: %s, %s" % (e.__class__, e))
            retry = False

    logger.debug("[worker] Worker process terminated.")
