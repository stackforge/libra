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


api_group = cfg.OptGroup('api', 'Libra API options')

cfg.CONF.register_group(api_group)

cfg.CONF.register_opts(
    [
        cfg.ListOpt('db_sections',
                    required=True,
                    help='MySQL config sections in the config file'),
        cfg.BoolOpt('disable_keystone',
                    default=False,
                    help='Unauthenticated server, for testing only'),
        cfg.StrOpt('host',
                   default='0.0.0.0',
                   help='IP address to bind to, 0.0.0.0 for all IPs'),
        cfg.ListOpt('ip_filters',
                    help='IP filters for backend nodes in the form '
                         'xxx.xxx.xxx.xxx/yy'),
        cfg.StrOpt('keystone_module',
                   default='keystoneclient.middleware.auth_token:AuthProtocol',
                   help='A colon separated module and class for keystone '
                        ' middleware'),
        cfg.StrOpt('pid',
                   default='/var/run/libra/libra_api.pid',
                   help='PID file'),
        cfg.IntOpt('port',
                   default=443,
                   help='Port number for API server'),
        cfg.StrOpt('ssl_certfile',
                   help='Path to an SSL certificate file'),
        cfg.StrOpt('ssl_keyfile',
                   help='Path to an SSL key file'),
        cfg.StrOpt('swift_basepath',
                   required=True,
                   help='Default Swift container to place log files'),
        cfg.StrOpt('swift_endpoint',
                   required=True,
                   help='Default endpoint URL (tenant ID will be appended'
                        ' to this)'),
    ],
    group=api_group
)
