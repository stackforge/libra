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


class Options(object):
    def __init__(self, shortname, title):
        self.title = title
        self._parse_args(shortname)

    def _parse_args(self, shortname):
        self.parser = argparse.ArgumentParser(
            description='Libra {title}'.format(title=self.title)
        )
        self.parser.add_argument(
            '-n', '--nodaemon', dest='nodaemon', action='store_true',
            help='do not run in daemon mode'
        )
        self.parser.add_argument(
            '-d', '--debug', dest='nodaemon', action='store_true',
            help='Log debugging output'
        )
        self.parser.add_argument(
            '-v', '--verbose', dest='verbose', action='store_true',
            help='Log more verbose output'
        )
        self.parser.add_argument(
            '-p', '--pid', dest='pid',
            default='/var/run/libra/libra_{name}.pid'.format(name=shortname),
            help='PID file to use (ignored with --nodaemon)'
        )
        self.parser.add_argument(
            '-l', '--logfile', dest='logfile',
            default='/var/log/libra/libra_{name}.log'.format(name=shortname),
            help='Log file to use (ignored with --nodaemon)'
        )

    def run(self):
        args = self.parser.parse_args()
        return vars(args)
