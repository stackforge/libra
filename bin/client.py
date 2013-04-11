#!/usr/bin/env python
##############################################################################
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################

import json
import socket
from gearman import GearmanClient, DataEncoder, JOB_UNKNOWN


class JSONDataEncoder(DataEncoder):
    @classmethod
    def encode(cls, encodable_object):
        s = json.dumps(encodable_object)
        print("Encoding JSON object to string: %s" % s)
        return s

    @classmethod
    def decode(cls, decodable_string):
        s = json.loads(decodable_string)
        print("Decoding string (%s) to JSON object" % s)
        return s


class JSONGearmanClient(GearmanClient):
    data_encoder = JSONDataEncoder


def check_request_status(job_request):
    if job_request.complete:
        print "Job %s finished!  Result: %s -\n%s" % (job_request.job.unique,
                                                      job_request.state,
                                                      json.dumps(
                                                          job_request.result,
                                                          indent=2
                                                      ))
    elif job_request.timed_out:
        print "Job %s timed out!" % job_request.unique
    elif job_request.state == JOB_UNKNOWN:
        print "Job %s connection failed!" % job_request.unique


def main():
    hostname = socket.gethostname()
    task = hostname
    client = JSONGearmanClient(['localhost:4730'])
    data = """
{
    "hpcs_action": "update",
    "loadbalancers": [
        {
            "name": "a-new-loadbalancer",
            "protocol": "http",
            "nodes": [
                {
                    "address": "10.1.1.1",
                    "port": "80"
                },
                {
                    "address": "10.1.1.2",
                    "port": "81"
                }
            ]
        }
    ]
}
"""

    # Worker class expects the data as a JSON object, not string
    json_data = json.loads(data)
    request = client.submit_job(task, json_data)
    check_request_status(request)

if __name__ == "__main__":
    main()
