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
import gearman.errors
import grp
import json
import os
import pwd
import socket
import time

from libra.common.json_gearman import JSONGearmanWorker
from libra.common.options import Options, setup_logging


class CustomJSONGearmanWorker(JSONGearmanWorker):
    """ Custom class we will use to pass arguments to the Gearman task. """
    logger = None


def handler(worker, job):
    """ Main Gearman worker task. """
    logger = worker.logger
    logger.debug("Received JSON message: %s" % json.dumps(job.data, indent=4))
    return {"OK"}


def start(logger, servers):
    """ Start the main server processing. """

    hostname = socket.gethostname()
    task_name = "lbaas-statistics"
    worker = CustomJSONGearmanWorker(servers)
    worker.set_client_id(hostname)
    worker.register_task(task_name, handler)
    worker.logger = logger

    retry = True

    while retry:
        try:
            worker.work()
        except KeyboardInterrupt:
            retry = False
        except gearman.errors.ServerUnavailable:
            logger.error("[statsd] Job server(s) went away. Reconnecting.")
            time.sleep(60)
            retry = True
        except Exception as e:
            logger.critical("[statsd] Exception: %s, %s" % (e.__class__, e))
            retry = False

    logger.info("[statsd] Statistics process terminated.")


def main():
    """ Main Python entry point for the statistics daemon. """

    options = Options('statsd', 'Statistics Daemon')
    options.parser.add_argument(
        '--server', dest='server', action='append', metavar='HOST:PORT',
        default=[],
        help='add a Gearman job server to the connection list'
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

    logger.info("Job server list: %s" % args.server)

    if args.nodaemon:
        start(logger, args.server)
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

        start(logger, args.server)
