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

import logging
import argparse
import daemon
import signal
import sys

from libra.mgm.listener import Listener


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
    parser = argparse.ArgumentParser(
        description='LBaaS Node Management Daemon'
    )
    parser.add_argument('nodes', metavar='N', type=int,
                        help='number of nodes to maintain')
    parser.add_argument('-d', dest='nodaemon', action='store_true',
                        help='do not run in daemon mode')
    options = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)-6s: %(name)s - %(levelname)s - %(message)s',
        filename='/var/log/lbaas/lbaas_mgm.log'
    )
    logger = logging.getLogger('lbaas_mgm')
    logger.setLevel(logging.INFO)

    pid_fn = '/var/run/lbaas_mgm/lbaas_mgm.pid'
    pid = daemon.pidlockfile.TimeoutPIDLockFile(pid_fn, 10)

    server = Server(logger, options.nodes)

    if options.nodaemon:
        server.main()
    else:
        with daemon.DaemonContext(pidfile=pid):
            server.main()
