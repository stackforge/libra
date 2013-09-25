# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the 'License'); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Class Responses
responder objects for framework.
"""


class Responses(object):
    """404 - not found"""
    _default = {'status': '404', 'message': 'Object not Found'}

    """not found """
    not_found = {'message': 'Object not Found'}

    """service_unavailable"""
    service_unavailable = {'message': 'Service Unavailable'}

    """algorithms response"""
    algorithms = {
        'algorithms': [
            {'name': 'ROUND_ROBIN'},
            {'name': 'LEAST_CONNECTIONS'}
        ]
    }

    """protocols response"""
    protocols = {
        'protocols': [
            {
                'name': 'HTTP',
                'port': '80'
            },
            {
                'name': 'TCP',
                'port': '443'
            },
            {
                'name': 'GALERA',
                'port': '3306'
            }
        ]
    }

    versions = {
        "versions": [
            {
                "id": "v1.1",
                "updated": "2012-12-18T18:30:02.25Z",
                "status": "CURRENT",
                "links": [
                    {
                        "rel": "self",
                        "href": "http://wiki.openstack.org/Atlas-LB"
                    }
                ]
            }
        ]
    }

    v1_1 = {
        "version": {
            "id": "v1.1",
            "updated": "2012-12-18T18:30:02.25Z",
            "status": "CURRENT",
            "links": [
                {
                    "rel": "self",
                    "href": "http://wiki.openstack.org/Atlas-LB"
                }
            ],
            "media-types": [
                {
                    "base": "application/json"
                }
            ]
        }
    }
