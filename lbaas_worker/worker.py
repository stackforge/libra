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

import argparse
import daemon
import json
import lockfile
import logging
import socket
from json_gearman import JSONGearmanWorker

from lbaas_worker.faults import BadRequest


def lbaas_task(worker, job):
    """ Main Gearman worker task.  """

    # Turn string into JSON object
    data = json.loads(job.data)

    lb_name = data['name']
    logging.info("LB name: %s" % lb_name)

    if 'nodes' not in data:
        return BadRequest("Missing 'nodes' element").to_json()

    for lb_node in data['nodes']:
        port, address, status = None, None, None

        if 'port' in lb_node:
            port = lb_node['port']
        else:
            return BadRequest("Missing 'port' element.").to_json()

        if 'address' in lb_node:
            address = lb_node['address']
        else:
            return BadRequest("Missing 'address' element.").to_json()

        if 'status' in lb_node:
            status = lb_node['status']

        logging.info("LB node: %s:%s - %s" % (address, port, status))
        lb_node['status'] = 'ACTIVE'

    # Return the same JSON object, but with status fields set.
    return data


class Server(object):
    """
    Encapsulates server activity so we can run it in either daemon or
    non-daemon mode.
    """

    def __init__(self, logger):
        self.logger = logger

    def main(self):
        self.logger.info("Getting IP")
        my_ip = socket.gethostbyname(socket.gethostname())
        task_name = "lbaas-%s" % my_ip
        self.logger.debug("Registering task %s" % task_name)

        worker = JSONGearmanWorker(['localhost:4730'])
        worker.set_client_id(my_ip)
        worker.register_task(task_name, lbaas_task)

        try:
            worker.work()
        except KeyboardInterrupt:
            self.logger.debug("Quitting")
        except Exception as e:
            self.logger.critical("Exception: %s, %s" % (e.__class__, e))


def main():
    """ Main Python entry point for the worker utility. """

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true',
                        help='enable debug output')
    parser.add_argument('-d', dest='nodaemon', action='store_true',
                        help='do not run in daemon mode')
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        format='%(asctime)-6s: %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger('lbaas_worker')
    if args.debug:
        logger.setLevel(level=logging.DEBUG)

    server = Server(logger)

    if args.nodaemon:
        server.main()
    else:
        context = daemon.DaemonContext(
            working_directory='/etc/haproxy',
            umask=0o022,
            pidfile=lockfile.FileLock('/var/run/lbaas_worker.pid')
        )

        with context:
            server.main()

    return 0
