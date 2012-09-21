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

import daemon
import gearman.errors
import json
import lockfile
import socket
from time import sleep

from libra.common.json_gearman import JSONGearmanWorker
from libra.common.faults import BadRequest
from libra.common.options import Options, setup_logging
from libra.worker.drivers.base import known_drivers
from libra.worker.utils import import_class


def lbaas_task(worker, job):
    """ Main Gearman worker task.  """

    NODE_OK = "ENABLED"
    NODE_ERR = "DISABLED"

    logger = worker.logger
    driver = worker.driver

    # Turn string into JSON object
    data = json.loads(job.data)

    lb_name = data['name']
    logger.debug("LB name: %s" % lb_name)

    if 'nodes' not in data:
        return BadRequest("Missing 'nodes' element").to_json()

    for lb_node in data['nodes']:
        port, address = None, None

        if 'port' in lb_node:
            port = lb_node['port']
        else:
            return BadRequest("Missing 'port' element.").to_json()

        if 'address' in lb_node:
            address = lb_node['address']
        else:
            return BadRequest("Missing 'address' element.").to_json()

        logger.debug("Server node: %s:%s" % (address, port))

        try:
            driver.add_server(address, port)
        except NotImplementedError:
            logger.info("Selected driver could not add server.")
            lb_node['condition'] = NODE_ERR
        except Exception as e:
            logger.critical("Failure trying adding server: %s, %s" %
                            (e.__class__, e))
            lb_node['condition'] = NODE_ERR
        else:
            lb_node['condition'] = NODE_OK

    try:
        driver.activate()
    except NotImplementedError:
        logger.info("Selected driver could not activate changes.")
        for lb_node in data['nodes']:
            lb_node['condition'] = NODE_ERR

    # Return the same JSON object, but with condition fields set.
    return data


class CustomJSONGearmanWorker(JSONGearmanWorker):
    """ Custom class we will use to pass arguments to the Gearman task. """
    logger = None
    driver = None


class Server(object):
    """
    Encapsulates server activity so we can run it in either daemon or
    non-daemon mode.
    """

    def __init__(self, servers, reconnect_sleep):
        self.logger = None
        self.driver = None
        self.servers = servers
        self.reconnect_sleep = reconnect_sleep

    def main(self):
        my_ip = socket.gethostbyname(socket.gethostname())
        task_name = "lbaas-%s" % my_ip
        self.logger.debug("Registering task %s" % task_name)

        worker = CustomJSONGearmanWorker(self.servers)
        worker.set_client_id(my_ip)
        worker.register_task(task_name, lbaas_task)

        retry = True

        while (retry):
            try:
                worker.work()
            except KeyboardInterrupt:
                retry = False
            except gearman.errors.ServerUnavailable:
                self.logger.error("Job server(s) went away. Reconnecting.")
                sleep(self.reconnect_sleep)
                retry = True
            except Exception as e:
                self.logger.critical("Exception: %s, %s" % (e.__class__, e))
                retry = False

        self.logger.info("Shutting down")


def main():
    """ Main Python entry point for the worker utility. """

    options = Options('worker', 'Worker Daemon')
    options.parser.add_argument(
        '-s', dest='reconnect_sleep', type=int, metavar='TIME',
        default=60, help='seconds to sleep between job server reconnects'
    )
    options.parser.add_argument(
        '--driver', dest='driver',
        choices=known_drivers.keys(), default='haproxy',
        help='Type of device to use'
    )
    args = options.run()

    logger = setup_logging('libra_worker', args)

    # Import the device driver we are going to use. This will be sent
    # along to the Gearman task that will use it to communicate with
    # the device.

    logger.debug("Using driver %s=%s" % (args.driver,
                                         known_drivers[args.driver]))
    driver_class = import_class(known_drivers[args.driver])
    driver = driver_class()

    server = Server(['localhost:4730'], args.reconnect_sleep)
    server.logger = logger
    server.driver = driver

    if args.nodaemon:
        server.main()
    else:
        context = daemon.DaemonContext(
            working_directory='/etc/haproxy',
            umask=0o022,
            pidfile=lockfile.FileLock(args.pid)
        )

        with context:
            server.main()

    return 0
