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

from libra.common.json_gearman import JSONGearmanClient
from pecan import conf


gearman_client = JSONGearmanClient(conf.gearman.server)

gearman_workers = [
    'UPDATE', # Create/Update a Load Balancer.
    'SUSPEND', # Suspend a Load Balancer.
    'ENABLE', # Enable a suspended Load Balancer.
    'DELETE', # Delete a Load Balancer.
    'DISCOVER',  # Return service discovery information.
    'ARCHIVE', # Archive LB log files.
    'STATS' # Get load balancer statistics.
]