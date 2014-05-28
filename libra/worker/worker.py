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

# import gearman.errors
import json
import socket
# import time
import gear
from oslo.config import cfg

# from libra.common.json_gearman import JSONGearmanWorker
from libra.worker.controller import LBaaSController
from libra.openstack.common import log


LOG = log.getLogger(__name__)


# class CustomJSONGearmanWorker(JSONGearmanWorker):

class CustomJSONGearmanWorker(gear.Worker):
    """ Custom class we will use to pass arguments to the Gearman task. """
    driver = None


def handler(worker, job):
    """
    Main Gearman worker task.

    This is the function executed by the Gearman worker for incoming requests
    from the Gearman job server. It will be executed once per request. Data
    comes in as a JSON object, and a JSON object is returned in response.
    """
    driver = worker.driver

    # Hide information that should not be logged

    # copy = job.data.copy()----commented by min
    copy = json.loads(job.arguments)
    if LBaaSController.OBJ_STORE_TOKEN_FIELD in copy:
        copy[LBaaSController.OBJ_STORE_TOKEN_FIELD] = "*****"

    LOG.debug("Received JSON message: %s" % json.dumps(copy))

    controller = LBaaSController(driver, json.loads(job.arguments))
    response = controller.run()

    # Hide information that should not be logged
    copy = response.copy()
    if LBaaSController.OBJ_STORE_TOKEN_FIELD in copy:
        copy[LBaaSController.OBJ_STORE_TOKEN_FIELD] = "*****"

    LOG.debug("Return JSON message: %s" % json.dumps(copy))
    # return copy---commented by min
    job.sendWorkComplete(json.dumps(copy))


def config_thread(driver):
    """ Worker thread function. """
    # Hostname should be a unique value, like UUID
    hostname = socket.gethostname()
    LOG.info("Registering task %s" % hostname)

    # worker = gear.Worker(hostname)
    worker = CustomJSONGearmanWorker(hostname)

    # server_list = []---commented by min
    for host_port in cfg.CONF['gearman']['servers']:
        host, port = host_port.split(':')
        worker.addServer(host, port, cfg.CONF['gearman']['ssl_key'],
                         cfg.CONF['gearman']['ssl_cert'],
                         cfg.CONF['gearman']['ssl_ca'])
        # the following code is commented by min
        # server_list.append({'host': host,
        #                     'port': int(port),
        #                     'keyfile': cfg.CONF['gearman']['ssl_key'],
        #                     'certfile': cfg.CONF['gearman']['ssl_cert'],
        #                     'ca_certs': cfg.CONF['gearman']['ssl_ca'],
        #                     'keepalive': cfg.CONF['gearman']['keepalive'],
        #                     'keepcnt': cfg.CONF['gearman']['keepcnt'],
        #                     'keepidle': cfg.CONF['gearman']['keepidle'],
        #                     'keepintvl': cfg.CONF['gearman']['keepintvl']})

    # worker = CustomJSONGearmanWorker(server_list)
    # worker.set_client_id(hostname)
    # worker.register_task(hostname, handler)
    # worker.logger = LOG
    # worker.driver = driver

    # this part is changed for replacing gearman with gear

    worker.registerFunction(hostname)
    worker.log = LOG
    worker .driver = driver

    # while (retry):
    #    try:
    #       worker.work(cfg.CONF['gearman']['poll'])
    # except KeyboardInterrupt:
    #    retry = False
    # except gearman.errors.ServerUnavailable:
    #   LOG.error("Job server(s) went away. Reconnecting.")
    # time.sleep(cfg.CONF['gearman']['reconnect_sleep'])
    # retry = True
    # except Exception as e:
    #     LOG.critical("Exception: %s, %s" % (e.__class__, e))
    #    retry = False

    retry = True
    while retry:
        try:
            job = worker.getJob()
            handler(worker, job)
            # job.sendWorkComplete(cfg.CONF['gearman']['poll'])
        except KeyboardInterrupt:
            retry = False
        except Exception as e:
            LOG.critical("Exception: %s, %s" % (e.__class__, e))
            retry = False
    # end of change
    LOG.debug("Worker process terminated.")
