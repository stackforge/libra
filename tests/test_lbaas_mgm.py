import unittest
import logging
import mock
import httplib2
import json

import mock_objects
from libra.mgm.nova import Node, BuildError

fake_response = httplib2.Response({"status": '200'})
fake_bad_response = httplib2.Response({"status": '500'})
fake_del_response = httplib2.Response({"status": '204'})
fake_body = json.dumps({u'server': {u'status': u'ACTIVE', u'updated': u'2012-10-10T11:55:55Z', u'hostId': u'', u'user_id': u'18290556240782', u'name': u'lbass_0', u'links': [{u'href': u'https://az-1.region-a.geo-1.compute.hpcloudsvc.com/v1.1/58012755801586/servers/417773', u'rel': u'self'}, {u'href': u'https://az-1.region-a.geo-1.compute.hpcloudsvc.com/58012755801586/servers/417773', u'rel': u'bookmark'}], u'created': u'2012-10-10T11:55:55Z', u'tenant_id': u'58012755801586', u'image': {u'id': u'8419', u'links': [{u'href': u'https://az-1.region-a.geo-1.compute.hpcloudsvc.com/58012755801586/images/8419', u'rel': u'bookmark'}]}, u'adminPass': u'u2LKPA73msRTxDMC', u'uuid': u'14984389-8cc5-4780-be64-2d31ace662ad', u'accessIPv4': u'', u'metadata': {}, u'accessIPv6': u'', u'key_name': u'default', u'flavor': {u'id': u'100', u'links': [{u'href': u'https://az-1.region-a.geo-1.compute.hpcloudsvc.com/58012755801586/flavors/100', u'rel': u'bookmark'}]}, u'config_drive': u'', u'id': 417773, u'security_groups': [{u'name': u'default', u'links': [{u'href': u'https://az-1.region-a.geo-1.compute.hpcloudsvc.com/v1.1/58012755801586/os-security-groups/4008', u'rel': u'bookmark'}], u'id': 4008}], u'addresses': {}}})
mock_request = mock.Mock(return_value=(fake_response, fake_body))
mock_bad_request = mock.Mock(return_value=(fake_bad_response, ""))
mock_del_request = mock.Mock(return_value=(fake_del_response, ""))


class TestLBaaSMgmTask(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger('lbass_mgm_test')
        self.lh = mock_objects.MockLoggingHandler()
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.lh)

    def tearDown(self):
        pass


class TestLBaaSMgmNova(unittest.TestCase):
    def setUp(self):
        self.api = Node(
            "username", "password", "auth_test", "tenant1", "region1",
            "default", "default", '1234', '100'
        )
        self.api.nova.management_url = "http://example.com"
        self.api.nova.auth_token = "token"

    def tearDown(self):
        pass

    def testCreateNode(self):
        with mock.patch.object(httplib2.Http, "request", mock_request):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                data = self.api.build()
                self.assertEqual(data['id'], 417773)

    def testCreateNodeFail(self):
        with mock.patch.object(httplib2.Http, "request", mock_bad_request):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                with self.assertRaises(BuildError):
                    data = self.api.build()

    def testDeleteNodeFail(self):
        with mock.patch.object(httplib2.Http, "request", mock_bad_request):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                resp, data = self.api.delete('1234')
                self.assertFalse(resp)

    def testDeleteNodeSucceed(self):
        with mock.patch.object(httplib2.Http, "request", mock_del_request):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                resp, data = self.api.delete('1234')
                self.assertTrue(resp)
