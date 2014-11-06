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

from oslo.config import cfg


mgm_group = cfg.OptGroup('mgm', 'Libra Pool Manager options')

cfg.CONF.register_group(mgm_group)

cfg.CONF.register_opts(
    [
        cfg.IntOpt('az',
                   required=True,
                   help='The az the nodes and IPs will reside in (to be '
                        'passed to the API server'),
        cfg.StrOpt('pid',
                   default='/var/run/libra/libra_mgm.pid',
                   help='PID file'),
        cfg.StrOpt('node_basename',
                   help='prepend the name of all nodes with this'),
        cfg.StrOpt('nova_auth_url',
                   required=True,
                   help='the auth URL for the Nova API'),
        cfg.StrOpt('nova_user',
                   required=True,
                   secret=True,
                   help='the username for the Nova API'),
        cfg.StrOpt('nova_pass',
                   required=True,
                   secret=True,
                   help='the password for the Nova API'),
        cfg.StrOpt('nova_region',
                   required=True,
                   help='the region to use for the Nova API'),
        cfg.StrOpt('nova_tenant',
                   help='the tenant name for the Nova API'),
        cfg.StrOpt('nova_tenant_id',
                   help='the tenant ID for the Nova API'),
        cfg.StrOpt('nova_keyname',
                   required=True,
                   help='the key name for new nodes spun up in the Nova API'),
        cfg.StrOpt('nova_secgroup',
                   required=True,
                   help='the security group for new nodes spun up in the '
                        'Nova API'),
        cfg.StrOpt('nova_image',
                   required=True,
                   help='the image ID or name to use for new nodes spun up '
                        'in the Nova API'),
        cfg.StrOpt('nova_image_size',
                   required=True,
                   help='the image size ID (flavor ID) or name to use for '
                        'new nodes spun up in the Nova API'),
        cfg.StrOpt('nova_az_name',
                   help='the az name to build in'),
        cfg.BoolOpt('nova_insecure',
                    default=False,
                    help='do not attempt to verify Nova/Keystone SSL '
                         'certificates'),
        cfg.StrOpt('nova_bypass_url',
                   help='use a different URL to the one supplied by the '
                        'service'),
        cfg.StrOpt('nova_net_id',
                   help='The ID of the network to put loadbalancer on '
                        '(Required if multiple Neutron networks)'),
        cfg.BoolOpt('rm_fip_ignore_500',
                    default=False,
                    help='Ignore HTTP 500 error when removing a floating IP'),
        cfg.IntOpt('tcp_check_port',
                   help='Port number to ping to check floating IP assign '
                        'worked'),
        cfg.IntOpt('threads',
                   default=4,
                   help='Number of worker threads to spawn'),
        cfg.IntOpt('build_diag_timeout',
                   default=10,
                   help='Timeout in seconds the pool manager '
                        'will wait for a worker to complete '
                        'the post-build diagnostic tests.'),
        cfg.IntOpt('nova_timeout',
                   default=30,
                   help='Timeout in seconds the pool manager '
                        'will wait for a nova call to complete.'),
        cfg.IntOpt('rate_limit_expunge_seconds',
                   default=86400,
                   help='Time (in seconds) after which old rows will '
                        'be expunged from rate_limited_actions'),
        cfg.IntOpt('rate_limit_delete_device_period',
                   default=30,
                   help='Period duration (in seconds) which rate-limit '
                        'checking applies for DELETE_DEVICE'),
        cfg.IntOpt('rate_limit_delete_device_max_count',
                   default=3,
                   help='Max number of DELETE_DEVICE actions permitted '
                        'in the specified period'),
     ],
    group=mgm_group
)
