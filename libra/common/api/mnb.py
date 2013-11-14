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
from libra.common.api.lbaas import LoadBalancer, db_session, Billing
#from libra.common.api.lbaas import loadbalancers_devices, Device
from libra.openstack.common.notifier import api as notifier_api
from libra.openstack.common import timeutils
from libra.openstack.common import log as logging
from libra.openstack.common import rpc
from libra.openstack.common.rpc import common as rpc_common
from sqlalchemy.sql import func


LOG = logging.getLogger(__name__)


def update_mnb(event_type, lbid, tenant_id):
    # Start a new thread
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


def _test_connection():
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
        payload = {
            "audit_period_beginning": date,
            "audit_period_ending": date,
            "record_type": "event",
            "display_name": lb.name,
            "id": lbid,
            "type": "lbaas.std",
            "type_id": 1,
            "tenant_id": tenant_id,
            "state": lb.status,
            "state_description": lb.status,
            "region": "az-3.region-a.geo-1"
        }

        if not _test_connection():
            # Abort the notification
            session.rollback()
            if event_type == 'lbaas.instance.create':
                LOG.info("Aborting Create Notifications. Could not connect")
            else:
                LOG.info("Aborting Delete Notifications. Could not connect")
            return

        _notify('lbaas', event_type, payload)
        session.commit()


def _send_exists(event_type):

    LOG.info("Sending MnB {0} notifications to MnB".format(event_type))

    with db_session() as session:
        lbs = session.query(
            LoadBalancer.id,
            LoadBalancer.tenantid,
            LoadBalancer.name,
            LoadBalancer.status,
            LoadBalancer.created,
            LoadBalancer.updated
        ).filter(LoadBalancer.status != 'DELETED').all()

        if lbs is None:
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

        # Check the connection before sending the notifications
        if _test_connection():
            #Update the exists timestamp now since it is locked for update
            session.query(Billing).update({"exists_last_sent": func.now()},
                                          synchronize_session='fetch')
            session.commit()
        else:
            # Abort the exists notifications
            session.rollback()
            LOG.info("Aborting Exists Notifications. Could not connect")
            return

        for lb in lbs:
            LOG.info(
                "Sending MnB {0} notification to MnB for "
                "loadbalancer {1} tenant_id {2}".format(
                    event_type, lb.id, lb.tenantid)
            )

            # Build the payload
            payload = {
                "audit_period_beginning": audit_period_beginning,
                "audit_period_ending": audit_period_ending,
                "record_type": "event",
                "display_name": lb.name,
                "id": lb.id,
                "type": "lbaas.std",
                "type_id": 1,
                "tenant_id": lb.tenantid,
                "state": lb.status,
                "state_description": lb.status,
                "region": "az-3.region-a.geo-1"
            }
            _notify('lbaas', event_type, payload)

        return


def _send_usage(event_type, lbid, tenant_id):
    '''
    LOG.info("Sending MnB {0} notifications to MnB".format(event_type))

    with db_session() as session:
        lbs = session.query(
            LoadBalancer.id,
            LoadBalancer.tenantid,
            LoadBalancer.name,
            LoadBalancer.status,
            LoadBalancer.created,
            LoadBalancer.updated
        ).filter(LoadBalancer.status != 'DELETED').all()

        if lbs is None:
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

        # Check the connection before sending the notifications
        if _test_connection():
            #Update the usage timestamp now since it is locked for update
            session.query(Billing).update({"usage_last_sent": func.now()},
                                          synchronize_session='fetch')
            session.commit()
        else:
            # Abort the exists notifications
            session.rollback()
            LOG.info("Aborting Usage Notifications. Could not connect")
            return

        for lb in lbs:
            LOG.info(
                "Sending MnB {0} notification to MnB for "
                "loadbalancer {1} tenant_id {2}".format(
                    event_type, lb.id, lb.tenantid)
            )

            # Build the payload
            payload = {
                "audit_period_beginning": audit_period_beginning,
                "audit_period_ending": audit_period_ending,
                "record_type": "event",
                "display_name": lb.name,
                "id": lb.id,
                "type": "lbaas.std",
                "type_id": 1,
                "tenant_id": lb.tenantid,
                "state": lb.status,
                "state_description": lb.status,
                "region": "az-3.region-a.geo-1"
            }
            _notify('lbaas', event_type, payload)

        return

    '''
    pass


def _send_test(event_type, lbid, tenant_id):

    # Build the payload
    now = str(timeutils.utcnow())
    LOG.error("Sending {0} test notifications".format(lbid))

    if not _test_connection():
        # Abort the test notifications
        LOG.info("Aborting test Notifications. Could not connect")
        return

    #Note lbid is the number of notifications to send
    lbid += 1
    for x in xrange(1, lbid):
        payload = {
            "audit_period_beginning": now,
            "audit_period_ending": now,
            "record_type": "event",
            "display_name": "Test LB",
            "id": str(x),
            "type": "lbaas.std",
            "type_id": '1',
            "tenant_id": str(tenant_id),
            "state": "ACTIVE",
            "state_description": "ACTIVE",
            "region": "az-3.region-a.geo-1"
        }

        _notify('lbaas', 'lbaas.instance.test', payload)
