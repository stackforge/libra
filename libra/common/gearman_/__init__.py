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
import gearman
from stevedore.driver import DriverManager

from libra.common.options import CONF
from libra.common.gearman_.encoders import get_encoder


GEARMAN_OPTS = [
    cfg.StrOpt('encoder', default='json', help='Encoder plugin to use'),
    cfg.StrOpt('driver', default='gearman', help='Gearman driver')
]

cfg.CONF.register_opts(GEARMAN_OPTS, group='gearman')


def get_server_list():
    server_list = []
    for host_port in CONF['gearman']['servers']:
        host, port = host_port.split(':')
        server_list.append({'host': host,
                            'port': int(port),
                            'keyfile': CONF['gearman']['ssl_key'],
                            'certfile': CONF['gearman']['ssl_cert'],
                            'ca_certs': CONF['gearman']['ssl_ca'],
                            'keepalive': CONF['gearman']['keepalive'],
                            'keepcnt': CONF['gearman']['keepcnt'],
                            'keepidle': CONF['gearman']['keepidle'],
                            'keepintvl': CONF['gearman']['keepintvl']})
    return server_list


def get_cls(name):
    mgr = DriverManager('libra.rpc_plugins', name)
    return mgr.driver


class GearmanWorker(gearman.GearmanWorker):
    """ Overload the Gearman worker class so we can set the data encoder. """
    def __init__(self, *args, **kw):
        super(GearmanWorker, self).__init__(*args, **kw)
        self.data_encoder = get_encoder(cfg.CONF.gearman.encoder)


class GearmanClient(gearman.GearmanClient):
    """ Overload the Gearman client class so we can set the data encoder. """
    def __init__(self, *args, **kw):
        super(GearmanClient, self).__init__(*args, **kw)
        self.data_encoder = get_encoder(cfg.CONF.gearman.encoder)
