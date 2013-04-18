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

from libra.statsd.drivers.base import AlertDriver
from dogapi import dog_http_api as api


class DatadogDriver(AlertDriver):
    def __init__(self, logger, args):
        api.api_key = args.datadog_api_key
        api.application_key = args.datadog_app_key
        super(DatadogDriver, self).__init__(logger, args)

    def send_alert(self, message, device_id):
        title = 'Load balancer failure'
        text = 'Load balancer failed with message {0} {1}'.format(
            message, self.args.datadog_message_tail
        )
        tags = self.args.datadog_tags.split()
        resp = api.event_with_response(
            title, text, tags=tags, alert_type='error'
        )
        self.logger.info('Datadog alert response: {0}'.format(resp))

    def send_repair(self, message, device_id):
        title = 'Load balancer recovered'
        text = 'Load balancer recovered with message {0} {1}'.format(
            message, self.args.datadog_message_tail
        )
        tags = self.args.datadog_tags.split()
        resp = api.event_with_response(
            title, text, tags=tags, alert_type='success'
        )
        self.logger.info('Datadog alert response: {0}'.format(resp))
