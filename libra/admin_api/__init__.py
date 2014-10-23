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


adminapi_group = cfg.OptGroup('admin_api', 'Libra Admin API options')

cfg.CONF.register_group(adminapi_group)

cfg.CONF.register_opts(
    [
        cfg.BoolOpt('disable_keystone',
                    default=False,
                    help='Unauthenticated server, for testing only'),
        cfg.StrOpt('keystone_module',
                   default='keystoneclient.middleware.auth_token:AuthProtocol',
                   help='A colon separated module and class for keystone '
                        ' middleware'),
        cfg.StrOpt('datadog_api_key',
                   help='API key for datadog alerting'),
        cfg.StrOpt('datadog_app_key',
                   help='Application key for datadog alerting'),
        cfg.StrOpt('datadog_env',
                   default='unknown',
                   help='Server enironment'),
        cfg.StrOpt('datadog_message_tail',
                   help='Text to add at the end of a Datadog alert'),
        cfg.StrOpt('datadog_tags',
                   help='A space separated list of tags for Datadog alerts'),
        cfg.ListOpt('db_sections',
                    required=True,
                    help='MySQL config sections in the config file'),
        cfg.IntOpt('expire_days',
                   default=0,
                   help='Number of days until deleted load balancers '
                        'are expired'),
        cfg.StrOpt('host',
                   default='0.0.0.0',
                   help='IP address to bind to, 0.0.0.0 for all IPs'),
        cfg.IntOpt('node_pool_size',
                   default=10,
                   help='Number of hot spare devices to keep in the pool'),
        cfg.IntOpt('number_of_servers',
                   default=1,
                   help='number of Admin API servers, used to calculate '
                        'which Admin API server should stats ping next'),
        cfg.StrOpt('pid',
                   default='/var/run/libra/libra_admin_api.pid',
                   help='PID file'),
        cfg.IntOpt('port',
                   default=8889,
                   help='Port number for API server'),
        cfg.IntOpt('server_id',
                   default=0,
                   help='server ID of this server, used to calculate which '
                        'Admin API server should stats ping next '
                        '(start at 0)'),
        cfg.StrOpt('ssl_certfile',
                   help='Path to an SSL certificate file'),
        cfg.StrOpt('ssl_keyfile',
                   help='Path to an SSL key file'),
        cfg.IntOpt('stats_device_error_limit',
                   default=5,
                   help='Max number of simultaneous device failures to allow '
                        'recovery on'),
        cfg.ListOpt('stats_driver',
                    default=['dummy'],
                    help='type of stats device to use'),
        cfg.IntOpt('stats_offline_ping_limit',
                   default=10,
                   help='Number of failed pings to an OFFLINE device before '
                        'deleting it'),
        cfg.IntOpt('stats_poll_timeout',
                   default=5,
                   help='gearman timeout value for initial ping request '
                        '(in seconds)'),
        cfg.IntOpt('stats_poll_timeout_retry',
                   default=30,
                   help='gearman timeout value for retry ping request '
                        '(in seconds)'),
        cfg.IntOpt('vip_pool_size',
                   default=10,
                   help='Number of hot spare vips to keep in the pool'),
        cfg.BoolOpt('stats_enable',
                    default=False,
                    help='Enable / Disable usage statistics gathering'),
        cfg.IntOpt('exists_freq',
                   metavar='MINUTES',
                   default=60,
                   help='Minutes between sending of billing exists messages'),
        cfg.IntOpt('usage_freq',
                   metavar='MINUTES',
                   default=60,
                   help='Minutes between sending of billing usage messages'),
        cfg.IntOpt('stats_freq',
                   metavar='MINUTES',
                   default=5,
                   help='Minutes between collecting usage statistics'),
        cfg.BoolOpt('stats_purge_enable',
                    default=False,
                    help='Enable / Disable purging of usage statistics'),
        cfg.IntOpt('stats_purge_days',
                   metavar='DAYS',
                   default=5,
                   help='Number of days to keep usage statistics'),
        cfg.IntOpt('delete_timer_seconds',
                   default=5,
                   help='Which second of each minute delete timer should run'),
        cfg.IntOpt('ping_timer_seconds',
                   default=15,
                   help='Second of each minute ping timer should run'),
        cfg.IntOpt('stats_timer_seconds',
                   default=20,
                   help='Second of each minute statistics timer should run'),
        cfg.IntOpt('usage_timer_seconds',
                   default=25,
                   help='Which second of each minute usage timer should run'),
        cfg.IntOpt('probe_timer_seconds',
                   default=30,
                   help='Which second of each minute probe timer should run'),
        cfg.IntOpt('offline_timer_seconds',
                   default=45,
                   help='Second of each minute offline timer should run'),
        cfg.IntOpt('vips_timer_seconds',
                   default=50,
                   help='Which second of each minute vips timer should run'),
        cfg.IntOpt('exists_timer_seconds',
                   default=55,
                   help='Second of each minute exists timer should run'),
        cfg.IntOpt('offline_failed_save',
                   default=0,
                   help='Number of failed offline instances to save '
                        'for forensic analysis'),
         cfg.IntOpt('online_failed_save',
                   default=0,
                   help='Number of failed online instances to save '
                        'for forensic analysis'),
     ],
    group=adminapi_group
)
