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

import threading
import signal
import sys
from datetime import datetime, timedelta
from pecan import conf
from libra.api.model.lbaas import LoadBalancer, db_session


class ExpungeScheduler(object):
    def __init__(self, logger):
        if not conf.expire_days:
            logger.info('Expunge not configured, disabled')
            return
        self.logger = logger
        self.expunge_timer = None
        signal.signal(signal.SIGINT, self.exit_handler)
        signal.signal(signal.SIGTERM, self.exit_handler)
        self.run_expunge()

    def exit_handler(self, signum, frame):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if self.expunge_timer:
            self.expunge_timer.cancel()
        self.logger.info('Safely shutting down')
        sys.exit(0)

    def run_expunge(self):
        with db_session() as session:
            try:
                exp = datetime.now() - timedelta(
                    days=int(conf.expire_days)
                )
                exp_time = exp.strftime('%Y-%m-%d %H:%M:%S')
                self.logger.info(
                    'Expunging deleted loadbalancers older than {0}'
                    .format(exp_time)
                )
                count = session.query(
                    LoadBalancer.status
                ).filter(LoadBalancer.updated < exp_time).\
                    filter(LoadBalancer.status == 'DELETED').delete()
                session.commit()
                self.logger.info(
                    '{0} deleted load balancers expunged'.format(count)
                )
            except:
                self.logger.exception('Exception occured during expunge')
        self.logger.info('Expunge thread sleeping for 24 hours')
        self.expunge_timer = threading.Timer(24*60*60, self.run_expunge, ())
