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
from libra.worker.drivers.haproxy.services_base import haproxy_services

haproxy_group = cfg.OptGroup('worker:haproxy', 'Worker HAProxy options')

cfg.CONF.register_group(haproxy_group)

cfg.CONF.register_opts(
    [
        cfg.StrOpt('service',
                   choices=haproxy_services.keys(),
                   default='ubuntu',
                   help='OS services to use with HAProxy driver'),
        cfg.StrOpt('logfile',
                   default='/var/log/haproxy.log',
                   help='Location of HAProxy logfile'),
        cfg.StrOpt('statsfile',
                   default='/var/log/haproxy.stats',
                   help='Location of the HAProxy statistics cache file'),
    ],
    group=haproxy_group
)
