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
import sys
import os
import threading

from libra.common.options import Options, setup_logging
from libra.mgm.gearman_worker import worker_thread


class Server(object):
    def __init__(self, args):
        self.args = args
        self.logger = None

    def main(self):
        self.logger = setup_logging('libra_mgm', self.args)

        self.logger.info(
            'Libra Pool Manager worker started, spawning {0} threads'
            .format(self.args.threads)
        )
        thread_list = []
        for x in xrange(0, self.args.threads):
            thd = threading.Thread(
                target=worker_thread, args=[self.logger, self.args]
            )
            thd.daemon = True
            thread_list.append(thd)
            thd.start()
        for thd in thread_list:
            thd.join()


def main():
    options = Options('mgm', 'Node Management Daemon')
    options.parser.add_argument(
        '--az', type=int,
        help='The az the nodes and IPs will reside in (to be passed to the API'
             ' server)'
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
        help='the tenant name for the Nova API'
    )
    options.parser.add_argument(
        '--nova_tenant_id',
        help='the tenant ID for the Nova API'
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
    options.parser.add_argument(
        '--nova_az_name',
        help='the az name to build in'
    )
    options.parser.add_argument(
        '--nova_insecure', action='store_true',
        help='do not attempt to verify Nova/Keystone SSL certificates'
    )
    options.parser.add_argument(
        '--nova_bypass_url',
        help='use a different URL to the one supplied by the service'
    )
    options.parser.add_argument(
        '--gearman', action='append', metavar='HOST:PORT', default=[],
        help='Gearman job servers'
    )
    options.parser.add_argument(
        '--gearman_keepalive', action="store_true",
        help='use KEEPALIVE to Gearman server'
    )
    options.parser.add_argument(
        '--gearman_keepcnt', type=int, metavar='COUNT',
        help='max keepalive probes to send before killing connection'
    )
    options.parser.add_argument(
        '--gearman_keepidle', type=int, metavar='SECONDS',
        help='seconds of idle time before sending keepalive probes'
    )
    options.parser.add_argument(
        '--gearman_keepintvl', type=int, metavar='SECONDS',
        help='seconds between TCP keepalive probes'
    )
    options.parser.add_argument(
        '--gearman_ssl_ca', metavar='FILE',
        help='Gearman SSL certificate authority'
    )
    options.parser.add_argument(
        '--gearman_ssl_cert', metavar='FILE',
        help='Gearman SSL certificate'
    )
    options.parser.add_argument(
        '--gearman_ssl_key', metavar='FILE',
        help='Gearman SSL key'
    )
    options.parser.add_argument(
        '--gearman_poll', type=int, metavar='TIME',
        default=1, help='Gearman worker polling timeout'
    )
    options.parser.add_argument(
        '--threads',
        dest='threads', type=int, default=4,
        help='Number of worker threads to spawn'
    )
    options.parser.add_argument(
        '--rm_fip_ignore_500', action='store_true',
        help='Ignore HTTP 500 error when removing a floating IP'
    )

    args = options.run()

    required_args = [
        'az',
        'nova_image', 'nova_image_size', 'nova_secgroup', 'nova_keyname',
        'nova_region', 'nova_user', 'nova_pass', 'nova_auth_url'
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

    if not args.gearman:
        # NOTE(shrews): Can't set a default in argparse method because the
        # value is appended to the specified default.
        args.gearman.append('localhost:4730')
    elif not isinstance(args.gearman, list):
        # NOTE(shrews): The Options object cannot intelligently handle
        # creating a list from an option that may have multiple values.
        # We convert it to the expected type here.
        svr_list = args.gearman.split()
        args.gearman = svr_list

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
