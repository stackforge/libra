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

import daemon
import daemon.pidfile
import daemon.runner
import grp
import pwd

from libra.common.options import Options, setup_logging


class APIServer(object):
    def __init__(self, logger, args):
        self.logger = logger
        self.args = args


def main():
    options = Options('api', 'API Daemon')
    args = options.run()

    logger = setup_logging('api_server', args)
    server = APIServer(logger, args)

    if args.nodaemon:
        server.main(task_list)
    else:
        pidfile = daemon.pidfile.TimeoutPIDLockFile(args.pid, 10)
        if daemon.runner.is_pidfile_stale(pidfile):
            logger.warning("Cleaning up stale PID file")
            pidfile.break_lock()
        context = daemon.DaemonContext(
            working_directory='/etc/libra',
            umask=0o022,
            pidfile=pidfile,
            files_preserve=[logger.handlers[0].stream]
        )
        if args.user:
            try:
                context.uid = pwd.getpwnam(args.user).pw_uid
            except KeyError:
                logger.critical("Invalid user: %s" % args.user)
                return 1
            # NOTE(LinuxJedi): we are switching user so need to switch
            # the ownership of the log file for rotation
            os.chown(logger.handlers[0].baseFilename, context.uid, -1)
        if args.group:
            try:
                context.gid = grp.getgrnam(args.group).gr_gid
            except KeyError:
                logger.critical("Invalid group: %s" % args.group)
                return 1

        try:
            context.open()
        except lockfile.LockTimeout:
            logger.critical(
                "Failed to lock pidfile %s, another instance running?",
                args.pid
            )
            return 1

        server.main()
    return 0
