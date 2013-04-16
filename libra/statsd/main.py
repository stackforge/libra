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
import daemon.runner
import lockfile
import grp
import os
import pwd
import time

from libra.common.options import Options, setup_logging
from libra.openstack.common import importutils
from libra.statsd.drivers.base import known_drivers
from libra.statsd.scheduler import Sched


def start(logger, args, drivers):
    """ Start the main server processing. """

    scheduler = Sched(logger, args, drivers)
    scheduler.start()
    while True:
        time.sleep(1)


def main():
    """ Main Python entry point for the statistics daemon. """
    drivers = []

    options = Options('statsd', 'Statistics Daemon')
    options.parser.add_argument(
        '--driver', dest='driver',
        choices=known_drivers.keys(), default='dummy',
        help='type of device to use'
    )
    options.parser.add_argument(
        '--server', dest='server', action='append', metavar='HOST:PORT',
        default=[],
        help='add a Gearman job server to the connection list'
    )
    options.parser.add_argument(
        '--ping_interval', type=int, default=60,
        help='how often to ping load balancers (in seconds)'
    )
    options.parser.add_argument(
        '--api_server', action='append', metavar='HOST:PORT', default=[],
        help='a list of API servers to connect to'
    )

    args = options.run()

    logger = setup_logging('libra_statsd', args)

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

    if not args.api_server:
        # NOTE(shrews): Can't set a default in argparse method because the
        # value is appended to the specified default.
        args.api_server.append('localhost:8889')
    elif not isinstance(args.api_server, list):
        # NOTE(shrews): The Options object cannot intelligently handle
        # creating a list from an option that may have multiple values.
        # We convert it to the expected type here.
        svr_list = args.api_server.split()
        args.api_server = svr_list

    logger.info("Job server list: %s" % args.server)
    logger.info("Selected drivers: {0}".format(args.driver))
    if not isinstance(args.driver, list):
        args.driver = args.driver.split()
    for driver in args.driver:
        drivers.append(importutils.import_class(
            known_drivers[driver]
        ))

    if args.nodaemon:
        start(logger, args, drivers)
    else:
        pidfile = daemon.pidfile.TimeoutPIDLockFile(args.pid, 10)
        if daemon.runner.is_pidfile_stale(pidfile):
            logger.warning("Cleaning up stale PID file")
            pidfile.break_lock()
        context = daemon.DaemonContext(
            umask=0o022,
            pidfile=pidfile,
            files_preserve=[logger.handlers[0].stream]
        )
        if args.user:
            try:
                context.uid = pwd.getpwnam(args.user).pw_uid
            except KeyError:
                logger.critical("Invalid user: %s" % args.user)
                return 1
            # NOTE(LinuxJedi): we are switching user so need to switch
            # the ownership of the log file for rotation
            os.chown(logger.handlers[0].baseFilename, context.uid, -1)
        if args.group:
            try:
                context.gid = grp.getgrnam(args.group).gr_gid
            except KeyError:
                logger.critical("Invalid group: %s" % args.group)
                return 1

        try:
            context.open()
        except lockfile.LockTimeout:
            logger.critical(
                "Failed to lock pidfile %s, another instance running?",
                args.pid
            )

        start(logger, args, drivers)
