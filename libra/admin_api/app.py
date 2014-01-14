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
# under the License.

import eventlet
eventlet.monkey_patch()
import daemon
import daemon.pidfile
import daemon.runner
import grp
import logging as std_logging
import pwd
import pecan
import sys
import signal

from eventlet import wsgi

from libra import __version__
from libra.common.api import server
from libra.admin_api.stats.drivers.base import known_drivers
from libra.admin_api.stats.ping_sched import PingStats
from libra.admin_api.stats.offline_sched import OfflineStats
from libra.admin_api.stats.billing_sched import BillingStats
from libra.admin_api.stats.stats_sched import UsageStats
from libra.admin_api.device_pool.manage_pool import Pool
from libra.admin_api.expunge.expunge import ExpungeScheduler
from libra.admin_api import config as api_config
from libra.admin_api import model
from libra.admin_api import acl
from libra.openstack.common import importutils
from libra.openstack.common import log as logging
from libra.common.log import get_descriptors
from libra.common.options import CONF
from libra.common.options import add_common_opts
from libra.common.options import check_gearman_ssl_files


LOG = logging.getLogger(__name__)


def get_pecan_config():
    # Set up the pecan configuration
    filename = api_config.__file__.replace('.pyc', '.py')
    return pecan.configuration.conf_from_file(filename)


def setup_app(pecan_config):

    model.init_model()

    if not pecan_config:
        pecan_config = get_pecan_config()
    config = dict(pecan_config)
    config['database'] = CONF['admin_api']['db_sections']
    config['gearman'] = {
        'server': CONF['gearman']['servers'],
        'ssl_key': CONF['gearman']['ssl_key'],
        'ssl_cert': CONF['gearman']['ssl_cert'],
        'ssl_ca': CONF['gearman']['ssl_ca'],
        'keepalive': CONF['gearman']['keepalive'],
        'keepcnt': CONF['gearman']['keepcnt'],
        'keepidle': CONF['gearman']['keepidle'],
        'keepintvl': CONF['gearman']['keepintvl']
    }
    if CONF['debug']:
        config['wsme'] = {'debug': True}
        config['app']['debug'] = True

    pecan.configuration.set_config(config, overwrite=True)

    app = pecan.make_app(
        pecan_config.app.root,
        static_root=pecan_config.app.static_root,
        template_path=pecan_config.app.template_path,
        debug=getattr(pecan_config.app, 'debug', False),
        force_canonical=getattr(pecan_config.app, 'force_canonical', True),
        guess_content_type_from_ext=getattr(
            pecan_config.app,
            'guess_content_type_from_ext',
            True)
    )

    final_app = acl.AuthDirector(app)

    return final_app


class MaintThreads(object):
    def __init__(self, drivers):
        self.classes = []
        self.drivers = drivers
        signal.signal(signal.SIGINT, self.exit_handler)
        signal.signal(signal.SIGTERM, self.exit_handler)
        self.run_threads()

    def run_threads(self):

        pool = Pool()
        self.classes.append(pool)

        expunge = ExpungeScheduler()
        self.classes.append(expunge)

        pings = PingStats(self.drivers)
        self.classes.append(pings)

        offline = OfflineStats(self.drivers)
        self.classes.append(offline)

        if CONF['admin_api'].stats_enable:
            usage = UsageStats(self.drivers)
            self.classes.append(usage)

        if CONF['billing_enable']:
            billing = BillingStats(self.drivers)
            self.classes.append(billing)

    def exit_handler(self, signum, frame):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        for function in self.classes:
            function.shutdown()
        sys.exit()


class LogStdout(object):
    def write(self, data):
        if data.strip() != '':
            LOG.info(data)


def main():
    add_common_opts()
    CONF(project='libra', version=__version__)

    logging.setup('libra')

    LOG.debug('Configuration:')
    CONF.log_opt_values(LOG, std_logging.DEBUG)

    drivers = []

    pc = get_pecan_config()

    sock = server.make_socket(CONF['admin_api']['host'],
                              CONF['admin_api']['port'],
                              CONF['admin_api']['ssl_keyfile'],
                              CONF['admin_api']['ssl_certfile'])

    if CONF['daemon']:
        pidfile = daemon.pidfile.TimeoutPIDLockFile(CONF['admin_api']['pid'],
                                                    10)
        if daemon.runner.is_pidfile_stale(pidfile):
            pidfile.break_lock()

        descriptors = get_descriptors()
        descriptors.append(sock.fileno())
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

    try:
        check_gearman_ssl_files()
    except Exception as e:
        LOG.critical(str(e))
        return

    # Use the root logger due to lots of services using logger
    LOG.info('Starting on %s:%d', CONF.admin_api.host, CONF.admin_api.port)
    api = setup_app(pc)

    for driver in CONF['admin_api']['stats_driver']:
        drivers.append(importutils.import_class(known_drivers[driver]))

    MaintThreads(drivers)
    sys.stderr = LogStdout()

    wsgi.server(sock, api, keepalive=False)

    return 0
