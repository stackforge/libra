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
from libra.common.options import CONF
from libra.common.gearman_.serializers import JSONDataEncoder
import gearman


class GearmanWorker(gearman.GearmanWorker):
    """ Overload the Gearman worker class so we can set the data encoder. """
    data_encoder = JSONDataEncoder


class GearmanClient(gearman.GearmanClient):
    """ Overload the Gearman client class so we can set the data encoder. """
    data_encoder = JSONDataEncoder


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
