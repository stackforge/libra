import json
import logging
import unittest
import mock
from libra.worker.worker import lbaas_task
from libra.worker.drivers.base import LoadBalancerDriver


class FakeDriver(LoadBalancerDriver):
    pass


class FakeJob(object):
    def __init__(self, data):
        """
        data: JSON object to convert to a string
        """
        self.data = data


class FakeWorker(object):
    def __init__(self):
        self.logger = logging.getLogger('lbaas_worker_test')
        self.driver = FakeDriver()


class TestLBaaSTask(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testLBaaSTask(self):
        """ Test the lbaas_task() function """

        worker = FakeWorker()
        data = {
            "name": "a-new-loadbalancer",
            "nodes": [
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

        job = FakeJob(data)
        r = lbaas_task(worker, job)

        self.assertEqual(r["name"], data["name"])
        self.assertEqual(len(r["nodes"]), 2)
        self.assertEqual(r["nodes"][0]["address"], data["nodes"][0]["address"])
        self.assertEqual(r["nodes"][0]["port"], data["nodes"][0]["port"])
        self.assertIn("condition", r["nodes"][0])
        self.assertEqual(r["nodes"][1]["address"], data["nodes"][1]["address"])
        self.assertEqual(r["nodes"][1]["port"], data["nodes"][1]["port"])
        self.assertIn("condition", r["nodes"][1])

    def testMissingNodes(self):
        """ Test invalid messages: missing nodes """

        worker = FakeWorker()
        data = {
            "name": "a-new-loadbalancer"
        }
        job = FakeJob(data)
        r = lbaas_task(worker, job)
        self.assertIn("badRequest", r)
        self.assertIn("validationErrors", r["badRequest"])

    def testMissingPort(self):
        """ Test invalid messages: missing port """

        worker = FakeWorker()
        data = {
            "name": "a-new-loadbalancer",
            "nodes": [
                {
                    "address": "10.1.1.1"
                }
            ]
        }
        job = FakeJob(data)
        r = lbaas_task(worker, job)
        self.assertIn("badRequest", r)
        self.assertIn("validationErrors", r["badRequest"])

    def testMissingAddress(self):
        """ Test invalid messages: missing address """

        worker = FakeWorker()
        data = {
            "name": "a-new-loadbalancer",
            "nodes": [
                {
                    "port": "80"
                }
            ]
        }
        job = FakeJob(data)
        r = lbaas_task(worker, job)
        self.assertIn("badRequest", r)
        self.assertIn("validationErrors", r["badRequest"])
