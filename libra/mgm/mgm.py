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
import grp
import pwd
import threading

from libra import __version__
from libra.common.options import add_common_opts, CONF
from libra.common.log import get_descriptors
from libra.openstack.common import log
from libra.mgm.gearman_worker import worker_thread


LOG = log.getLogger(__name__)


class Server(object):
    def main(self):
        log.setup('libra')

        LOG.info(
            'Libra Pool Manager worker started, spawning {0} threads'
            .format(CONF['mgm']['threads'])
        )
        thread_list = []
        for x in xrange(0, CONF['mgm']['threads']):
            thd = threading.Thread(
                target=worker_thread, args=[]
            )
            thd.daemon = True
            thread_list.append(thd)
            thd.start()
        for thd in thread_list:
            thd.join()


def main():
    add_common_opts()
    CONF(project='libra', version=__version__)

    server = Server()

    if not CONF['daemon']:
        server.main()
    else:
        pidfile = daemon.pidfile.TimeoutPIDLockFile(CONF['mgm']['pid'], 10)
        if daemon.runner.is_pidfile_stale(pidfile):
            pidfile.break_lock()

        descriptors = get_descriptors()
        context = daemon.DaemonContext(
            working_directory='/',
            umask=0o022,
            pidfile=pidfile,
            files_preserve=descriptors
        )
        if CONF['user']:
            context.uid = pwd.getpwnam(CONF['user']).pw_uid
        if CONF['group']:
            context.gid = grp.getgrnam(CONF['group']).gr_gid

        context.open()
        server.main()

    return 0
