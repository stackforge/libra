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
import logging


from oslo.config import cfg
from libra.common.api.lbaas import LoadBalancer, db_session
#from libra.common.api.lbaas import loadbalancers_devices, Device
from libra.openstack.common.notifier import api as notifier_api
from libra.openstack.common import timeutils


def update_mnb(event_type, lbid, tenant_id):
    # If billing is disabled, just return
    if not cfg.CONF['admin_api'].billing_enable:
        return
    logger = logging.getLogger(__name__)
    #if event_type == 'lbaas.instance.test':
    client_job(logger, event_type, lbid, tenant_id)
    #else:
    #eventlet.spawn_n(client_job, logger, event_type, lbid, tenant_id)
    #eventlet.sleep


def client_job(logger, event_type, lbid, tenant_id):

    try:
        if(event_type == 'lbaas.instance.create' or
           event_type == 'lbaas.instance.delete'):
            _send_create_or_delete(logger, event_type, lbid, tenant_id)
        elif event_type == 'lbaas.instance.exists':
            _send_exists(logger, event_type)
        elif event_type == 'lbaas.bandwidth.usage':
            _send_usage(logger, event_type, lbid, tenant_id)
        elif event_type == 'lbaas.instance.test':
            _send_test(logger, event_type, lbid, tenant_id)
        return

    except:
        logger.exception("MnB notify: unhandled exception")

    logger.error("MnB notification unsuccessful. Type {0}, loadbalancer {1} "
                 "tenant_id {2}".format(event_type, lbid, tenant_id))


def _notify(logger, service, event_type, payload):
    priority = cfg.CONF.default_notification_level
    publisher_id = notifier_api.publisher_id(service)
    notifier_api.notify(None, publisher_id, event_type, priority, payload)


def _send_create_or_delete(logger, event_type, lbid, tenant_id):

    logger.info(
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
            logger.error("Load Balancer {0} not found for tenant {1}".format(
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
            "state_description": lb.status
        }

        _notify(None, 'lbaas', event_type, payload)
        session.commit()


def _send_exists(logger, event_type):

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
            logger.error("No existing Load Balancers found")
            return 0

        # Figure out our audit period beging/ending
        seconds = (cfg.CONF['admin_api'].exists_freq * 60)
        interval = datetime.timedelta(seconds=seconds)
        audit_period_ending = timeutils.utcnow()
        audit_period_beginning = audit_period_ending - interval
        audit_period_beginning = str(audit_period_beginning)
        audit_period_ending = str(audit_period_ending)

        count = 0
        for lb in lbs:
            logger.info(
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
                "state_description": lb.status
            }
            _notify(None, 'lbaas', event_type, payload)
            count += 1
        session.commit()
        return count


def _send_usage(logger, event_type, lbid, tenant_id):
    with db_session() as session:
        lb = session.query(
            LoadBalancer.name,
            LoadBalancer.status,
            LoadBalancer.created
        ).filter(LoadBalancer.id == lbid).\
            filter(LoadBalancer.tenant_id == tenant_id).first()

        if lb is None:
            session.rollback()
            logger.error("Load Balancer {0} not found for tenant {1}".format(
                lbid, tenant_id))
            return

        # Build the payload
        payload = {
            "audit_period_beginning": lb.created,
            "audit_period_ending": lb.created,
            "record_type": "event",
            "display_name": lb.name,
            "instance_id": lbid,
            "tenant_id": tenant_id
        }

        _notify(None, 'lbaas', event_type, payload)
        session.commit()


def _send_test(logger, event_type, lbid, tenant_id):
    # Build the payload
    now = str(timeutils.utcnow())
    payload = {
        "audit_period_beginning": now,
        "audit_period_ending": now,
        "record_type": "event",
        "display_name": "Test LB",
        "id": str(lbid),
        "type": "lbaas.std",
        "type_id": '1',
        "tenant_id": str(tenant_id),
        "state": "ACTIVE",
        "state_description": "ACTIVE",
        "region": "az-3.region-a.geo-1"
    }

    _notify(None, 'lbaas', 'lbaas.instance.create', payload)
