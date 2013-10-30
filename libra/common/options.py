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

import logging
import logging.handlers
import logstash
import sys

from oslo.config import cfg

from logging_handler import CompressedTimedRotatingFileHandler
from logging_handler import NewlineFormatter


CONF = cfg.CONF

common_opts = [
    cfg.BoolOpt('syslog',
                default=False,
                help='Use syslog for logging output'),
    cfg.StrOpt('syslog_socket',
               default='/dev/log',
               help='Socket to use for syslog connection'),
    cfg.StrOpt('syslog_facility',
               default='local7',
               help='Syslog logging facility'),
    cfg.StrOpt('logstash',
               metavar="HOST:PORT",
               help='Send logs to logstash at "host:port"'),
    cfg.StrOpt('group',
               help='Group to use for daemon mode'),
    cfg.StrOpt('user',
               help='User to use for daemon mode'),
]

common_cli_opts = [
    cfg.BoolOpt('daemon',
                default=True,
                help='Run as a daemon'),
]

gearman_opts = [
    cfg.BoolOpt('keepalive',
                default=False,
                help='Enable TCP KEEPALIVE pings'),
    cfg.IntOpt('keepcnt',
               metavar='COUNT',
               help='Max KEEPALIVE probes to send before killing connection'),
    cfg.IntOpt('keepidle',
               metavar='SECONDS',
               help='Seconds of idle time before sending KEEPALIVE probes'),
    cfg.IntOpt('keepintvl',
               metavar='SECONDS',
               help='Seconds between TCP KEEPALIVE probes'),
    cfg.IntOpt('poll',
               default=1,
               metavar='SECONDS',
               help='Gearman worker polling timeout'),
    cfg.IntOpt('reconnect_sleep',
               default=60,
               metavar='SECONDS',
               help='Seconds to sleep between job server reconnects'),
    cfg.ListOpt('servers',
                default=['localhost:4730'],
                metavar='HOST:PORT,...',
                help='List of Gearman job servers'),
    cfg.StrOpt('ssl_ca',
               metavar='FILE',
               help='Gearman SSL certificate authority'),
    cfg.StrOpt('ssl_cert',
               metavar='FILE',
               help='Gearman SSL certificate'),
    cfg.StrOpt('ssl_key',
               metavar='FILE',
               help='Gearman SSL key'),
]


def add_common_opts():
    CONF.register_opts(common_opts)
    CONF.register_opts(gearman_opts, group='gearman')
    CONF.register_cli_opts(common_cli_opts)


def libra_logging(name, section):
    """
    Shared routine for setting up logging. Depends on some common options
    (nodaemon, logfile, debug, verbose) being set.
    """

    debug = CONF['debug']
    verbose = CONF['verbose']
    logfile = CONF[section]['logfile']
    daemon = CONF['daemon']
    syslog = CONF['syslog']
    syslog_socket = CONF['syslog_socket']
    syslog_facility = CONF['syslog_facility']
    logstash_opt = CONF['logstash']

    if not daemon:
        logfile = None

    # Timestamped formatter
    # Use newline formatter to convert /n to ' ' so logstatsh doesn't break
    # multiline
    ts_formatter = NewlineFormatter(
        '%(asctime)-6s: %(name)s - %(levelname)s - %(message)s'
    )

    # No timestamp, used with syslog
    simple_formatter = logging.Formatter(
        '%(name)s - %(levelname)s - %(message)s'
    )

    if syslog and daemon:
        handler = logging.handlers.SysLogHandler(address=syslog_socket,
                                                 facility=syslog_facility)
        handler.setFormatter(simple_formatter)
    elif logstash_opt:
        logstash_host, logstash_port = logstash_opt.split(':')
        handler = logstash.LogstashHandler(logstash_host, int(logstash_port))
        handler.setFormatter(ts_formatter)
    elif logfile:
        handler = CompressedTimedRotatingFileHandler(
            logfile, when='D', interval=1, backupCount=7
        )
        handler.setFormatter(ts_formatter)
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(ts_formatter)

    logger = logging.getLogger(name)
    logger.addHandler(handler)

    if debug:
        logger.setLevel(level=logging.DEBUG)
    elif verbose:
        logger.setLevel(level=logging.INFO)

    return logger
