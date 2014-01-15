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

import datetime
import eventlet
eventlet.monkey_patch()

from oslo.config import cfg
from libra.common.api.lbaas import LoadBalancer, db_session
from libra.common.api.lbaas import Stats
from libra.openstack.common.notifier import api as notifier_api
from libra.openstack.common import timeutils
from libra.openstack.common import log as logging
from libra.openstack.common import rpc
from libra.openstack.common.rpc import common as rpc_common
from sqlalchemy.sql import func


LOG = logging.getLogger(__name__)


def update_mnb(event_type, lbid, tenant_id):
    eventlet.spawn_n(client_job, event_type, lbid, tenant_id)


def client_job(event_type, lbid, tenant_id):

    try:
        if(event_type == 'lbaas.instance.create' or
           event_type == 'lbaas.instance.delete'):
            _send_create_or_delete(event_type, lbid, tenant_id)
        elif event_type == 'lbaas.instance.exists':
            _send_exists(event_type)
        elif event_type == 'lbaas.bandwidth.usage':
            _send_usage(event_type, lbid, tenant_id)
        elif event_type == 'lbaas.instance.test':
            _send_test(event_type, lbid, tenant_id)
        return

    except:
        LOG.exception("MnB notify: unhandled exception")

    LOG.error("MnB notification unsuccessful. Type {0}, loadbalancer {1} "
              "tenant_id {2}".format(event_type, lbid, tenant_id))


def _notify(service, event_type, payload):
    priority = cfg.CONF.default_notification_level
    publisher_id = notifier_api.publisher_id(service)
    notifier_api.notify(None, publisher_id, event_type, priority, payload)


def test_mnb_connection():
    # Because the oslo notifier code does not have a return status
    # and exceptions are caught inside oslo (I know...), the best we
    # can do here is use the oslo rpc code to try a test connection
    # to the MnB servers before the notification(s) are sent.
    connected = False
    try:
        cx = rpc.create_connection()
        cx.close()
        LOG.info("Verified RPC connection is ready")
        connected = True
    except rpc_common.RPCException as e:
        LOG.error("RPC connect exception: %s", e)
    except Exception as e:
        LOG.error("Non-RPC connect exception: %s", e)
    return connected


def _send_create_or_delete(event_type, lbid, tenant_id):

    LOG.info(
        "Sending MnB {0} notification to MnB for "
        "loadbalancer {1} tenant_id {2}".format(
            event_type, lbid, tenant_id)
    )

    if not test_mnb_connection():
        # Abort the notification
        if event_type == 'lbaas.instance.create':
            LOG.info("Aborting Create Notifications. Could not connect")
        else:
            LOG.info("Aborting Delete Notifications. Could not connect")
        return

    with db_session() as session:
        lb = session.query(
            LoadBalancer.name,
            LoadBalancer.status,
            LoadBalancer.created,
            LoadBalancer.updated
        ).filter(LoadBalancer.id == lbid).\
            filter(LoadBalancer.tenantid == tenant_id).first()

        if lb is None:
            session.rollback()
            LOG.error("Load Balancer {0} not found for tenant {1}".format(
                lbid, tenant_id))
            return

        if event_type == 'lbaas.instance.create':
            date = lb.created
        else:
            date = lb.updated

        # Build the payload
        payload = _build_payload(date, date, lb.name, lbid,
                                 tenant_id, lb.status)

        _notify('lbaas', event_type, payload)
        session.commit()


def _send_exists(event_type):

    LOG.info("Sending MnB {0} notifications to MnB".format(event_type))
    count = 0
    with db_session() as session:
        lbs = session.query(
            LoadBalancer.id,
            LoadBalancer.tenantid,
            LoadBalancer.name,
            LoadBalancer.status,
            LoadBalancer.created,
            LoadBalancer.updated
        ).filter(LoadBalancer.status != 'DELETED').all()

        if not lbs:
            session.rollback()
            LOG.error("No existing Load Balancers found")
            return

        # Figure out our audit period beging/ending
        seconds = (cfg.CONF['admin_api'].exists_freq * 60)
        interval = datetime.timedelta(seconds=seconds)
        audit_period_ending = timeutils.utcnow()
        audit_period_beginning = audit_period_ending - interval
        audit_period_beginning = str(audit_period_beginning)
        audit_period_ending = str(audit_period_ending)

        for lb in lbs:
            LOG.info(
                "Sending MnB {0} notification to MnB for "
                "loadbalancer {1} tenant_id {2}".format(
                    event_type, lb.id, lb.tenantid)
            )

            # Build the payload
            payload = _build_payload(audit_period_beginning,
                                     audit_period_ending,
                                     lb.name, lb.id, lb.tenantid, lb.status)

            _notify('lbaas', event_type, payload)
            count += 1

        session.commit()
    LOG.info("Sent {0} MnB {1} notifications to MnB".format(count, event_type))


def _send_usage(event_type, start, stop):

    LOG.info("Sending MnB {0} notifications to MnB".format(event_type))
    N = cfg.CONF['admin_api'].usage_freq

    with db_session() as session:

        # Start by making sure we have stats in the Stats table and
        # track the oldest value in case we need it below.
        oldest, = session.query(Stats.period_end).\
            order_by(Stats.id.asc()).first()

        if oldest is None:
            # No Stats at all
            LOG.info("No usage statistics to send.")
            session.rollback()
            return

        if start is None:
            # The value in the DB must be '0000-00-00 00:00:00 so
            # as a starting point, we can find the oldest stat in
            # the Stats table and start from there.  No sense iterating
            # from 0000-00-00 to now looking for stats to send. Also
            # round it back to the previous update period
            start = _rounded_down_min(oldest, N)
            LOG.info("Starting usage notifications from first saved {0}".
                     format(start))

        # Now that we know where to start, make sure we have stats to
        # send for the time period. Use stats that end in this period.
        # It's ok if the stats started in a previous period. Some skew
        # is allowed.
        total = session.query(Stats).\
            filter(Stats.period_end >= start).\
            filter(Stats.period_end < stop).\
            count()
        if total == 0:
            LOG.info("No usage statistics to send between {0} and {1}"
                     .format(start, stop))
            session.rollback()
            return

        LOG.info("Found {0} total usage statistics to send between {1} and {2}"
                 .format(total, start, stop))

        # Get info on all of our loadbalancers for the payloads.
        loadbalancers = _get_lbs()

        # Get ready to loop through however N minute periods we
        # have to send. We do it this way rather than one lump sum
        # because finer grain data is probably needed on the MnB side.
        end = start + datetime.timedelta(minutes=N)
        count = 0
        while end <= stop:
            # Loop through all N periods up to the current period
            # sending usage notifications to MnB
            stats = session.query(
                Stats.lbid,
                func.sum(Stats.bytes_out)
            ).group_by(Stats.lbid).\
                filter(Stats.period_end >= start).\
                filter(Stats.period_end < end).\
                all()

            # Prep for the next loop here in case of continue
            prev_start = start
            prev_end = end
            start = end
            end = start + datetime.timedelta(minutes=N)

            if not stats:
                LOG.info("No usage statistics to send for period {0} to {1}".
                         format(prev_start, prev_end))
                continue
            else:
                LOG.info("Sending usage statistics for {0} to {1}".
                         format(prev_start, prev_end))

            audit_period_beginning = str(prev_start)
            audit_period_ending = str(prev_end)
            for lb in stats:
                lbid, byte_count = lb

                byte_count = int(byte_count)
                if lbid not in loadbalancers:
                    LOG.error("Loadbalancer {0} not found in DB "
                              "not sending usage statistics".format(lbid))
                    continue

                # Build the payload
                payload = _build_payload(audit_period_beginning,
                                         audit_period_ending,
                                         loadbalancers[lbid]["name"],
                                         lbid,
                                         loadbalancers[lbid]["tenant_id"],
                                         loadbalancers[lbid]["status"])

                payload["metrics"] = _build_metrics(byte_count)

                LOG.info(
                    "Sending MnB {0} notification to MnB for "
                    "loadbalancer {1} tenant_id {2} from "
                    "{3} to {4}: PAYLOAD = {5}".
                    format(event_type,
                           lbid,
                           loadbalancers[lbid]["tenant_id"],
                           prev_start,
                           prev_end,
                           payload)
                )
                _notify('lbaas', event_type, payload)
                count += 1

        # Purge old stats
        if cfg.CONF['admin_api'].stats_purge_enable:
            hours = cfg.CONF['admin_api'].stats_purge_days * 24
            delta = datetime.timedelta(hours=hours)
            exp = timeutils.utcnow() - delta
            exp_time = exp.strftime('%Y-%m-%d %H:%M:%S')
            purged = session.query(Stats).\
                filter(Stats.period_end < exp_time).\
                delete()
            LOG.info("Purged {0} usage statistics from before {1}".
                     format(purged, exp_time))

        session.commit()
    LOG.info("Sent {0} MnB {1} notifications to MnB".format(count, event_type))


def _send_test(event_type, lbid, tenant_id):

    # Build the payload
    now = str(timeutils.utcnow())
    LOG.error("Sending {0} test notifications".format(lbid))

    if not test_mnb_connection():
        # Abort the test notifications
        LOG.info("Aborting test Notifications. Could not connect")
        return

    #Note lbid is the number of notifications to send
    lbid += 1
    for x in xrange(1, lbid):
        payload = _build_payload(now, now, "Test LB", str(x),
                                 str(tenant_id), 'active')
        _notify('lbaas', 'lbaas.instance.test', payload)


def _build_payload(begin, end, name, id, tenant, status):
    return {
        "audit_period_beginning": begin,
        "audit_period_ending": end,
        "display_name": name,
        "id": id,
        "type": "lbaas.std",
        "type_id": 1,
        "tenant_id": tenant,
        "state": status.lower(),
        "state_description": status.lower()
    }


def _build_metrics(bytes):
    return {
        "metric_name": "lbaas.network.outgoing.bytes",
        "metric_type": "gauge",
        "metric_units": "BYTES",
        "metric_value": bytes
    }


def _rounded_down_min(ts, N):
    ts = ts - datetime.timedelta(minutes=ts.minute % N,
                                 seconds=ts.second,
                                 microseconds=ts.microsecond)
    return ts


def _get_lbs():
    all_lbs = {}
    with db_session() as session:
        lbs = session.query(
            LoadBalancer.id,
            LoadBalancer.tenantid,
            LoadBalancer.name,
            LoadBalancer.status,
        ).all()

        for lb in lbs:
            all_lbs[lb.id] = {
                "tenant_id": lb.tenantid,
                "name": lb.name,
                "status": lb.status
            }
        session.commit()
    return all_lbs
