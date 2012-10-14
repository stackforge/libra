import unittest
import json
import mock
import httplib2
import sys
from StringIO import StringIO
from libra.client.libraapi import LibraAPI

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


class TestLBaaSClientLibraAPI(unittest.TestCase):
    def setUp(self):
        self.api = LibraAPI('username', 'password', 'tenant', 'auth_test', 'region')
        self.api.nova.management_url = "http://example.com"
        self.api.nova.auth_token = "token"

    def tearDown(self):
        pass

    def testListLb(self):
        with mock.patch.object(httplib2.Http, "request", mock_request):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                orig = sys.stdout
                try:
                    out = StringIO()
                    sys.stdout = out
                    self.api.list_lb()
                    output = out.getvalue().strip()
                    self.assertRegexpMatches(output, 'LEAST_CONNECTIONS')
                finally:
                    sys.stdout = orig
