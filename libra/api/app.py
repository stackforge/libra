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
from oslo.config import cfg
import pecan
import logging
import sys
from libra.api import config as api_config
from libra.api import model
from libra.api import acl
from wsgiref.simple_server import make_server
from libra.common.options import Options, setup_logging

auth_opts = [
    cfg.StrOpt('auth_strategy',
               default='keystone',
               help='The strategy to use for auth: noauth or keystone.'),
]

CONF = cfg.CONF
CONF.register_opts(auth_opts)


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
        'schema': args.db_schema
    }
    config['gearman'] = {
        'server': args.gearman
    }
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

    if not args.disable_keystone:
        return acl.install(app, cfg.CONF)

    return app


class LogStdout(object):
    def __init__(self, logger):
        self.logger = logger.info

    def write(self, data):
        if data.strip() != '': self.logger(data)

def main():
    options = Options('api', 'API Server')
    options.parser.add_argument(
        '--host', help='IP address to bind to, 0.0.0.0 for all IPs',
        default='0.0.0.0'
    )
    options.parser.add_argument(
        '--port', help='Port number for API server', type=int, default=8080
    )
    options.parser.add_argument(
        '--disable_keystone', help='Unauthenticated server, for testing only',
        action='store_true'
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
        '--db_schema', help='MySQL schema for libra'
    )
    options.parser.add_argument(
        '--gearman', action='append', metavar='HOST:PORT', default=[],
        help='Gearman job servers'
    )

    args = options.run()

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

    logger = setup_logging('api', args)
    sys.stderr = LogStdout(logger)
    pc = get_pecan_config()
    api = setup_app(pc, args)
    srv = make_server(args.host, args.port, api)
    srv.serve_forever()
