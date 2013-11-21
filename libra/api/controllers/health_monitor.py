# vim: tabstop=4 shiftwidth=4 softtabstop=4
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

from pecan import request, response
from pecan.rest import RestController
import wsmeext.pecan as wsme_pecan
from wsme.exc import ClientSideError
from wsme import Unset
from urllib import quote
from libra.common.api.lbaas import LoadBalancer, db_session
from libra.common.api.lbaas import Device, HealthMonitor
from libra.api.acl import get_limited_to_project
from libra.api.model.validators import LBMonitorPut, LBMonitorResp
from libra.common.api.gearman_client import submit_job
from libra.api.library.exp import NotFound, ImmutableEntity, ImmutableStates


class HealthMonitorController(RestController):
    """functions for /loadbalancers/{loadBalancerId}/healthmonitor routing"""
    def __init__(self, load_balancer_id=None):
        self.lbid = load_balancer_id

    @wsme_pecan.wsexpose(None)
    def get(self):
        """Retrieve the health monitor configuration, if one exists.
        Url:
           GET /loadbalancers/{load_balancer_id}/healthmonitor

        Returns: dict
        """
        if not self.lbid:
            raise ClientSideError('Load Balancer ID has not been supplied')

        tenant_id = get_limited_to_project(request.headers)
        with db_session() as session:
            # grab the lb
            monitor = session.query(
                HealthMonitor.type, HealthMonitor.delay,
                HealthMonitor.timeout, HealthMonitor.attempts,
                HealthMonitor.path
            ).join(LoadBalancer.monitors).\
                filter(LoadBalancer.id == self.lbid).\
                filter(LoadBalancer.tenantid == tenant_id).\
                filter(LoadBalancer.status != 'DELETED').\
                first()

            response.status = 200
            if monitor is None:
                session.rollback()
                return {}

            monitor_data = {
                'type': monitor.type,
                'delay': monitor.delay,
                'timeout': monitor.timeout,
                'attemptsBeforeDeactivation': monitor.attempts
            }

            if monitor.path:
                monitor_data['path'] = monitor.path

            session.commit()
        return monitor_data

    @wsme_pecan.wsexpose(LBMonitorResp, body=LBMonitorPut, status_code=202)
    def put(self, body=None):
        """Update the settings for a health monitor.

        :param load_balancer_id: id of lb
        :param *args: holds the posted json or xml data

        Url:
           PUT /loadbalancers/{load_balancer_id}/healthmonitor

        Returns: dict
        """
        if not self.lbid:
            raise ClientSideError('Load Balancer ID has not been supplied')

        tenant_id = get_limited_to_project(request.headers)
        with db_session() as session:
            # grab the lb
            query = session.query(LoadBalancer, HealthMonitor).\
                outerjoin(LoadBalancer.monitors).\
                filter(LoadBalancer.id == self.lbid).\
                filter(LoadBalancer.tenantid == tenant_id).\
                filter(LoadBalancer.status != 'DELETED').first()

            if query is None:
                session.rollback()
                raise NotFound("Load Balancer not found")

            lb, monitor = query

            if lb is None:
                session.rollback()
                raise NotFound('Load Balancer not found')

            # Check inputs
            if (
                body.type == Unset or
                body.delay == Unset or
                body.timeout == Unset or
                body.attemptsBeforeDeactivation == Unset
            ):
                session.rollback()
                raise ClientSideError(
                    "Missing field(s): {0}, {1}, {2}, and {3} are required"
                    .format("type", "delay", "timeout",
                            "attemptsBeforeDeactivation")
                )

            data = {
                "lbid": self.lbid,
                "type": body.type,
                "delay": int(body.delay),
                "timeout": int(body.timeout),
                "attempts": int(body.attemptsBeforeDeactivation)
            }

            # Path only required when type is not CONNECT
            if body.path != Unset and body.path is not None:
                if body.type == "CONNECT":
                    session.rollback()
                    raise ClientSideError(
                        "Path argument is invalid with CONNECT type"
                    )
                # Encode everything apart from allowed characters
                # This ignore list in the second parameter is everything in
                # RFC3986 section 2 that isn't already ignored by
                # urllib.quote()
                if body.path:
                    data["path"] = quote(body.path, "/~+*,;:!$'[]()?&=#%")
                else:
                    data["path"] = ""
                # If path is empty, set to /
                if len(data["path"]) == 0 or data["path"][0] != "/":
                    session.rollback()
                    raise ClientSideError(
                        "Path must begin with leading /"
                    )
            else:
                if body.type != "CONNECT":
                    session.rollback()
                    raise ClientSideError(
                        "Path argument is required"
                    )
                data["path"] = None

            if data["timeout"] > data["delay"]:
                session.rollback()
                raise ClientSideError(
                    "timeout cannot be greater than delay"
                )

            if (data["attempts"] < 1 or data["attempts"] > 10):
                session.rollback()
                raise ClientSideError(
                    "attemptsBeforeDeactivation must be between 1 and 10"
                )

            if monitor is None:
                # This is ok for LBs that already existed without
                # monitoring. Create a new entry.
                monitor = HealthMonitor(
                    lbid=self.lbid, type=data["type"], delay=data["delay"],
                    timeout=data["timeout"], attempts=data["attempts"],
                    path=data["path"]
                )
                session.add(monitor)
            else:
                # Modify the existing entry.
                monitor.type = data["type"]
                monitor.delay = data["delay"]
                monitor.timeout = data["timeout"]
                monitor.attempts = data["attempts"]
                monitor.path = data["path"]

            if lb.status in ImmutableStates:
                session.rollback()
                raise ImmutableEntity(
                    'Cannot modify a Load Balancer in a non-ACTIVE state'
                    ', current state: {0}'
                    .format(lb.status)
                )

            lb.status = 'PENDING_UPDATE'
            device = session.query(
                Device.id, Device.name, Device.status
            ).join(LoadBalancer.devices).\
                filter(LoadBalancer.id == self.lbid).\
                first()

            return_data = LBMonitorResp()
            return_data.type = data["type"]
            return_data.delay = str(data["delay"])
            return_data.timeout = str(data["timeout"])
            return_data.attemptsBeforeDeactivation =\
                str(data["attempts"])
            if ((data["path"] is not None) and (len(data["path"]) > 0)):
                return_data.path = data["path"]

            session.commit()
            submit_job(
                'UPDATE', device.name, device.id, lb.id
            )
            return return_data

    @wsme_pecan.wsexpose(None, status_code=202)
    def delete(self):
        """Remove the health monitor.

        :param load_balancer_id: id of lb

        Url:
           DELETE /loadbalancers/{load_balancer_id}/healthmonitor

        Returns: void
        """
        if not self.lbid:
            raise ClientSideError('Load Balancer ID has not been supplied')

        tenant_id = get_limited_to_project(request.headers)
        with db_session() as session:
            query = session.query(
                LoadBalancer, HealthMonitor
            ).outerjoin(LoadBalancer.monitors).\
                filter(LoadBalancer.tenantid == tenant_id).\
                filter(LoadBalancer.id == self.lbid).\
                filter(LoadBalancer.status != 'DELETED').\
                first()

            if query is None:
                session.rollback()
                raise NotFound("Load Balancer not found")

            lb, monitor = query

            if lb is None:
                session.rollback()
                raise NotFound("Load Balancer not found")

            if monitor is not None:
                session.delete(monitor)
                session.flush()

            device = session.query(
                Device.id, Device.name
            ).join(LoadBalancer.devices).\
                filter(LoadBalancer.id == self.lbid).\
                first()
            session.commit()
            submit_job(
                'UPDATE', device.name, device.id, self.lbid
            )
            return None
