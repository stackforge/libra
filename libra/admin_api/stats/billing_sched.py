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
import datetime

from oslo.config import cfg
from libra.common.api.lbaas import Billing, db_session
from libra.common.api.mnb import update_mnb, test_mnb_connection
from libra.openstack.common import timeutils
from libra.openstack.common import log as logging
from sqlalchemy.sql import func


LOG = logging.getLogger(__name__)


class BillingStats(object):

    EXISTS_SECONDS = cfg.CONF['admin_api'].exists_timer_seconds
    USAGE_SECONDS = cfg.CONF['admin_api'].usage_timer_seconds

    def __init__(self, drivers):
        self.drivers = drivers
        self.usage_timer = None
        self.exists_timer = None
        self.server_id = cfg.CONF['admin_api']['server_id']
        self.number_of_servers = cfg.CONF['admin_api']['number_of_servers']
        self.exists_freq = cfg.CONF['admin_api'].exists_freq
        self.usage_freq = cfg.CONF['admin_api'].usage_freq
        self.start_usage_sched()
        self.start_exists_sched()

    def shutdown(self):
        if self.usage_timer:
            self.usage_timer.cancel()
        if self.exists_timer:
            self.exists_timer.cancel()

    def update_usage(self):
        # Work out if it is our turn to run
        minute = datetime.datetime.now().minute
        if self.server_id != minute % self.number_of_servers:
            self.start_usage_sched()
            return

        # Send periodic usage notifications
        try:
            self._exec_usage()
        except Exception:
            LOG.exception('Uncaught exception during billing usage update')

        # Need to restart timer after every billing cycle
        self.start_usage_sched()

    def update_exists(self):
        # Work out if it is our turn to run
        minute = datetime.datetime.now().minute
        if self.server_id != minute % self.number_of_servers:
            self.start_exists_sched()
            return

        # Send periodic exists notifications
        try:
            self._exec_exists()
        except Exception:
            LOG.exception('Uncaught exception during billing exists update')

        # Need to restart timer after every billing cycle
        self.start_exists_sched()

    def _exec_exists(self):
        with db_session() as session:
            # Check if it's time to send exists notifications
            delta = datetime.timedelta(minutes=self.exists_freq)
            exp = timeutils.utcnow() - delta
            exp_time = exp.strftime('%Y-%m-%d %H:%M:%S')

            updated = session.query(
                Billing.last_update
            ).filter(Billing.name == "exists").\
                filter(Billing.last_update > exp_time).\
                first()

            if updated is not None:
                # Not time yet
                LOG.info('Not time to send exists notifications yet {0}'.
                         format(exp_time))
                session.rollback()
                return

            # Check the connection before sending the notifications
            if not test_mnb_connection():
                # Abort the exists notifications
                LOG.info("Aborting exists notifications. Could not connect")
                session.rollback()
                return

            # Update the exists timestamp now
            session.query(Billing).\
                filter(Billing.name == "exists").\
                update({"last_update": func.now()},
                       synchronize_session='fetch')
            session.commit()

        # Send the notifications
        update_mnb('lbaas.instance.exists', None, None)

    def _exec_usage(self):
        with db_session() as session:
            # Next check if it's time to send bandwidth usage notifications
            delta = datetime.timedelta(minutes=self.usage_freq)
            exp = timeutils.utcnow() - delta

            start, = session.query(
                Billing.last_update
            ).filter(Billing.name == "usage").\
                first()

            if start and start > exp:
                # Not time yet
                LOG.info('Not time to send usage statistics yet {0}'.
                         format(exp))
                session.rollback()
                return

            # Check the connection before sending the notifications
            if not test_mnb_connection():
                # Abort the exists notifications
                LOG.info("Aborting usage notifications. Could not connect")
                session.rollback()
                return

            # Calculate the stopping point by rounding backward to the nearest
            # N minutes. i.e. if N = 60, this will round us back to HH:00:00,
            # or if N = 15, it will round us back to HH:15:00, HH:30:00,
            # HH:45:00, or HH:00:00, whichever is closest.
            N = cfg.CONF['admin_api'].usage_freq
            now = timeutils.utcnow()
            stop = now - datetime.timedelta(minutes=now.minute % N,
                                            seconds=now.second,
                                            microseconds=now.microsecond)

            # Release the lock
            session.query(Billing).\
                filter(Billing.name == "usage").\
                update({"last_update": stop},
                       synchronize_session='fetch')
            session.commit()

        # Send the usage notifications. Pass the timestamps to save
        # queries.
        update_mnb('lbaas.bandwidth.usage', start, stop)

    def start_usage_sched(self):
        # Always try to hit the expected second mark for usage
        seconds = datetime.datetime.now().second
        if seconds < self.USAGE_SECONDS:
            sleeptime = self.USAGE_SECONDS - seconds
        else:
            sleeptime = 60 - (seconds - self.USAGE_SECONDS)

        LOG.info('LB usage timer sleeping for {secs} seconds'
                 .format(secs=sleeptime))
        self.usage_timer =\
            threading.Timer(sleeptime, self.update_usage, ())
        self.usage_timer.start()

    def start_exists_sched(self):
        # Always try to hit the expected second mark for exists
        seconds = datetime.datetime.now().second
        if seconds < self.EXISTS_SECONDS:
            sleeptime = self.EXISTS_SECONDS - seconds
        else:
            sleeptime = 60 - (seconds - self.EXISTS_SECONDS)

        LOG.info('LB exists timer sleeping for {secs} seconds'
                 .format(secs=sleeptime))
        self.exists_timer =\
            threading.Timer(sleeptime, self.update_exists, ())
        self.exists_timer.start()
