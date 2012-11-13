#!/usr/bin/env python

import json
import socket
from gearman import GearmanClient, DataEncoder


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
    my_ip = socket.gethostbyname(socket.gethostname())
    task = "lbaas-%s" % my_ip
    client = JSONGearmanClient(['localhost:4730'])
    data = """
{
    "hpcs_action": "create",
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
