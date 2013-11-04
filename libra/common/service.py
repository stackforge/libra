# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations

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
    Service that has a threadpool based on concurrent.futures which uses
    threading compared to OSLO tpool which uses GreenThreads.
    """
    def __init__(self, threads=1000):
        self.tp = futures.ThreadPoolExecutor(max_workers=threads)
        self.done = threading.Event()

    def start(self):
        pass

    def stop(self):
        self.tp.shutdown(wait=True)
        if not self.done.is_set():
            self.done.set()

    def wait(self):
        self.done.wait()


class Services(object):
    def __init__(self):
        self.services = []
        self.futures = []

        self.tp = futures.ThreadPoolExecutor(max_workers=20)
        self.done = threading.Event()

    def add(self, service_cls, instances=2, *args, **kw):
        LOG.debug('Starting %d instances of %s', instances, service_cls)
        for i in xrange(instances):
            svc = service_cls(*args, **kw)
            self.services.append(svc)

            f = self.tp.submit(self.run_service, svc, self.done)
            self.futures.append(f)

    def stop(self):
        LOG.debug('Stopping all services')
        for s in self.services:
            s.stop()
            s.wait()

        if not self.done.is_set():
            self.done.set()

        self.tp.shutdown(wait=False)

    def restart(self):
        LOG.debug('Restarting services')
        self.stop()
        self.done = threading.Event()
        for svc in self.services:
            svc.reset()
            self.tp.submit(self.run_svc, svc)

    def wait(self):
        LOG.debug('Services waiting')
        futures.wait(self.futures)

    @staticmethod
    def run_service(service, done):
        service.start()
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
        return status, signo

    def launch_service(self, service, instances=1):
        self.services.add(service, instances=instances)

    def stop(self):
        LOG.warn('Stopping services')
        self.services.stop()
