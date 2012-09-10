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
        self.assertNotEqual(r, "None")
