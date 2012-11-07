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

import eventlet
eventlet.monkey_patch()

import daemon
import daemon.pidfile
import grp
import pwd

from libra.openstack.common import importutils
from libra.common.options import Options, setup_logging
from libra.worker.drivers.base import known_drivers
from libra.worker.drivers.haproxy.services_base import haproxy_services
from libra.worker.stats_client import stats_manager
from libra.worker.worker import config_manager


class EventServer(object):
    """
    Encapsulates server activity so we can run it in either daemon or
    non-daemon mode.
    """

    def __init__(self, logger):
        self.logger = logger

    def main(self, tasks):
        """
        Main method of the server.

        tasks
            A tuple with two items: a function name, and a tuple with
            that function's arguments.
        """

        thread_list = []

        for task, args in tasks:
            thread_list.append(eventlet.spawn(task, *args))

        for thd in thread_list:
            thd.wait()

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
    server = EventServer(logger)

    # Tasks to execute in parallel
    task_list = [
        (config_manager, (logger, driver, args.server, args.reconnect_sleep)),
        (stats_manager, (logger, driver))
    ]

    if args.nodaemon:
        server.main(task_list)
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
            server.main(task_list)

    return 0
