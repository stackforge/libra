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
import eventlet
eventlet.monkey_patch()
import daemon
import daemon.pidfile
import daemon.runner
import grp
import pwd
import pecan
import sys
import os
from libra.admin_api import config as api_config
from libra.admin_api import model
from libra.admin_api.stats.scheduler import Stats
from libra.admin_api.stats.drivers.base import known_drivers
from libra.openstack.common import importutils
from libra.common.options import Options, setup_logging
from eventlet import wsgi


def get_pecan_config():
    # Set up the pecan configuration
    filename = api_config.__file__.replace('.pyc', '.py')
    return pecan.configuration.conf_from_file(filename)


def setup_app(pecan_config, args):

    model.init_model()

    if not pecan_config:
        pecan_config = get_pecan_config()
    config = dict(pecan_config)
    config['database'] = args.db_sections
    config['conffile'] = args.config
    if args.debug:
        config['wsme'] = {'debug': True}
        config['app']['debug'] = True

    pecan.configuration.set_config(config, overwrite=True)

    app = pecan.make_app(
        pecan_config.app.root,
        static_root=pecan_config.app.static_root,
        template_path=pecan_config.app.template_path,
        debug=getattr(pecan_config.app, 'debug', False),
        force_canonical=getattr(pecan_config.app, 'force_canonical', True),
        guess_content_type_from_ext=getattr(
            pecan_config.app,
            'guess_content_type_from_ext',
            True)
    )

    return app


class LogStdout(object):
    def __init__(self, logger):
        self.logger = logger.info

    def write(self, data):
        if data.strip() != '':
            self.logger(data)


def main():
    options = Options('admin_api', 'Admin API Server')
    options.parser.add_argument(
        '--host', help='IP address to bind to, 0.0.0.0 for all IPs',
        default='0.0.0.0'
    )
    options.parser.add_argument(
        '--port', help='Port number for API server', type=int, default=8889
    )
    options.parser.add_argument(
        '--db_sections', action='append', default=[],
        help='MySQL config sections in the config file'
    )
    options.parser.add_argument(
        '--ssl_certfile',
        help='Path to an SSL certificate file'
    )
    options.parser.add_argument(
        '--ssl_keyfile',
        help='Path to an SSL key file'
    )
    options.parser.add_argument(
        '--stats_driver',
        choices=known_drivers.keys(), default='dummy',
        help='type of stats device to use'
    )
    options.parser.add_argument(
        '--stats_ping_timer', type=int, default=60,
        help='how often to ping load balancers (in seconds)'
    )
    options.parser.add_argument(
        '--stats_poll_timeout', type=int, default=5,
        help='gearman timeout value for initial ping request (in seconds)'
    )
    options.parser.add_argument(
        '--stats_poll_timeout_retry', type=int, default=30,
        help='gearman timeout value for retry ping request (in seconds)'
    )
    options.parser.add_argument(
        '--stats_repair_timer', type=int, default=180,
        help='how often to check if a load balancer has been repaired (in '
             'seconds)'
    )
    options.parser.add_argument(
        '--number_of_servers', type=int, default=1,
        help='number of Admin API servers, used to calculate which Admin API '
             'server should stats ping next'
    )
    options.parser.add_argument(
        '--server_id', type=int, default=0,
        help='server ID of this server,  used to calculate which Admin API '
             'server should stats ping next (start at 0)'
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

    drivers = []

    if not isinstance(args.driver, list):
        args.driver = args.driver.split()
    for driver in args.driver:
        drivers.append(importutils.import_class(
            known_drivers[driver]
        ))

    required_args = ['db_sections', 'ssl_certfile', 'ssl_keyfile']

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

    if not isinstance(args.db_sections, list):
        db_list = args.db_sections.split()
        args.db_sections = db_list

    pc = get_pecan_config()
    if not args.nodaemon:
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
    # Use the root logger due to lots of services using logger
    logger = setup_logging('', args)
    logger.info('Starting on {0}:{1}'.format(args.host, args.port))
    api = setup_app(pc, args)
    Stats(logger, args, drivers)
    sys.stderr = LogStdout(logger)
    # TODO: set ca_certs and cert_reqs=CERT_REQUIRED
    ssl_sock = eventlet.wrap_ssl(
        eventlet.listen((args.host, args.port)),
        certfile=args.ssl_certfile,
        keyfile=args.ssl_keyfile,
        server_side=True
    )
    wsgi.server(ssl_sock, api, keepalive=False)

    return 0
