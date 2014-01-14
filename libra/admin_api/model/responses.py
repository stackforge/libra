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

    versions = {
        "versions": [
            {
                "id": "v1",
                "updated": "2014-01-13T16:55:25Z",
                "status": "DEPRECATED"
            },
            {
                "id": "v2.2",
                "updated": "2014-01-13T16:55:25Z",
                "status": "CURRENT"
            }
        ]
    }

    versions_v1 = {
        "version": {
            "id": "v1",
            "updated": "2014-01-13T16:55:25Z",
            "status": "DEPRECATED",
            "media-types": [
                {
                    "base": "application/json"
                }
            ]
        }
    }

    versions_v2_0 = {
        "version": {
            "id": "v2",
            "updated": "2014-01-13T16:55:25Z",
            "status": "DEPRECATED",
            "media-types": [
                {
                    "base": "application/json"
                }
            ]
        }
    }
