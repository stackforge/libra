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

import argparse
import logging
import logging.handlers
import logstash
import os
import os.path
import sys
import ConfigParser

from libra import __version__, __release__
from logging_handler import CompressedTimedRotatingFileHandler
from logging_handler import NewlineFormatter

"""
Common options parser.

Options can come from either the command line or a configuration file
in INI format. Command line options will override options from the config
file.

The following sections of the config file will be parsed:
    [global]
    [shortname]

The [global] section can be used for options common to any program using
this class. It is optional and does not need to be present in the file.

The [shortname] section can be used for program-specific options.
The value of 'shortname' comes from the Options.__init__() method.

For example, this Options object:

    options = Options('worker', 'Worker Daemon')

Will read the [global] and [worker] config file sections. All other
sections will be ignored.

Boolean values in the configuration file must be given a true/false
value.
"""


class Options(object):
    def __init__(self, shortname, title):
        self.title = title
        self.shortname = shortname
        self._arg_defaults = dict()
        self._parse_args()

    def _get_defaults_from_config(self, parser):
        """
        Use the config file to get the defaults. This should be called
        immediately after the option for the config file is defined, but
        before all other options are defined.
        """
        args, remaining_args = parser.parse_known_args()

        if args.config and os.path.exists(args.config):
            config = ConfigParser.SafeConfigParser()
            config.read([args.config])

            # global section not required, so don't error
            try:
                global_items = config.items('global')
            except ConfigParser.NoSectionError:
                global_items = []

            # program-specific section not required, so don't error
            try:
                section_items = config.items(self.shortname)
            except ConfigParser.NoSectionError:
                section_items = []

            self._arg_defaults.update(dict(global_items + section_items))

            # Convert booleans to correct type
            for k, v in self._arg_defaults.items():
                if v.upper() == 'FALSE':
                    self._arg_defaults[k] = False
                elif v.upper() == 'TRUE':
                    self._arg_defaults[k] = True

    def _parse_args(self):
        # We use a temporary parser to get the config file and read those
        # options in as defaults, then continue parsing the rest.
        tmp_parser = argparse.ArgumentParser(add_help=False)
        tmp_parser.add_argument(
            '-c', '--config', dest='config', default='/etc/libra/libra.ini'
        )
        self._get_defaults_from_config(tmp_parser)

        self.parser = argparse.ArgumentParser(
            description='Libra {title}'.format(title=self.title)
        )

        # Config repeated here just so it will show up in the automatically
        # generated help from ArgumentParser.
        self.parser.add_argument(
            '-c', '--config', dest='config', default='/etc/libra/libra.ini',
            metavar='FILE', help='configuration file'
        )

        self.parser.add_argument(
            '--version', dest='version', action='store_true',
            help='print version and exit'
        )
        self.parser.add_argument(
            '--release', dest='release', action='store_true',
            help='print full release version info and exit'
        )
        self.parser.add_argument(
            '-n', '--nodaemon', dest='nodaemon', action='store_true',
            help='do not run in daemon mode'
        )
        self.parser.add_argument(
            '--syslog', dest='syslog', action='store_true',
            help='use syslog for logging output'
        )
        self.parser.add_argument(
            '--syslog-socket', dest='syslog_socket',
            default='/dev/log',
            help='socket to use for syslog connection (default: /dev/log)'
        )
        self.parser.add_argument(
            '--syslog-facility', dest='syslog_facility',
            default='local7',
            help='syslog logging facility (default: local7)'
        )
        self.parser.add_argument(
            '-d', '--debug', dest='debug', action='store_true',
            help='log debugging output'
        )
        self.parser.add_argument(
            '-v', '--verbose', dest='verbose', action='store_true',
            help='log more verbose output'
        )
        self.parser.add_argument(
            '-p', '--pid', dest='pid',
            default='/var/run/libra/libra_{name}.pid'.format(
                name=self.shortname
            ),
            help='PID file to use (ignored with --nodaemon)'
        )
        self.parser.add_argument(
            '-l', '--logfile', dest='logfile',
            default='/var/log/libra/libra_{name}.log'.format(
                name=self.shortname
            ),
            help='log file to use (ignored with --nodaemon)'
        )
        self.parser.add_argument(
            '--logstash', dest='logstash', metavar="HOST:PORT",
            help='send logs to logstash at "host:port"'
        )
        self.parser.add_argument(
            '--user', dest='user',
            help='user to use for daemon mode'
        )
        self.parser.add_argument(
            '--group', dest='group',
            help='group to use for daemon mode'
        )

    def run(self):
        # We have to set defaults from the config AFTER all add_argument()
        # calls because otherwise, the default= value used in those calls
        # would take precedence.
        if self._arg_defaults:
            self.parser.set_defaults(**self._arg_defaults)
        args = self.parser.parse_args()
        if args.version:
            print("Libra toolset version %s" % __version__)
            sys.exit(0)
        if args.release:
            print("Libra toolset release %s" % __release__)
            sys.exit(0)
        return args


def setup_logging(name, args):
    """
    Shared routine for setting up logging. Depends on some common options
    (nodaemon, logfile, debug, verbose) being set.
    """

    logfile = args.logfile
    if args.nodaemon:
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

    if args.syslog and not args.nodaemon:
        handler = logging.handlers.SysLogHandler(address=args.syslog_socket,
                                                 facility=args.syslog_facility)
        handler.setFormatter(simple_formatter)
    elif args.logstash:
        logstash_host, logstash_port = args.logstash.split(':')
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

    if args.debug:
        logger.setLevel(level=logging.DEBUG)
    elif args.verbose:
        logger.setLevel(level=logging.INFO)

    return logger
