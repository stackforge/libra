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

from dogapi import dog_http_api as api
from oslo.config import cfg

from libra.admin_api.stats.drivers.base import AlertDriver
from libra.openstack.common import log


LOG = log.getLogger(__name__)


class DatadogDriver(AlertDriver):
    def __init__(self):
        super(DatadogDriver, self).__init__()
        api.api_key = cfg.CONF['admin_api']['datadog_api_key']
        api.application_key = cfg.CONF['admin_api']['datadog_app_key']
        self.dd_env = cfg.CONF['admin_api']['datadog_env']
        self.dd_tags = cfg.CONF['admin_api']['datadog_tags']
        self.dd_message_tail = cfg.CONF['admin_api']['datadog_message_tail']

    def send_alert(self, message, device_id, device_ip, device_name, device_tenant):
        title = 'Load balancer failure in {0}: {1} {2} {3} {4}'.format(
            self.dd_env, device_id, device_ip, device_name, device_tenant)
        text = 'Load balancer failed with message {0} {1}'.format(
            message, self.dd_message_tail
        )
        tags = self.dd_tags.split()
        resp = api.event_with_response(
            title, text, tags=tags, alert_type='error'
        )
        LOG.info('Datadog alert response: {0}'.format(resp))

    def send_delete(self, message, device_id, device_ip, device_name):
        title = 'Load balancer unreachable in {0}: {1} {2}'.\
            format(self.dd_env, device_ip, device_name)
        text = 'Load balancer unreachable with message {0} {1}'.format(
            message, self.dd_message_tail
        )
        tags = self.dd_tags.split()
        resp = api.event_with_response(
            title, text, tags=tags, alert_type='success'
        )
        LOG.info('Datadog alert response: {0}'.format(resp))
