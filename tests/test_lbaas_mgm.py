import unittest
import logging
import mock
import httplib2

import mock_objects
from libra.mgm.nova import Node

fake_response = httplib2.Response({"status": 200})
fake_bad_response = httplib2.Response({"status": 500})
fake_del_response = httplib2.Response({"status": 204})
fake_body = '{"hi": "there"}'
mock_request = mock.Mock(return_value=(fake_response, fake_body))
mock_bad_request = mock.Mock(return_value=(fake_bad_response, fake_body))
mock_del_request = mock.Mock(return_value=(fake_del_response, fake_body))


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
        @mock.patch.object(httplib2.Http, "request", mock_request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def testCreateCall():
            data = self.api.create('4321', '123', '321')
            self.assertEqual(data, {"hi": "there"})

    def testDeleteNodeFail(self):
        @mock.patch.object(httplib2.Http, "request", mock_bad_request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def testDeleteCall():
            resp = self.api.delete('1234')
            self.assertEqual(resp, 1)

    def testDeleteNodeSucceed(self):
        @mock.patch.object(httplib2.Http, "request", mock_del_request)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def testDeleteCall():
            resp = self.api.delete('1234')
            self.assertEqual(resp, 0)
