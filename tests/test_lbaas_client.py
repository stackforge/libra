import json
import mock
import httplib2
import sys
import novaclient
import testtools
from StringIO import StringIO
from libra.client.libraapi import LibraAPI

class DummyArgs(object):
    """ Fake argparse response """
    def __init__(self):
        self.id = 2000
        self.deleted = False

class DummyCreateArgs(object):
    """ Fake argparse response for Create function """
    def __init__(self):
        self.name = 'a-new-loadbalancer'
        self.node = ['10.1.1.1:80', '10.1.1.2:81']
        self.port = None
        self.protocol = None
        self.algorithm = None
        self.vip = None

class DummyModifyArgs(object):
    """ Fake argparse response for Modify function """
    def __init__(self):
        self.id = 2012
        self.name = 'a-modified-loadbalancer'
        self.algorithm = 'LEAST_CONNECTIONS'

class MockLibraAPI(LibraAPI):
    """ Used to capture data that would be sent to the API server """
    def __init__(self, username, password, tenant, auth_url, region):
        self.postdata = None
        self.putdata = None
        return super(MockLibraAPI, self).__init__(username, password, tenant, auth_url, region, False, False, None)
    def _post(self, url, **kwargs):
        """ Store the post data and execute as normal """
        self.postdata = kwargs['body']
        return super(MockLibraAPI, self)._post(url, **kwargs)
    def _put(self, url, **kwargs):
        """ Store the put data, no need to execute the httplib """
        self.putdata = kwargs['body']

class TestLBaaSClientLibraAPI(testtools.TestCase):
    def setUp(self):
        """ Fake a login with token """
        super(TestLBaaSClientLibraAPI, self).setUp()
        self.api = MockLibraAPI('username', 'password', 'tenant', 'auth_test', 'region')
        self.api.nova.management_url = "http://example.com"
        self.api.nova.auth_token = "token"

    def testListLb(self):
        """ Test the table generated from the LIST function """
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
                    args = DummyArgs()
                    self.api.list_lb(args)
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
        """ Test the table generated from the STATUS function """
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

    def testDeleteFailLb(self):
        """
        Test a failure of a DELETE function.  We don't test a succeed yet
        since that has no response so nothing to assert on
        """
        fake_response = httplib2.Response({"status": '500'})
        fake_body = ''
        mock_request = mock.Mock(return_value=(fake_response, fake_body))
        with mock.patch.object(httplib2.Http, "request", mock_request):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                args = DummyArgs()
                self.assertRaises(novaclient.exceptions.ClientException,
                                  self.api.delete_lb, args)

    def testCreateLb(self):
        """
        Tests the CREATE function, tests that:
        1. We send the correct POST data
        2. We create a table from the response correctly
        """
        fake_response = httplib2.Response({"status": '202'})
        fake_body = json.dumps({
            'name': 'a-new-loadbalancer',
            'id': '144',
            'protocol': 'HTTP',
            'port': '83',
            'algorithm': 'ROUND_ROBIN',
            'status': 'BUILD',
            'created': '2011-04-13T14:18:07Z',
            'updated': '2011-04-13T14:18:07Z',
            'virtualIps': [
                    {
                        'address': '15.0.0.1',
                        'id': '39',
                        'type': 'PUBLIC',
                        'ipVersion': 'IPV4',
                    }
                ],
            'nodes': [
                    {
                        'address': '10.1.1.1',
                        'id': '653',
                        'port': '80',
                        'status': 'ONLINE',
                        'condition': 'ENABLED'
                    }
                ]
            })
        # This is what the POST data should look like based on the args passed
        post_compare = {
                    "name": "a-new-loadbalancer",
                    "nodes": [
                                {
                                    "address": "10.1.1.1",
                                    "condition": "ENABLED",
                                    "port": "80"
                                },
                                {
                                    "address": "10.1.1.2",
                                    "condition": "ENABLED",
                                    "port": "81"
                                }
                             ]
                        }
        mock_request = mock.Mock(return_value=(fake_response, fake_body))
        with mock.patch.object(httplib2.Http, "request", mock_request):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                orig = sys.stdout
                try:
                    out = StringIO()
                    sys.stdout = out
                    args = DummyCreateArgs()
                    self.api.create_lb(args)
                    self.assertEquals(post_compare, self.api.postdata)
                    output = out.getvalue().strip()
                    # At some point we should possibly compare the complete
                    # table rendering somehow instead of basic field data
                    self.assertRegexpMatches(output, 'ROUND_ROBIN')
                    self.assertRegexpMatches(output, 'BUILD')
                    self.assertRegexpMatches(output, '144')
                finally:
                    sys.stdout = orig

    def testCreateAddLb(self):
        """
        Tests the CREATE function as above but adding a load balancer to a
        virtual IP
        """
        fake_response = httplib2.Response({"status": '202'})
        fake_body = json.dumps({
            'name': 'a-new-loadbalancer',
            'id': '144',
            'protocol': 'HTTP',
            'port': '83',
            'algorithm': 'ROUND_ROBIN',
            'status': 'BUILD',
            'created': '2011-04-13T14:18:07Z',
            'updated': '2011-04-13T14:18:07Z',
            'virtualIps': [
                    {
                        'address': '15.0.0.1',
                        'id': '39',
                        'type': 'PUBLIC',
                        'ipVersion': 'IPV4',
                    }
                ],
            'nodes': [
                    {
                        'address': '10.1.1.1',
                        'id': '653',
                        'port': '80',
                        'status': 'ONLINE',
                        'condition': 'ENABLED'
                    }
                ]
            })
        # This is what the POST data should look like based on the args passed
        post_compare = {
                    "name": "a-new-loadbalancer",
                    "port": "83",
                    "protocol": "HTTP",
                    "virtualIps": [
                                    {
                                        "id": "39"
                                    }
                                  ],
                    "nodes": [
                                {
                                    "address": "10.1.1.1",
                                    "condition": "ENABLED",
                                    "port": "80"
                                }
                             ]
                        }
        mock_request = mock.Mock(return_value=(fake_response, fake_body))
        with mock.patch.object(httplib2.Http, "request", mock_request):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                orig = sys.stdout
                try:
                    out = StringIO()
                    sys.stdout = out
                    # Add args to add a LB to a VIP
                    args = DummyCreateArgs()
                    args.port = '83'
                    args.protocol = 'HTTP'
                    args.vip = '39'
                    args.node = ['10.1.1.1:80']
                    self.api.create_lb(args)
                    self.assertEquals(post_compare, self.api.postdata)
                    output = out.getvalue().strip()
                    # At some point we should possibly compare the complete
                    # table rendering somehow instead of basic field data
                    self.assertRegexpMatches(output, 'ROUND_ROBIN')
                    self.assertRegexpMatches(output, 'BUILD')
                    self.assertRegexpMatches(output, '144')
                finally:
                    sys.stdout = orig


    def testModifyLb(self):
        """
        Tests the MODIFY function, no repsonse so we only test the PUT data
        """
        # This is what the PUT data should look like based on the args passed
        put_compare = {
                        "name": "a-modified-loadbalancer",
                        "algorithm": "LEAST_CONNECTIONS" 
                       }
        args = DummyModifyArgs()
        self.api.modify_lb(args)
        self.assertEquals(put_compare, self.api.putdata)
