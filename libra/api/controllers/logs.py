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

from pecan import request
from pecan import conf
from pecan.rest import RestController
import wsmeext.pecan as wsme_pecan
from wsme.exc import ClientSideError
from wsme import Unset
from libra.common.api.lbaas import LoadBalancer, Device, db_session, Counters
from libra.api.acl import get_limited_to_project
from libra.api.model.validators import LBLogsPost
from libra.common.api.gearman_client import submit_job
from libra.api.library.exp import NotFound, ImmutableEntity, ImmutableStates


class LogsController(RestController):
    def __init__(self, load_balancer_id=None):
        self.lbid = load_balancer_id

    @wsme_pecan.wsexpose(None, body=LBLogsPost, status_code=202)
    def post(self, body=None):
        if self.lbid is None:
            raise ClientSideError('Load Balancer ID has not been supplied')

        tenant_id = get_limited_to_project(request.headers)
        with db_session() as session:
            load_balancer = session.query(LoadBalancer).\
                filter(LoadBalancer.tenantid == tenant_id).\
                filter(LoadBalancer.id == self.lbid).\
                filter(LoadBalancer.status != 'DELETED').\
                first()
            if load_balancer is None:
                session.rollback()
                raise NotFound('Load Balancer not found')

            if load_balancer.status in ImmutableStates:
                session.rollback()
                raise ImmutableEntity(
                    'Cannot get logs from a Load Balancer in a non-ACTIVE '
                    'state, current state: {0}'.format(load_balancer.status)
                )

            load_balancer.status = 'PENDING_UPDATE'
            device = session.query(
                Device.id, Device.name, Device.status
            ).join(LoadBalancer.devices).\
                filter(LoadBalancer.id == self.lbid).\
                first()
            session.commit()
            data = {
                'deviceid': device.id
            }
            if body.objectStoreType != Unset:
                data['objectStoreType'] = body.objectStoreType.lower()
            else:
                data['objectStoreType'] = 'swift'

            if body.objectStoreBasePath != Unset:
                data['objectStoreBasePath'] = body.objectStoreBasePath
            else:
                data['objectStoreBasePath'] = conf.swift.swift_basepath

            if body.objectStoreEndpoint != Unset:
                data['objectStoreEndpoint'] = body.objectStoreEndpoint
            else:
                data['objectStoreEndpoint'] = '{0}/{1}'.\
                    format(conf.swift.swift_endpoint.rstrip('/'), tenant_id)

            if body.authToken != Unset:
                data['authToken'] = body.authToken
            else:
                data['authToken'] = request.headers.get('X-Auth-Token')

            submit_job(
                'ARCHIVE', device.name, data, self.lbid
            )
        with db_session() as session:
            try:
                load_balancer = session.query(LoadBalancer).\
                counter = session.query(Counters).\
                    filter(Counters.name == 'api_log_archive').first()
                counter.value += 1
                session.commit()
            except:
                pass
        return
