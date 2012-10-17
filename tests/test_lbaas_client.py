import unittest
import json
import mock
import httplib2
import sys
from StringIO import StringIO
from libra.client.libraapi import LibraAPI

class DummyArgs(object):
    def __init__(self):
        self.lbid = 2000


class TestLBaaSClientLibraAPI(unittest.TestCase):
    def setUp(self):
        self.api = LibraAPI('username', 'password', 'tenant', 'auth_test', 'region')
        self.api.nova.management_url = "http://example.com"
        self.api.nova.auth_token = "token"

    def tearDown(self):
        pass

    def testListLb(self):
        fake_response = httplib2.Response({"status": '200'})
        fake_body = json.dumps({
            "loadBalancers":[
                {
                    "name":"lb-site1",
                    "id":"71",
                    "protocol":"HTTP",
                    "port":"80",
                    "algorithm":"LEAST_CONNECTIONS",
                    "status":"ACTIVE",
                    "created":"2010-11-30T03:23:42Z",
                    "updated":"2010-11-30T03:23:44Z"
                },
                {
                    "name":"lb-site2",
                    "id":"166",
                    "protocol":"TCP",
                    "port":"9123",
                    "algorithm":"ROUND_ROBIN",
                    "status":"ACTIVE",
                    "created":"2010-11-30T03:23:42Z",
                    "updated":"2010-11-30T03:23:44Z"
                }
            ]
        })
        mock_request = mock.Mock(return_value=(fake_response, fake_body))

        with mock.patch.object(httplib2.Http, "request", mock_request):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                orig = sys.stdout
                try:
                    out = StringIO()
                    sys.stdout = out
                    self.api.list_lb(None)
                    output = out.getvalue().strip()
                    self.assertRegexpMatches(output, 'lb-site1')
                    self.assertRegexpMatches(output, '71')
                    self.assertRegexpMatches(output, 'HTTP')
                    self.assertRegexpMatches(output, '80')
                    self.assertRegexpMatches(output, 'LEAST_CONNECTIONS')
                    self.assertRegexpMatches(output, 'ACTIVE')
                    self.assertRegexpMatches(output, '2010-11-30T03:23:42Z')
                    self.assertRegexpMatches(output, '2010-11-30T03:23:44Z')
                finally:
                    sys.stdout = orig

    def testGetLb(self):
        fake_response = httplib2.Response({"status": '200'})
        fake_body = json.dumps({
            "id": "2000",
            "name":"sample-loadbalancer",
            "protocol":"HTTP",
            "port": "80",
            "algorithm":"ROUND_ROBIN",
            "status":"ACTIVE",
            "created":"2010-11-30T03:23:42Z",
            "updated":"2010-11-30T03:23:44Z",
            "virtualIps":[
            {
                "id": "1000",
                "address":"2001:cdba:0000:0000:0000:0000:3257:9652",
                "type":"PUBLIC",
                "ipVersion":"IPV6"
            }],
            "nodes": [
            {
                "id": "1041",
                "address":"10.1.1.1",
                "port": "80",
                "condition":"ENABLED",
                "status":"ONLINE"
            },
            {
                "id": "1411",
                "address":"10.1.1.2",
                "port": "80",
                "condition":"ENABLED",
                "status":"ONLINE"
            }],
            "sessionPersistence":{
                "persistenceType":"HTTP_COOKIE"
            },
            "connectionThrottle":{
                "maxRequestRate": "50",
                "rateInterval": "60"
            }
        })
        mock_request = mock.Mock(return_value=(fake_response, fake_body))
        with mock.patch.object(httplib2.Http, "request", mock_request):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                orig = sys.stdout
                try:
                    out = StringIO()
                    sys.stdout = out
                    args = DummyArgs()
                    self.api.status_lb(args)
                    output = out.getvalue().strip()
                    self.assertRegexpMatches(output, 'HTTP_COOKIE')
                finally:
                    sys.stdout = orig

