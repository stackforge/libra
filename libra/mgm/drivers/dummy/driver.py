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

from libra.mgm.drivers.base import MgmDriver


class DummyDriver(MgmDriver):
    """
    Pool manager dummy driver for testing
    """
    def __init__(self, addresses, logger):
        self.logger = logger

    def get_free_count(self):
        return 5

    def is_online(self):
        return True

    def add_node(self, node_data):
        self.logger.info('Dummy API send of {0}'.format(node_data))
        return True, 'test response'

    def get_url(self):
        return 'Dummy Connection'
