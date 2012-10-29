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
import daemon.pidfile
import gearman.errors
import grp
import json
import pwd
import socket
from time import sleep

from libra.openstack.common import importutils
from libra.common.json_gearman import JSONGearmanWorker
from libra.common.options import Options, setup_logging
from libra.worker.controller import LBaaSController
from libra.worker.drivers.base import known_drivers
from libra.worker.drivers.haproxy.services_base import haproxy_services


def lbaas_task(worker, job):
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


class CustomJSONGearmanWorker(JSONGearmanWorker):
    """ Custom class we will use to pass arguments to the Gearman task. """
    logger = None
    driver = None


class Server(object):
    """
    Encapsulates server activity so we can run it in either daemon or
    non-daemon mode.
    """

    def __init__(self, logger, servers, reconnect_sleep):
        self.logger = logger
        self.driver = None
        self.servers = servers
        self.reconnect_sleep = reconnect_sleep

    def main(self):
        """ Main method of the server.  """
        my_ip = socket.gethostbyname(socket.gethostname())
        task_name = "lbaas-%s" % my_ip
        self.logger.info("Registering task %s" % task_name)

        worker = CustomJSONGearmanWorker(self.servers)
        worker.set_client_id(my_ip)
        worker.register_task(task_name, lbaas_task)
        worker.logger = self.logger
        worker.driver = self.driver

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
        '-s', '--reconnect_sleep',
        dest='reconnect_sleep', type=int, metavar='TIME',
        default=60, help='seconds to sleep between job server reconnects'
    )
    options.parser.add_argument(
        '--driver', dest='driver',
        choices=known_drivers.keys(), default='haproxy',
        help='type of device to use'
    )
    options.parser.add_argument(
        '--server', dest='server', action='append', metavar='HOST:PORT',
        default=[],
        help='add a Gearman job server to the connection list'
    )
    options.parser.add_argument(
        '--haproxy-service', dest='haproxy_service',
        choices=haproxy_services.keys(), default='ubuntu',
        help='os services to use with HAProxy driver (when used)'
    )
    args = options.run()

    logger = setup_logging('libra_worker', args)

    if not args.server:
        # NOTE(shrews): Can't set a default in argparse method because the
        # value is appended to the specified default.
        args.server.append('localhost:4730')
    elif not isinstance(args.server, list):
        # NOTE(shrews): The Options object cannot intelligently handle
        # creating a list from an option that may have multiple values.
        # We convert it to the expected type here.
        svr_list = args.server.split()
        args.server = svr_list

    # Import the device driver we are going to use. This will be sent
    # along to the Gearman task that will use it to communicate with
    # the device.

    logger.info("Selected driver: %s" % args.driver)
    driver_class = importutils.import_class(known_drivers[args.driver])

    if args.driver == 'haproxy':
        logger.info("Selected HAProxy service: %s" % args.haproxy_service)
        driver = driver_class(haproxy_services[args.haproxy_service])
    else:
        driver = driver_class()

    logger.info("Job server list: %s" % args.server)
    server = Server(logger, args.server, args.reconnect_sleep)
    server.driver = driver

    if args.nodaemon:
        server.main()
    else:
        context = daemon.DaemonContext(
            working_directory='/etc/haproxy',
            umask=0o022,
            pidfile=daemon.pidfile.TimeoutPIDLockFile(args.pid),
            files_preserve=[logger.handlers[0].stream]
        )
        if args.user:
            try:
                context.uid = pwd.getpwnam(args.user).pw_uid
            except KeyError:
                logger.critical("Invalid user: %s" % args.user)
                return 1
        if args.group:
            try:
                context.gid = grp.getgrnam(args.group).gr_gid
            except KeyError:
                logger.critical("Invalid group: %s" % args.group)
                return 1

        with context:
            server.main()

    return 0
