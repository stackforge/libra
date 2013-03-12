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
import threading
import lockfile

from novaclient import exceptions
from libra.openstack.common import importutils
from libra.mgm.nova import Node, BuildError, NotFound
from libra.common.options import Options, setup_logging
from libra.mgm.drivers.base import known_drivers
from libra.mgm.node_list import NodeList, AccessDenied


class Server(object):
    def __init__(self, logger, args):
        self.logger = logger
        self.args = args
        self.ct = None
        self.ft = None
        self.api = None
        self.driver_class = None
        try:
            self.node_list = NodeList(self.args.datadir)
        except AccessDenied as exc:
            self.logger.error(exc)
            self.shutdown(True)

    def main(self):
        self.logger.info(
            'Libra Pool Manager started with a float of {nodes} nodes'
            .format(nodes=self.args.nodes)
        )
        signal.signal(signal.SIGINT, self.exit_handler)
        signal.signal(signal.SIGTERM, self.exit_handler)

        self.logger.info("Selected driver: {0}".format(self.args.driver))
        self.driver_class = importutils.import_class(
            known_drivers[self.args.driver]
        )

        # make initial check and then run scheduler
        self.logger.info(
            'Scheduling node check for {check} minutes'
            .format(check=self.args.check_interval)
        )
        # NOTE(LinuxJedi): Threading lock is for the case in the future where
        # we need two timers, we don't want them to both execute their trigger
        # at the same time.
        self.rlock = threading.RLock()
        self.check_nodes()
        self.failed_nodes()
        while True:
            time.sleep(1)

    def failed_nodes(self):
        """ check list of failures """
        with self.rlock:
            try:
                self.logger.info('Checking log of failed node uploads')
                nodes = self.node_list.get()
                if len(nodes) == 0:
                    self.logger.info('Node log empty')
                else:
                    api = self.driver_class(self.args.api_server, self.logger)
                    if api.is_online():
                        self.logger.info(
                            'Connected to {url}'.format(url=api.get_url())
                        )
                        for node in nodes:
                            self.retest_node(node, api)
                    else:
                        self.logger.error('No working API server found')
            except Exception:
                self.logger.exception(
                    'Uncaught exception during failed node check'
                )
            self.reset_failed_scheduler()

    def retest_node(self, node_id, api):
        try:
            nova = Node(
                self.args.nova_user,
                self.args.nova_pass,
                self.args.nova_tenant,
                self.args.nova_auth_url,
                self.args.nova_region,
                self.args.nova_keyname,
                self.args.nova_secgroup,
                self.args.nova_image,
                self.args.nova_image_size,
                node_basename=self.args.node_basename
            )
        except Exception as exc:
            self.logger.error(
                'Error initialising Nova connection {exc}'
                .format(exc=exc)
            )
            return
        self.logger.info('Retrying node {0}'.format(node_id))
        try:
            resp, status = nova.status(node_id)
        except NotFound:
            self.logger.info(
                'Node {0} no longer exists, removing from list'
                .format(node_id)
            )
            self.node_list.delete(node_id)
            return
        except exceptions.ClientException as exc:
            self.logger.error(
                'Error getting status from Nova, exception {exc}'
                .format(exc=sys.exc_info()[0])
            )
            return

        if resp.status_code not in(200, 203):
            self.logger.error(
                'Error geting status from Nova, error {0}'
                .format(resp.status_code)
            )
            return
        status = status['server']
        if status['status'] == 'ACTIVE':
            name = status['name']
            body = self.build_node_data(status)
            status, response = api.add_node(body)
            if not status:
                self.logger.error(
                    'Could not upload node {name} to API server'
                    .format(name=name)
                )
            else:
                self.node_list.delete(node_id)
                self.logger.info('Node {0} added to API server'.format(name))
            return
        elif status['status'].startswith('BUILD'):
            self.logger.info(
                'Node {0} still building, ignoring'.format(node_id)
            )
            return
        else:
            self.logger.info(
                'Node {0} is bad, deleting'.format(node_id)
            )
            status, msg = nova.delete(node_id)
            if not status:
                self.logger.error(msg)
            else:
                self.logger.info('Delete successful')
                self.node_list.delete(node_id)

    def check_nodes(self):
        """ check if known nodes are used """
        with self.rlock:
            try:
                self.logger.info('Checking if new nodes are needed')
                api = self.driver_class(self.args.api_server, self.logger)
                if api.is_online():
                    self.logger.info(
                        'Connected to {url}'.format(url=api.get_url())
                    )
                    free_count = api.get_free_count()
                    if free_count is None:
                        self.reset_scheduler()
                        return
                    if free_count < self.args.nodes:
                        # we need to build new nodes
                        nodes_required = self.args.nodes - free_count
                        self.logger.info(
                            'Building {nodes} nodes'
                            .format(nodes=nodes_required)
                        )
                        self.build_nodes(nodes_required, api)
                    else:
                        self.logger.info('No new nodes required')
                else:
                    self.logger.error('No working API server found')
            except Exception:
                self.logger.exception('Uncaught exception during node check')

            self.reset_scheduler()

    def reset_scheduler(self):
        self.logger.info('Node check timer sleeping for {mins} minutes'
                         .format(mins=self.args.check_interval))
        self.ct = threading.Timer(60 * int(self.args.check_interval),
                                  self.check_nodes, ())
        self.ct.start()

    def reset_failed_scheduler(self):
        self.logger.info('Node failed timer sleeping for {mins} minutes'
                         .format(mins=self.args.failed_interval))
        self.ft = threading.Timer(60 * int(self.args.failed_interval),
                                  self.failed_nodes, ())
        self.ft.start()

    def build_node_data(self, data):
        """ Build the API data from the node data """
        body = {}
        body['name'] = data['name']
        addresses = data['addresses']['private']
        for address in addresses:
            if not address['addr'].startswith('10.'):
                break
        body['publicIpAddr'] = address['addr']
        body['floatingIpAddr'] = address['addr']
        body['az'] = self.args.az
        body['type'] = "basename: {0}, image: {1}".format(
            self.args.node_basename, self.args.nova_image
        )
        return body

    def find_unknown(self, name, nova):
        """
            Nova can tell us a node failed to build when it didn't
            This does a check and if it did start to build adds it to the
            failed node list.
        """
        try:
            node_id = nova.get_node(name)
            self.logger.info('Storing node to try again later')
            self.node_list.add(node_id)
        except NotFound:
            # Node really didn't build
            return
        except exceptions.ClientException as exc:
            # TODO: edge case where if node reports failed, actually succeeds
            # and this node check fails we will have a dangling node
            self.logger.error(
                'Error getting failed node info from Nova, exception {exc}'
                .format(exc=exc)
            )

    def build_nodes(self, count, api):
        try:
            nova = Node(
                self.args.nova_user,
                self.args.nova_pass,
                self.args.nova_tenant,
                self.args.nova_auth_url,
                self.args.nova_region,
                self.args.nova_keyname,
                self.args.nova_secgroup,
                self.args.nova_image,
                self.args.nova_image_size,
                node_basename=self.args.node_basename
            )
        except Exception as exc:
            self.logger.error('Error initialising Nova connection {exc}'
                .format(exc=exc)
            )
            return
        while count > 0:
            try:
                data = nova.build()
            except BuildError as exc:
                self.logger.error('{0}, node {1}'
                    .format(exc.msg, exc.node_name)
                )
                if exc.node_id > 0:
                    self.logger.info('Storing node to try again later')
                    self.node_list.add(exc.node_id)
                else:
                    self.find_unknown(exc.node_name, nova)
                self.logger.warning('Aborting node building')
                return
            body = self.build_node_data(data)
            self.logger.info('Adding node {name} on {ip}'.format(
                name=body['name'], ip=body['publicIpAddr'])
            )
            status, response = api.add_node(body)
            if not status:
                self.logger.error(
                    'Could not upload node {name} to API server'
                    .format(name=data['name'])
                )
                self.logger.info('Storing node to try again later')
                self.node_list.add(data['id'])
                self.logger.warning('Aborting node building')
                return
            count = count - 1

    def exit_handler(self, signum, frame):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        self.shutdown(False)

    def shutdown(self, error):
        if self.ct:
            self.ct.cancel()
        if self.ft:
            self.ft.cancel()

        if not error:
            self.logger.info('Safely shutting down')
            sys.exit(0)
        else:
            self.logger.info('Shutting down due to error')
            sys.exit(1)


def main():
    options = Options('mgm', 'Node Management Daemon')
    options.parser.add_argument(
        '--api_server', action='append', metavar='HOST:PORT',
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
        '--failed_interval', type=int, default=15,
        help='how often to retest nodes that failed to get added to the API'
             ' server (in minutes)'
    )
    options.parser.add_argument(
        '--driver', dest='driver',
        choices=known_drivers.keys(), default='hp_rest',
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

    logger = setup_logging('libra_mgm', args)
    server = Server(logger, args)

    if args.nodaemon:
        server.main()
    else:
        pidfile = daemon.pidfile.TimeoutPIDLockFile(args.pid, 10)
        if daemon.runner.is_pidfile_stale(pidfile):
            logger.warning("Cleaning up stale PID file")
            pidfile.break_lock()
        context = daemon.DaemonContext(
            working_directory='/',
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
            return 1

        server.main()

    return 0
