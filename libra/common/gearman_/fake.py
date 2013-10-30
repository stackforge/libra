from oslo.config import cfg

import Queue
import threading
import time

from libra.common.gearman_.encoders import get_encoder


cfg.CONF.import_opt('encoder', 'libra.common.gearman_', group='gearman')


class DummyServer(object):
    def __init__(self):
        self.workers = set()
        self.tasks = {}

    def add_worker(self, worker):
        self.workers.add(worker)
        return self

    def _get_or_create_task_key(self, task):
        """
        Get's or creates a set.
        """
        if task not in self.tasks:
            self.tasks[task] = set()
        return self.tasks[task]

    def register_task(self, task, worker):
        tasks = self._get_or_create_task_key(task)
        tasks.add(worker)

    def unregister_task(self, task, worker):
        """
        Remove a worker from a task
        """
        tasks = selt.tasks.get(task, None)
        if worker in tasks:
            tasks.remove(worker)


SERVER = DummyServer()


class FakeWorker(object):
    def __init__(self, host_list=None):
        self.encoder = get_encoder(cfg.CONF.gearman.encoder)

        # Setup some variables
        self.client_id = None

        self.server = SERVER.add_worker(self)

    def set_client_id(self, id_):
        self.client_id = id_

    def register_task(self, task, callback_function):
        self.server.register_task(task, self)

    def unregister_task(self, task):
        self.server.unregister_task(task, self)

    def work(self, poll=None):
        print "DO WORK"