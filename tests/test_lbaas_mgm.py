import testtools
import logging
import mock
import os
import requests

import mock_objects
from libra.mgm.nova import Node, BuildError

fake_body = open(
    os.path.join((os.path.dirname(__file__), "fake_body.json"))).read()


class TestResponse(requests.Response):
    """
    Class used to wrap requests.Response and provide some
    convenience to initialize with a dict
    """

    def __init__(self, data):
        self._text = None
        super(TestResponse, self)
        if isinstance(data, dict):
            self.status_code = data.get('status', None)
            self.headers = data.get('headers', None)
            # Fake the text attribute to streamline Response creation
            self._text = data.get('text', None)
        else:
            self.status_code = data

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @property
    def text(self):
        return self._text


fake_response = TestResponse({"status": 200, "text": fake_body})
fake_bad_response = TestResponse({"status": 500, "text": ""})
fake_del_response = TestResponse({"status": 204, "text": ""})
mock_request = mock.Mock(return_value=(fake_response))
mock_bad_request = mock.Mock(return_value=(fake_bad_response))
mock_del_request = mock.Mock(return_value=(fake_del_response))


class TestLBaaSMgmTask(testtools.TestCase):
    def setUp(self):
        super(TestLBaaSMgmTask, self).setUp()
        self.logger = logging.getLogger('lbass_mgm_test')
        self.lh = mock_objects.MockLoggingHandler()
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.lh)


class TestLBaaSMgmNova(testtools.TestCase):
    def setUp(self):
        super(TestLBaaSMgmNova, self).setUp()
        self.api = Node(
            "username", "password", "auth_test", "tenant1", "region1",
            "default", "default", '1234', '100'
        )
        self.api.nova.management_url = "http://example.com"
        self.api.nova.auth_token = "token"

    def testCreateNode(self):
        with mock.patch.object(requests, "request", mock_request):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                data = self.api.build()
                self.assertEqual(data['id'], 417773)

    def testCreateNodeFail(self):
        with mock.patch.object(requests, "request", mock_bad_request):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                self.assertRaises(BuildError, self.api.build)

    def testDeleteNodeFail(self):
        with mock.patch.object(requests, "request", mock_bad_request):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                resp, data = self.api.delete('1234')
                self.assertFalse(resp)

    def testDeleteNodeSucceed(self):
        with mock.patch.object(requests, "request", mock_del_request):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                resp, data = self.api.delete('1234')
                self.assertTrue(resp)
