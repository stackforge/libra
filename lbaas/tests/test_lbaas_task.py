import json
import unittest
from lbaas.worker import lbaas_task

class FakeJob(object):
    def __init__(self, data):
        """
        data: JSON object to convert to a string
        """
        self.data = json.dumps(data)

class TestLBaaSTask(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testLBaaSTask(self):
        """ Test the lbaas_task() function """

        worker = None
        data = { "name": "a-new-loadbalancer",
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
        self.assertIn("status", r["nodes"][0])
        self.assertEqual(r["nodes"][1]["address"], data["nodes"][1]["address"])
        self.assertEqual(r["nodes"][1]["port"], data["nodes"][1]["port"])
        self.assertIn("status", r["nodes"][1])
