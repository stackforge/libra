# Copyright 2014 Hewlett-Packard Development Company, L.P.
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
import wsme_overrides

from eventlet import wsgi

from libra import __version__
from libra.api import config as api_config
from libra.api import model
from libra.api import acl
from libra.common.api import server
from libra.common.log import get_descriptors
from libra.common.options import CONF
from libra.common.options import add_common_opts
from libra.common.options import check_gearman_ssl_files
from libra.openstack.common import log as logging


LOG = logging.getLogger(__name__)


# Gets rid of pep8 error
assert wsme_overrides


def get_pecan_config():
    # Set up the pecan configuration
    filename = api_config.__file__.replace('.pyc', '.py')
    return pecan.configuration.conf_from_file(filename)


def setup_app(pecan_config):

    model.init_model()

    if not pecan_config:
        pecan_config = get_pecan_config()
    config = dict(pecan_config)
    config['database'] = CONF['api']['db_sections']
    config['swift'] = {
        'swift_basepath': CONF['api']['swift_basepath'],
        'swift_endpoint': CONF['api']['swift_endpoint']
    }
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
    config['ip_filters'] = CONF['api']['ip_filters']
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


class LogStdout(object):
    def write(self, data):
        if data.strip() != '':
            LOG.info(data)

    # Gearman calls this
    def flush(self):
        pass


def main():
    add_common_opts()
    CONF(project='libra', version=__version__)

    logging.setup('libra')

    LOG.debug('Configuration:')
    CONF.log_opt_values(LOG, std_logging.DEBUG)

    pc = get_pecan_config()

    # NOTE: Let's not force anyone to actually have to use SSL, it shouldn't be
    # up to us to decide.
    sock = server.make_socket(CONF['api']['host'],
                              CONF['api']['port'],
                              CONF['api']['ssl_keyfile'],
                              CONF['api']['ssl_certfile'])

    if CONF['daemon']:
        pidfile = daemon.pidfile.TimeoutPIDLockFile(CONF['api']['pid'], 10)
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

    LOG.info('Starting on %s:%d', CONF.api.host, CONF.api.port)
    api = setup_app(pc)
    sys.stderr = LogStdout()

    wsgi.server(sock, api, keepalive=False, debug=CONF['debug'])

    return 0
