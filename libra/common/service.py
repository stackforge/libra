import eventlet
import logging
import socket
import signal
import sys

import gearman
from libra.common.options import CONF, cfg, libra_logging
from libra.openstack.common import gettextutils
from libra.openstack.common import jsonutils
from libra.openstack.common import log
from libra.openstack.common import service as os_service
from libra.common import gearman_

import threading


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


try:
    from concurrent import futures
except ImportError:
    import futures

from threading import Event


class Service(object):
    """
    Service that boots up n+ threads of the given object
    """
    def __init__(self, threads=1000):
        self.tp = futures.ThreadPoolExecutor(max_workers=threads)
        self._done = Event()

    def reset(self):
        self._done = Event()

    def start(self):
        pass

    def stop(self):

        self.tp.shutdown(wait=True)

    def wait(self):
        self._done.wait()


class Services(object):
    def __init__(self):
        self.services = []
        # NOTE: Bootup maximum of 10 service threads at once.
        self.tp = futures.ThreadPoolExecutor(max_workers=10)
        self.done = threading.Event()

    def add(self, service, threads=1):
        LOG.debug('Booting up %d threads of %s', threads, service)
        for i in xrange(threads):
            self.services.append(service)
            f = self.tp.submit(self.run_svc, service, self.done)

    def stop(self):
        LOG.debug('Stopping all services')
        self.tp.shutdown(wait=False)
        for s in self.services:
            s.stop()
            s.wait()

        if not self.done.ready():
            self.done.send()

    def restart(self):
        LOG.debug('Restarting services')
        self.stop()
        self.done = Event()
        for svc in self.services:
            svc.reset()
            self.tp.submit(self.run_svc, svc, self.done)

    def wait(self):
        self.done.wait()

    @staticmethod
    def run_svc(svc, done):
        svc.start()
        done.wait()


class ThreadLauncher(os_service.ServiceLauncher):
    """
    Launcher that holds multiple threads that are Service objects.
    """
    def __init__(self):
        self.services = Services()

    def _wait_for_exit_or_signal(self, ready_callback=None):
        status = None
        signo = 0

        LOG.debug(_('Full set of CONF:'))
        CONF.log_opt_values(LOG, logging.DEBUG)

        try:
            if ready_callback:
                ready_callback()
            self.services.wait()
        except os_service.SignalExit as exc:
            signame = _signo_to_signame(exc.signo)
            LOG.info(_('Caught %s, exiting'), signame)
            status = exc.code
            signo = exc.signo
        except SystemExit as exc:
            status = exc.code
        except Exception, e:
            LOG.error('Unknown error happened %s', e)
        finally:
            self.stop()
        return status, signo

    def launch_service(self, service, threads=1):
        self.services.add(service, threads=threads)

    def stop(self):
        LOG.warn('Stopping services')
        self.services.stop()


class WorkerService(Service):
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
        self.host = host or cfg.CONF.host
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
        #from libra.openstack.common.rpc.dispatcher import RpcDispatcher

        dispatcher = RpcDispatcher([self.manager])
        def _dispatch(*args, **kw):
            print args
        worker = gearman_.GearmanWorker(server_list)

        worker.set_client_id(self.host)
        worker.register_task(self.name, _dispatch)

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