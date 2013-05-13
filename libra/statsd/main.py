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

import daemon
import daemon.pidfile
import daemon.runner
import grp
import pwd
import time

from libra.common.options import Options, setup_logging
from libra.openstack.common import importutils
from libra.statsd.drivers.base import known_drivers
from libra.statsd.scheduler import Sched


def start(args, drivers):
    """ Start the main server processing. """

    logger = setup_logging('libra_statsd', args)

    logger.info("Job server list: %s" % args.server)
    logger.info("Selected drivers: {0}".format(args.driver))

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
        '--repair_interval', type=int, default=180,
        help='how often to check if a load balancer has been repaired (in '
             'seconds)'
    )
    options.parser.add_argument(
        '--api_server', action='append', metavar='HOST:PORT', default=[],
        help='a list of API servers to connect to'
    )
    # Datadog plugin options
    options.parser.add_argument(
        '--datadog_api_key', help='API key for datadog alerting'
    )
    options.parser.add_argument(
        '--datadog_app_key', help='Application key for datadog alerting'
    )
    options.parser.add_argument(
        '--datadog_message_tail',
        help='Text to add at the end of a Datadog alert'
    )
    options.parser.add_argument(
        '--datadog_tags',
        help='A space separated list of tags for Datadog alerts'
    )
    options.parser.add_argument(
        '--datadog_env', default='unknown',
        help='Server enironment'
    )

    args = options.run()

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

    if not isinstance(args.driver, list):
        args.driver = args.driver.split()
    for driver in args.driver:
        drivers.append(importutils.import_class(
            known_drivers[driver]
        ))

    if args.nodaemon:
        start(args, drivers)
    else:
        pidfile = daemon.pidfile.TimeoutPIDLockFile(args.pid, 10)
        if daemon.runner.is_pidfile_stale(pidfile):
            pidfile.break_lock()
        context = daemon.DaemonContext(
            umask=0o022,
            pidfile=pidfile
        )
        if args.user:
            context.uid = pwd.getpwnam(args.user).pw_uid
        if args.group:
            context.gid = grp.getgrnam(args.group).gr_gid

        context.open()
        start(args, drivers)
