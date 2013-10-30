import eventlet
import socket
import sys

import gearman
from libra.common.options import CONF, cfg, libra_logging
from libra.openstack.common import gettextutils
from libra.openstack.common import jsonutils
from libra.openstack.common import log
from libra.openstack.common import service
from libra.common import gearman_



CONF.register_opts([
    cfg.StrOpt('host',
               default=socket.gethostname(),
               help='Name of this node.  This can be an opaque identifier.  '
               'It is not necessarily a hostname, FQDN, or IP address. '
               'However, the node name must be valid within '
               'an AMQP key, and if using ZeroMQ, a valid '
               'hostname, FQDN, or IP address'),
])


LOG = log.getLogger(__name__)


def prepare_service(argv=None):
    eventlet.monkey_patch()
    gettextutils.install('libra', lazy=False)

    if argv is None:
        argv = sys.argv
    CONF(argv[1:], project='libra')
    log.setup('libra')


from libra.openstack.common.rpc.dispatcher import RpcDispatcher


# TODO: Use oslo's rpc dispatcher mechanism instead ?
class Dispatcher(RpcDispatcher):

    def run(self, worker, job):
        LOG.debug('Received data: %s', job.data)
        action = job.data['action'].lower()
        try:
            response = getattr(self.manager, action)
        except AttributeError:
            LOG.error('Unable to find action %s', action)
            return
        LOG.debug('Response %s', response)


class WorkerService(service.Service):
    def __init__(self, host, name=None, manager=None, serializer=None):
        super(WorkerService, self).__init__()
        self.host = host
        self.name = name or host

        self.serializer = serializer
        self.manager = self if manager is None else manager
        self.retry = True

    def start(self):
        super(WorkerService, self).start()

        LOG.debug('Starting worker connection %s @ %s', self.name, self.host)

        server_list = gearman_.get_server_list()

        LOG.debug('Server list: %s' % server_list)

        # NOTE: Setup the worker.
        from libra.openstack.common.rpc.dispatcher import RpcDispatcher
        dispatcher = RpcDispatcher([self.manager])

        worker = gearman_.GearmanWorker(server_list)
        worker.set_client_id(self.host)
        worker.register_task(self.name, dispatcher.run)

        logger = libra_logging('libra_mgm', 'mgm')

        worker.logger = logger

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