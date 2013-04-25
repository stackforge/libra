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
    _default = {'status':'404'}

    """not found """
    not_found = {'message':'Object not Found'}

    """service_unavailable"""
    service_unavailable = {'message':'Service Unavailable'}

    """algorithms response"""
    algorithms = {
        'algorithms':[
            {'name':'ROUND_ROBIN'},
            {'name':'LEAST_CONNECTIONS'}
        ]
    }

    """protocols response"""
    protocols = {
        'protocols':[
            {
                'name':'HTTP',
                'port':'80'
            },
            {
                'name':'HTTPS',
                'port':'443'
            },
            {
                'name':'TCP',
                'port':'*'
            }
        ]
    }


    """class LoadBalancers
    grouping of lb responses
    """
    class LoadBalancers(object):
        """LoadBalancers list"""
        get = {
            'loadBalancers':[
                {
                    'name':'lb-site1',
                    'id':'71',
                    'protocol':'HTTP',
                    'port':'80',
                    'algorithm':'LEAST_CONNECTIONS',
                    'status':'ACTIVE',
                    'created':'2010-11-30T03:23:42Z',
                    'updated':'2010-11-30T03:23:44Z'
                },
                {
                    'name':'lb-site2',
                    'id':'166',
                    'protocol':'TCP',
                    'port':'9123',
                    'algorithm':'ROUND_ROBIN',
                    'status':'ACTIVE',
                    'created':'2010-11-30T03:23:42Z',
                    'updated':'2010-11-30T03:23:44Z'
                }
            ]
        }

        """loadbalancer details"""
        detail = {
            'id':'2000',
            'name':'sample-loadbalancer',
            'protocol':'HTTP',
            'port':'80',
            'algorithm':'ROUND_ROBIN',
            'status':'ACTIVE',
            'created':'2010-11-30T03:23:42Z',
            'updated':'2010-11-30T03:23:44Z',
            'virtualIps':[
                {
                    'id':'1000',
                    'address':'2001:cdba:0000:0000:0000:0000:3257:9652',
                    'type':'PUBLIC',
                    'ipVersion':'IPV6'
                }
            ],
           'nodes':[
                {
                    'id':'1041',
                    'address':'10.1.1.1',
                    'port':'80',
                    'condition':'ENABLED',
                    'status':'ONLINE'
                },
                {
                    'id':'1411',
                    'address':'10.1.1.2',
                    'port':'80',
                    'condition':'ENABLED',
                    'status':'ONLINE'
                }
            ],
            'sessionPersistence':{
                'persistenceType':'HTTP_COOKIE'
            },
            'connectionThrottle':{
                'maxRequestRate':'50',
                'rateInterval':'60'
            }
        }

        """create loadbalancer response"""
        post = {
            'name':'a-new-loadbalancer',
            'id':'144',
            'protocol':'HTTP',
            'port':'83',
            'algorithm':'ROUND_ROBIN',
            'status':'BUILD',
            'created':'2011-04-13T14:18:07Z',
            'updated':'2011-04-13T14:18:07Z',
            'virtualIps':[
                {
                    'address':'3ffe:1900:4545:3:200:f8ff:fe21:67cf',
                    'id':'39',
                    'type':'PUBLIC',
                    'ipVersion':'IPV6'
                }
            ],
            'nodes':[
                {
                    'address':'10.1.1.1',
                    'id':'653',
                    'port':'80',
                    'status':'ONLINE',
                    'condition':'ENABLED'
                }
            ]
        }

        """virtualips"""
        virtualips = {
            'virtualIps':[
                {
                    'id':'1021',
                    'address':'206.10.10.210',
                    'type':'PUBLIC',
                    'ipVersion':'IPV4'
                }
            ]
        }

        """usage"""
        usage = {
            'loadBalancerUsageRecords':[
                {
                    'id':'394',
                    'transferBytesIn':'2819204',
                    'transferBytesOut':'84923069'
                },
                {
                    'id':'473',
                    'transferBytesIn':'0',
                    'transferBytesOut':'0'
                }
            ]
        }

        """class HealthMonitor
        monitor responses
        """
        class HealthMonitor(object):
            """monitor CONNECT response"""
            get = {
                'type':'CONNECT',
                'delay':'20',
                'timeout':'10',
                'attemptsBeforeDeactivation':'3'
            }
            """monitor HTTPS response"""
            get_https = {
               'type':'HTTPS',
               'delay':'10',
               'timeout':'3',
               'attemptsBeforeDeactivation':'3',
               'path':'/healthcheck'
            }
        """class SessionPersistence
        for managing Session Persistance
        """
        class SessionPersistence(object):
            """get"""
            get = {
                'persistenceType':'HTTP_COOKIE'
            }
        """class Connections
        Throttle Connections responses
        """
        class ConnectionThrottle(object):
            """get"""
            get = {
                'maxRequestRate':'50',
                'rateInterval':'60'
            }


        """class Nodes
        grouping of node related responses
        """
        class Nodes(object):
            """list of nodes of a specific lb"""
            get = {
                'nodes':[
                    {
                        'id':'410',
                        'address':'10.1.1.1',
                        'port':'80',
                        'condition':'ENABLED',
                        'status':'ONLINE'
                    },
                    {
                        'id':'236',
                        'address':'10.1.1.2',
                        'port':'80',
                        'condition':'ENABLED',
                        'status':'ONLINE'
                    },
                    {
                        'id':'2815',
                        'address':'10.1.1.3',
                        'port':'83',
                        'condition':'DISABLED',
                        'status':'OFFLINE'
                    },
                ]
            }

            """a specific node details"""
            get_detail = {
                'id':'236',
                'address':'10.1.1.2',
                'port':'80',
                'condition':'ENABLED',
                'status':'ONLINE'
            }

            """nodes create response"""
            post = {
                'nodes':[
                    {
                        'id':'7298',
                        'address':'10.1.1.1',
                        'port':'80',
                        'condition':'ENABLED',
                        'status':'ONLINE'
                    },
                    {
                        'id':'293',
                        'address':'10.2.2.1',
                        'port':'80',
                        'weight':'2',
                        'condition':'ENABLED',
                        'status':'OFFLINE'
                    },
                    {
                        'id':'183',
                        'address':'10.2.2.4',
                        'port':'88',
                        'weight':'2',
                        'condition':'DISABLED',
                        'status':'OFFLINE'
                    }
               ]
            }
