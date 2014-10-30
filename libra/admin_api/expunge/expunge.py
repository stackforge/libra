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

from datetime import datetime, timedelta
from oslo.config import cfg

from libra.common.api.lbaas import LoadBalancer, db_session, Counters
from libra.openstack.common import log


LOG = log.getLogger(__name__)


class ExpungeScheduler(object):
    def __init__(self):
        self.expunge_timer = None
        self.expire_days = cfg.CONF['admin_api']['expire_days']
        if not self.expire_days:
            LOG.info('Expunge not configured, disabled')
            return
        self.server_id = cfg.CONF['admin_api']['server_id']
        self.number_of_servers = cfg.CONF['admin_api']['number_of_servers']
        self.run_expunge()

    def shutdown(self):
        if self.expunge_timer:
            self.expunge_timer.cancel()

    def run_expunge(self):
        day = datetime.now().day
        if self.server_id != day % self.number_of_servers:
            LOG.info('Not our turn to run expunge check, sleeping')
            self.expunge_timer = threading.Timer(
                24 * 60 * 60, self.run_expunge, ()
            )
        with db_session() as session:
            try:
                exp = datetime.now() - timedelta(
                    days=int(self.expire_days)
                )
                exp_time = exp.strftime('%Y-%m-%d %H:%M:%S')
                LOG.info(
                    'Expunging deleted loadbalancers older than {0}'
                    .format(exp_time)
                )
                count = session.query(
                    LoadBalancer.status
                ).filter(LoadBalancer.updated < exp_time).\
                    filter(LoadBalancer.status == 'DELETED').delete()
                counter = session.query(Counters).\
                    filter(Counters.name == 'loadbalancers_expunged').first()
                counter.value += count
                session.commit()
                LOG.info(
                    '{0} deleted load balancers expunged'.format(count)
                )
                # TODO delete rate_limited_actions rows older than
                # rate_limit_expunge_age seconds
            except:
                LOG.exception('Exception occurred during expunge')
        LOG.info('Expunge thread sleeping for 24 hours')
        self.expunge_timer = threading.Timer(
            24 * 60 * 60, self.run_expunge, ())
