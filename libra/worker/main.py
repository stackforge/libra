# Copyright 2012 Hewlett-Packard Development Company, L.P.
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
# under the License.

import daemon
import daemon.pidfile
import daemon.runner
import getpass
import grp
import pwd
import time
import threading

from libra import __version__
from libra.openstack.common import importutils
from libra.openstack.common import log
from libra.common.options import add_common_opts, CONF
from libra.common.log import get_descriptors
from libra.worker.drivers.base import known_drivers
from libra.worker.drivers.haproxy.services_base import haproxy_services
from libra.worker.worker import config_thread


LOG = log.getLogger(__name__)


class EventServer(object):
    """
    Encapsulates server activity so we can run it in either daemon or
    non-daemon mode.
    """

    def main(self, tasks):
        """
        Main method of the server.

        tasks
            A tuple with two items: a function name, and a tuple with
            that function's arguments.
        """
        thread_list = []

        driver = CONF['worker']['driver']
        LOG.info("Selected driver: %s" % driver)
        if driver == 'haproxy':
            LOG.info("Selected HAProxy service: %s" %
                     CONF['worker:haproxy']['service'])
        LOG.info("Job server list: %s" % CONF['gearman']['servers'])

        for task, task_args in tasks:
            task_args = () + task_args  # Make the LOG the first arg
            thd = threading.Thread(target=task, args=task_args)
            thd.daemon = True
            thread_list.append(thd)
            thd.start()

        while True:
            try:
                time.sleep(600)
            except KeyboardInterrupt:
                LOG.info("Non-daemon session terminated")
                break

        LOG.info("Shutting down")


def main():
    """ Main Python entry point for the worker utility. """

    add_common_opts()
    CONF(project='libra', version=__version__)

    log.setup('libra')

    # Import the device driver we are going to use. This will be sent
    # along to the Gearman task that will use it to communicate with
    # the device.

    selected_driver = CONF['worker']['driver']
    driver_class = importutils.import_class(known_drivers[selected_driver])

    if selected_driver == 'haproxy':
        if CONF['user']:
            user = CONF['user']
        else:
            user = getpass.getuser()

        if CONF['group']:
            group = CONF['group']
        else:
            group = None

        haproxy_service = CONF['worker:haproxy']['service']
        haproxy_logfile = CONF['worker:haproxy']['logfile']
        driver = driver_class(haproxy_services[haproxy_service],
                              user, group,
                              haproxy_logfile=haproxy_logfile)
    else:
        driver = driver_class()

    server = EventServer()

    # Tasks to execute in parallel
    task_list = [
        (config_thread, (driver,))
    ]

    if not CONF['daemon']:
        server.main(task_list)
    else:

        pidfile = daemon.pidfile.TimeoutPIDLockFile(CONF['worker']['pid'], 10)
        if daemon.runner.is_pidfile_stale(pidfile):
            pidfile.break_lock()
        descriptors = get_descriptors()
        context = daemon.DaemonContext(
            working_directory='/etc/haproxy',
            umask=0o022,
            pidfile=pidfile,
            files_preserve=descriptors
        )
        if CONF['user']:
            context.uid = pwd.getpwnam(CONF['user']).pw_uid
        if CONF['group']:
            context.gid = grp.getgrnam(CONF['group']).gr_gid

        context.open()
        server.main(task_list)

    return 0
