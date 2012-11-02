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

from libra.worker.controller import LBaaSController


def config_manager(worker, job):
    """
    Main Gearman worker task.

    This is the function executed by the Gearman worker for incoming requests
    from the Gearman job server. It will be executed once per request. Data
    comes in as a JSON object, and a JSON object is returned in response.
    """
    logger = worker.logger
    driver = worker.driver

    logger.debug("Entered worker task")
    logger.debug("Received JSON message: %s" % json.dumps(job.data, indent=4))

    controller = LBaaSController(logger, driver, job.data)
    response = controller.run()

    logger.debug("Return JSON message: %s" % json.dumps(response, indent=4))
    return response
