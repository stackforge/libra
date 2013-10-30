import eventlet
import logging
import socket
import sys
import threading

try:
    from concurrent import futures
except ImportError:
    import futures

from oslo.config import cfg
from libra.openstack.common import gettextutils
from libra.openstack.common import log
from libra.openstack.common import service as os_service

from libra.openstack.common.gettextutils import _


cfg.CONF.register_opts([
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
    cfg.CONF(argv[1:], project='libra')
    log.setup('libra')


class Service(object):
    """
    Service that boots up n+ threads of the given object
    """
    def __init__(self, threads=1000):
        self.tp = futures.ThreadPoolExecutor(max_workers=threads)
        self._done = threading.Event()

    def reset(self):
        self._done = threading.Event()

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
        self.done = threading.Event()
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
        cfg.CONF.log_opt_values(LOG, logging.DEBUG)

        try:
            if ready_callback:
                ready_callback()
            self.services.wait()
        except os_service.SignalExit as exc:
            signame = os_service._signo_to_signame(exc.signo)
            LOG.info(_('Caught %s, exiting'), signame)
            status = exc.code
            signo = exc.signo
        except SystemExit as exc:
            status = exc.code
        except Exception, e:
            LOG.error('Unknown error happened %s', e)
        finally:
            self.stop()
        print "DOH"

        return status, signo

    def launch_service(self, service, threads=1):
        self.services.add(service, threads=threads)

    def stop(self):
        LOG.warn('Stopping services')
        self.services.stop()
