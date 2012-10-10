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
import grp
import pwd
import signal
import time
import sys
from threading import Timer

from libra.common.options import Options, setup_logging


class Server(object):
    def __init__(self, logger, args):
        self.logger = logger
        self.args = args
        self.st = None
        self.ct = None

    def main(self):
        self.logger.info(
            'Libra Pool Manager started with a float of {nodes} nodes'
            .format(nodes=self.args.nodes)
        )
        signal.signal(signal.SIGINT, self.exit_handler)
        signal.signal(signal.SIGTERM, self.exit_handler)

        # make initial sync and then run scheduler
        self.logger.info(
            'Scheduling node sync for {sync} minutes'
            .format(sync=self.args.sync_interval)
        )
        self.logger.info(
            'and node check for {check} minutes'
            .format(check=self.args.check_interval)
        )
        self.sync_nodes()
        self.check_nodes()
        while True:
            time.sleep(1)

    def check_nodes(self):
        """ check if known nodes are used """
        self.logger.info('Checking if new nodes are needed')
        self.ct = Timer(60 * int(self.args.check_interval),
                        self.check_nodes, ())
        self.ct.start()

    def sync_nodes(self):
        """ sync list of known nodes """
        self.logger.info('Syncing internal nodes list')
        self.st = Timer(60 * int(self.args.sync_interval), self.sync_nodes, ())
        self.st.start()

    def exit_handler(self, signum, frame):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        self.shutdown(False)

    def shutdown(self, error):
        if self.st:
            self.st.cancel()
        if self.ct:
            self.ct.cancel()

        if not error:
            self.logger.info('Safely shutting down')
            sys.exit(0)
        else:
            self.logger.info('Shutting down due to error')
            sys.exit(1)


def main():
    options = Options('mgm', 'Node Management Daemon')
    options.parser.add_argument(
        '--nodes', type=int, default=1,
        help='number of nodes'
    )
    options.parser.add_argument(
        '--interval', type=int, default=5,
        help='how often to poll API server (in minutes)'
    )
    args = options.run()

    logger = setup_logging('libra_mgm', args)
    server = Server(logger, args)

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
