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
    config['database'] = {
        'username': args.db_user,
        'password': args.db_pass,
        'host': args.db_host,
        'schema': args.db_schema,
        'port': args.db_port,
        'schema': args.db_schema,
        'use_ssl': args.db_ssl,
        'ssl_cert': args.db_ssl_cert,
        'ssl_key': args.db_ssl_key,
        'ssl_ca': args.db_ssl_ca
    }
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
        '--db_user', help='MySQL database user'
    )
    options.parser.add_argument(
        '--db_pass', help='MySQL database password'
    )
    options.parser.add_argument(
        '--db_host', help='MySQL host name'
    )
    options.parser.add_argument(
        '--db_port', help='MySQL port number', default=3306, type=int
    )
    options.parser.add_argument(
        '--db_schema', help='MySQL schema for libra'
    )
    options.parser.add_argument(
        '--db_ssl', help='Enable MySQL SSL connections', action='store_true'
    )
    options.parser.add_argument(
        '--db_ssl_cert', help='MySQL SSL certificate'
    )
    options.parser.add_argument(
        '--db_ssl_key', help='MySQL SSL key'
    )
    options.parser.add_argument(
        '--db_ssl_ca', help='MySQL SSL certificate authority'
    )
    options.parser.add_argument(
        '--ssl_certfile',
        help='Path to an SSL certificate file'
    )
    options.parser.add_argument(
        '--ssl_keyfile',
        help='Path to an SSL key file'
    )

    args = options.run()

    required_args = [
        'db_user', 'db_pass', 'db_host', 'db_schema', 'ssl_certfile',
        'ssl_keyfile'
    ]
    if args.db_ssl:
        required_args.extend(['db_ssl_cert', 'db_ssl_key', 'db_ssl_ca'])

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
    sys.stderr = LogStdout(logger)
    # TODO: set ca_certs and cert_reqs=CERT_REQUIRED
    wsgi.server(
        eventlet.wrap_ssl(
            eventlet.listen((args.host, args.port)),
            certfile=args.ssl_certfile,
            keyfile=args.ssl_keyfile,
            server_side=True
        ),
        api
    )

    return 0
