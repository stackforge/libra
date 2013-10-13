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
from libra.worker.drivers.base import known_drivers


worker_group = cfg.OptGroup('worker', 'Libra Worker options')

cfg.CONF.register_group(worker_group)

cfg.CONF.register_opts(
    [
        cfg.StrOpt('driver',
                   default='haproxy',
                   choices=known_drivers.keys(),
                   help='Type of device to use'),
        cfg.StrOpt('logfile',
                   default='/var/log/libra/libra_worker.log',
                   help='Log file'),
        cfg.StrOpt('pid',
                   default='/var/run/libra/libra_worker.pid',
                   help='PID file'),
    ],
    group=worker_group
)
