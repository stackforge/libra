from oslo.config import cfg
import gearman
import time

from libra.openstack.common import log
from libra.common import service
from libra.common.options import CONF
from libra.common.gearman_ import GearmanWorker, get_server_list
from libra.common.gearman_.dispatcher import Dispatcher
from libra.common.gearman_ import get_cls


LOG = log.getLogger(__name__)


class WorkerService(service.Service):
    def __init__(self, host=None, name=None, manager=None, serializer=None):
        """
        :param host: Use this as the hostname.
                     Defaults to the socket.gethostname() itself.
        :param name: The nane to register this worker with.
                     Defaults to the hostname if not set.
        :param manager: An alternative manager class.
        :param serializer: The serializer to be used with gearman.
        """
        super(WorkerService, self).__init__()
        self.host = host or CONF.host
        self.name = name or host

        self.serializer = serializer
        self.manager = self if manager is None else manager
        self.retry = True

    def start(self):
        super(WorkerService, self).start()

        LOG.debug('Starting worker connection %s @ %s', self.name, self.host)

        server_list = get_server_list()

        LOG.debug('Server list: %s' % server_list)

        # NOTE: Setup the worker.
        cls = get_cls(cfg.CONF.gearman.driver)
        worker = cls(server_list)
        worker.set_client_id(self.host)

        dispatcher = Dispatcher(self.manager)
        worker.register_task(self.name, dispatcher.dispatch)

        worker.logger = LOG

        while (self.retry):
            try:
                worker.work(CONF.gearman.poll)
            except KeyboardInterrupt:
                self.stop()
            except gearman.errors.ServerUnavailable:
                LOG.error("Job server(s) went away. Reconnecting.")
                time.sleep(CONF['gearman']['reconnect_sleep'])
                self.retry = True
            except Exception:
                LOG.exception("Exception in worker")
                self.stop()

    def stop(self):
        self.retry = False
        LOG.debug('Stopping %s @ %s', self.name, self.host)
        super(WorkerService, self).stop()
