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

from datetime import datetime
from oslo.config import cfg
from libra.common.api.lbaas import Billing, db_session
from libra.common.api.mnb import update_mnb
from libra.openstack.common import timeutils
from sqlalchemy.sql import func


class BillingStats(object):

    BILLING_SECONDS = 30

    def __init__(self, logger, drivers):
        self.logger = logger
        self.drivers = drivers
        self.billing_timer = None
        self.server_id = cfg.CONF['admin_api']['server_id']
        self.number_of_servers = cfg.CONF['admin_api']['number_of_servers']
        self.exists_freq = cfg.CONF['admin_api'].exists_freq
        self.usage_freq = cfg.CONF['admin_api'].usage_freq

        self.start_billing_sched()

    def shutdown(self):
        if self.billing_timer:
            self.billing_timer.cancel()

    def update_billing(self):
        # Work out if it is our turn to run
        minute = datetime.now().minute
        if self.server_id != minute % self.number_of_servers:
            self.start_billing_sched()
            return
        try:
            exists, usage = self._exec_billing()
        except Exception:
            self.logger.exception('Uncaught exception during billing update')

        if exists > 0:
            self.logger.info('{exists} loadbalancer exists notifications sent'
                             .format(exists=exists))

        if usage > 0:
            self.logger.info('{usage} loadbalancer BW usage notifications sent'
                             .format(usage=usage))

            # Need to restart timer after every billing cycle
        self.start_billing_sched()

    def _exec_billing(self):
        with db_session() as session:
            # Check if it's time to send exists notifications
            exists_count = 0
            delta = datetime.timedelta(mins=self.exists_freq)
            exp = timeutils.utcnow() - delta
            exp_time = exp.strftime('%Y-%m-%d %H:%M:%S')

            updated = session.query(
                Billing.exists_updated
            ).\
                filter(Billing.exists_updated > exp_time).\
                with_lockmode('update').\
                first()

            if updated is None:
                #Send exists notifications after updating the timestamp
                session.query(Billing).update({"exists_updated": func.now()},
                                              synchronize_session='fetch')
                session.commit()
                self.logger.info('Sending MnB exists notifications')
                exists_count = update_mnb('lbaas.instance.exists', None, None)
            else:
                session.rollback()

        with db_session() as session:
            # Next check if it's time to send bandwidth usage notifications
            usage_count = 0
            delta = datetime.timedelta(mins=self.usage_freq)
            exp = timeutils.utcnow() - delta
            exp_time = exp.strftime('%Y-%m-%d %H:%M:%S')

            updated = session.query(
                Billing.usage_updated
            ).\
                filter(Billing.usage_updated > exp_time).\
                with_lockmode('update').\
                first()

            if updated is None:
                #Send usage stats after updating the timestamp
                session.query(Billing).update({"usage_updated": func.now()},
                                              synchronize_session='fetch')
                session.commit()
                self.logger.info('Sending MnB usage notifications')
                usage_count = update_mnb('lbaas.bandwidth.usage', None, None)
            else:
                session.rollback()

        return exists_count, usage_count

    def start_billing_sched(self):
        # Always try to hit the expected second mark for billing
        seconds = datetime.now().second
        if seconds < self.BILLING_SECONDS:
            sleeptime = self.BILLING_SECONDS - seconds
        else:
            sleeptime = 60 - (seconds - self.BILLING_SECONDS)

        self.logger.info('LB billing timer sleeping for {secs} seconds'
                         .format(secs=sleeptime))
        self.billing_timer =\
            threading.Timer(sleeptime, self.update_billing, ())
        self.billing_timer.start()
