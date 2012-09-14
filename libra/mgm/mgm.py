#!/usr/bin/env python
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
import lockfile
import signal
import sys

from libra.mgm.listener import Listener
from libra.common.options import Options
from libra.common.logger import Logger


class Server(object):
    def __init__(self, logger, nodes):
        self.logger = logger
        self.nodes = nodes

    def main(self):
        self.logger.info(
            'LBaaS Pool Manager started with {nodes} nodes'
            .format(nodes=self.nodes)
        )
        signal.signal(signal.SIGINT, self.exit_handler)
        signal.signal(signal.SIGTERM, self.exit_handler)
        listner = Listener(self.logger)
        try:
            listner.run()
        except Exception as e:
            self.logger.critical(
                'Exception: {eclass}, {exception}'
                .format(eclass=e.__class__, exception=e)
            )
            self.shutdown(True)
        self.shutdown(False)

    def exit_handler(self, signum, frame):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

    def shutdown(self, error):
        if not error:
            self.logger.info('Safely shutting down')
            sys.exit(0)
        else:
            self.logger.info('Shutting down due to error')
            sys.exit(1)


def main():
    options = Options('mgm', 'Node Management Daemon')

    options.parser.add_argument(
        '-o', '--nodes', default=10,
        help='Number of spare nodes to keep in pool'
    )
    args = options.run()

    if args.verbose:
        loglevel = 'verbose'
    elif args.debug:
        loglevel = 'debug'

    if args.nodaemon:
        logfile = None
    else:
        logfile = args.logfile

    logger = Logger(
        logfile,
        loglevel
    )

    server = Server(logger.logger, args.nodes)

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
