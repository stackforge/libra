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

import os
import os.path

from oslo.config import cfg

CONF = cfg.CONF

common_cli_opts = [
    cfg.BoolOpt('daemon',
                default=True,
                help='Run as a daemon'),
    cfg.StrOpt('group',
               help='Group to use for daemon mode'),
    cfg.StrOpt('user',
               help='User to use for daemon mode')
]

gearman_opts = [
    cfg.BoolOpt('keepalive',
                default=False,
                help='Enable TCP KEEPALIVE pings'),
    cfg.IntOpt('keepcnt',
               metavar='COUNT',
               help='Max KEEPALIVE probes to send before killing connection'),
    cfg.IntOpt('keepidle',
               metavar='SECONDS',
               help='Seconds of idle time before sending KEEPALIVE probes'),
    cfg.IntOpt('keepintvl',
               metavar='SECONDS',
               help='Seconds between TCP KEEPALIVE probes'),
    cfg.IntOpt('poll',
               default=1,
               metavar='SECONDS',
               help='Gearman worker polling timeout'),
    cfg.IntOpt('reconnect_sleep',
               default=60,
               metavar='SECONDS',
               help='Seconds to sleep between job server reconnects'),
    cfg.ListOpt('servers',
                default=['localhost:4730'],
                metavar='HOST:PORT,...',
                help='List of Gearman job servers'),
    cfg.StrOpt('ssl_ca',
               metavar='FILE',
               help='Gearman SSL certificate authority'),
    cfg.StrOpt('ssl_cert',
               metavar='FILE',
               help='Gearman SSL certificate'),
    cfg.StrOpt('ssl_key',
               metavar='FILE',
               help='Gearman SSL key'),
]


def add_common_opts():
    CONF.register_opts(gearman_opts, group='gearman')
    CONF.register_cli_opts(common_cli_opts)


def check_gearman_ssl_files():
    """
    If using Gearman with SSL, validate that the SSL files exist and
    are readable by the user. It's a common problem that connections to
    Gearman will silently fail because these files cannot be read due to
    the private key being readable only by the file owner.
    """
    if 'gearman' not in CONF:
        return
    for key in ['ssl_ca', 'ssl_cert', 'ssl_key']:
        if key in CONF['gearman']:
            fname = CONF['gearman'][key]
            if fname is None:
                continue
            if not os.path.exists(fname):
                raise Exception("Gearman SSL file %s does not exist" % fname)
            if not os.access(fname, os.R_OK):
                raise Exception("Unable to read Gearman SSL file %s" % fname)
