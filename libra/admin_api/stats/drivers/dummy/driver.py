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


class DummyDriver(AlertDriver):
    def send_alert(self, message, device_id):
        self.logger.info('Dummy alert of: {0}'.format(message))

    def send_repair(self, message, dervice_id):
        self.logger.info('Dummy repair of: {0}'.format(message))
