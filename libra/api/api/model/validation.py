# vim: tabstop=4 shiftwidth=4 softtabstop=4
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

class Validation(object):
    """class Validatoin
    Validation templates for validict lib
    """
    """loadbalancer_create"""
    loadbalancer_create = {
        "name": "a-new-loadbalancer",
        "nodes":[
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
     """nodes_create"""
     nodes_create = {
        "nodes":[
            {
                "address": "10.1.1.1",
                "port": "80"
            },
            {
                "address": "10.2.2.1",
                "port": "80",
                "weight": "2"
            },
            {
                "address": "10.2.2.2",
                "port": "88",
                "condition": "DISABLED",
                "weight": "2"
            }
        ]
    }
    """monitor CONNECT request"""
    monitor_connect = {
        "type": "CONNECT",
        "delay": "20",
        "timeout": "10",
        "attemptsBeforeDeactivation": "3"
    }
