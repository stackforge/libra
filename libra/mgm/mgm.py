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
import grp
import pwd
import signal
import time
import sys
import os
from stevedore.extension import ExtensionManager
import threading

from libra.common.options import Options, setup_logging
from libra.common.utils import get_namespace_names
from libra.mgm.node_list import NodeList, AccessDenied
from libra.mgm import drivers


class Server(object):
    def __init__(self, args):
        self.args = args
        self.ft = None
        self.api = None
        self.driver_class = None
        self.schedulers = []
        try:
            self.node_list = NodeList(self.args.datadir)
        except AccessDenied as exc:
            print(str(exc))
            self.shutdown(True)

    def main(self):
        self.logger = setup_logging('libra_mgm', self.args)

        self.logger.info(
            'Libra Pool Manager started with a float of {nodes} nodes'
            .format(nodes=self.args.nodes)
        )
        signal.signal(signal.SIGINT, self.exit_handler)
        signal.signal(signal.SIGTERM, self.exit_handler)

        self.logger.info("Selected driver: {0}".format(self.args.driver))

        self.driver_class = drivers.get_driver(self.args.driver)

        # NOTE(LinuxJedi): Threading lock is due to needing more than one
        # timer and we don't want them to execute their trigger
        # at the same time.
        self.rlock = threading.RLock()

        # Load and log schedulers
        # NOTE(ekarlso): Should this be chaned into check what schedulers are
        # enabled ?
        em = ExtensionManager(drivers.NAMESPACE)
        em.map(self.run_scheduler)
        self.logger.info("Loaded schedulers %s", ", ".join(em.names()))

        while True:
            time.sleep(1)

    def run_scheduler(self, ep):
        """
        Run a scheduler
        """
        instance = ep.plugin(self.driver_class, self.rlock, self.logger,
                             self.node_list, self.args)
        instance.run()
        self.sheduler.apped(instance)

    def exit_handler(self, signum, frame):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        self.shutdown(False)

    def shutdown(self, error):
        for sched in self.schedulers:
            sched.timer.cancel()

        if not error:
            self.logger.info('Safely shutting down')
            sys.exit(0)
        else:
            self.logger.info('Shutting down due to error')
            sys.exit(1)


def main():
    options = Options('mgm', 'Node Management Daemon')
    options.parser.add_argument(
        '--api_server', action='append', metavar='HOST:PORT', default=[],
        help='a list of API servers to connect to (for HP REST API driver)'
    )
    options.parser.add_argument(
        '--datadir', dest='datadir',
        help='directory to store data files'
    )
    options.parser.add_argument(
        '--az', type=int,
        help='The az number the node will reside in (to be passed to the API'
             ' server)'
    )
    options.parser.add_argument(
        '--nodes', type=int, default=1,
        help='number of nodes'
    )
    options.parser.add_argument(
        '--check_interval', type=int, default=5,
        help='how often to check if new nodes are needed (in minutes)'
    )
    options.parser.add_argument(
        '--submit_interval', type=int, default=15,
        help='how often to test nodes for submission to the API'
             ' server (in minutes)'
    )
    options.parser.add_argument(
        '--driver', dest='driver',
        choices=get_namespace_names(drivers.NAMESPACE),
        default='hp_rest',
        help='type of device to use'
    )
    options.parser.add_argument(
        '--node_basename', dest='node_basename',
        help='prepend the name of all nodes with this'
    )
    options.parser.add_argument(
        '--nova_auth_url',
        help='the auth URL for the Nova API'
    )
    options.parser.add_argument(
        '--nova_user',
        help='the username for the Nova API'
    )
    options.parser.add_argument(
        '--nova_pass',
        help='the password for the Nova API'
    )
    options.parser.add_argument(
        '--nova_region',
        help='the region to use for the Nova API'
    )
    options.parser.add_argument(
        '--nova_tenant',
        help='the tenant for the Nova API'
    )
    options.parser.add_argument(
        '--nova_keyname',
        help='the key name for new nodes spun up in the Nova API'
    )
    options.parser.add_argument(
        '--nova_secgroup',
        help='the security group for new nodes spun up in the Nova API'
    )
    options.parser.add_argument(
        '--nova_image',
        help='the image ID or name to use for new nodes spun up in the'
             ' Nova API'
    )
    options.parser.add_argument(
        '--nova_image_size',
        help='the image size ID (flavor ID) or name to use for new nodes spun'
             ' up in the Nova API'
    )

    args = options.run()

    required_args = [
        'datadir', 'az',
        'nova_image', 'nova_image_size', 'nova_secgroup', 'nova_keyname',
        'nova_tenant', 'nova_region', 'nova_user', 'nova_pass', 'nova_auth_url'
    ]

    # NOTE(LinuxJedi): We are checking for required args here because the
    # parser can't yet check both command line and config file to see if an
    # option has been set
    missing_args = 0
    for req in required_args:
        test_var = getattr(args, req)
        if test_var is None:
            missing_args += 1
            sys.stderr.write(
                '{app}: error: argument --{test_var} is required\n'
                .format(app=os.path.basename(sys.argv[0]), test_var=req))
    if missing_args:
        return 2

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

    server = Server(args)

    if args.nodaemon:
        server.main()
    else:
        pidfile = daemon.pidfile.TimeoutPIDLockFile(args.pid, 10)
        if daemon.runner.is_pidfile_stale(pidfile):
            pidfile.break_lock()
        context = daemon.DaemonContext(
            working_directory='/',
            umask=0o022,
            pidfile=pidfile
        )
        if args.user:
            context.uid = pwd.getpwnam(args.user).pw_uid
        if args.group:
            context.gid = grp.getgrnam(args.group).gr_gid

        context.open()
        server.main()

    return 0
