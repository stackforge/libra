import json
import logging

from libra.worker.drivers.haproxy.services_base import ServicesBase


class FakeJob(object):
    def __init__(self, data):
        """
        data: JSON object to convert to a string
        """
        self.data = json.dumps(data)


class FakeOSServices(ServicesBase):
    def service_stop(self):
        pass

    def service_start(self):
        pass

    def write_config(self, config_str):
        pass

    def remove_configs(self):
        pass

    def sudo_rm(self, file):
        pass

    def syslog_restart(self):
        pass


class FakeFaultingOSServices(ServicesBase):
    def service_stop(self):
        raise Exception("fault")

    def service_start(self):
        raise Exception("fault")

    def service_restart(self):
        raise Exception("fault")

    def write_config(self):
        raise Exception("fault")

    def remove_configs(self):
        raise Exception("fault")


class MockLoggingHandler(logging.Handler):
    """Mock logging handler to check for expected logs."""

    def __init__(self, *args, **kwargs):
        self.reset()
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        self.messages[record.levelname.lower()].append(record.getMessage())

    def reset(self):
        self.messages = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'critical': [],
        }
