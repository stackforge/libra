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

from libra.admin_api.stats.drivers.base import AlertDriver
from libra.openstack.common import log


LOG = log.getLogger(__name__)


class DummyDriver(AlertDriver):
    def send_alert(self, message, device_id, device_ip, device_name, device_tenant):
        LOG.info('Dummy alert of: {0}'.format(message))

    def send_delete(self, message, device_id, device_ip, device_name):
        LOG.info('Dummy delete of: {0}'.format(message))

    def send_node_change(self, message, lbid, degraded):
        LOG.info('Dummy node change of: {0}'.format(message))
