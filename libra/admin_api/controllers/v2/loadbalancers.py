# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright 2014 Hewlett-Packard Development Company, L.P.
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

# pecan imports
import ipaddress
from pecan import expose, request, response
from pecan.rest import RestController
from libra.common.api.lbaas import LoadBalancer, Device, db_session
from libra.common.api.lbaas import Vip, Node, HealthMonitor
from libra.openstack.common import log
from libra.admin_api.acl import tenant_is_user

LOG = log.getLogger(__name__)


class LoadBalancersController(RestController):

    @expose('json')
    def get(
        self, lb_id=None, status=None, tenant=None, name=None, ip=None,
        vip=None
    ):
        """
        Gets either a list of all loadbalancers or a details for a single
        loadbalancer.

        :param lb_id: id of the loadbalancer (unless getall)
        Url:
            GET /loadbalancers
            List all loadbalancers
        Url:
            GET /loadbalancers/{lb_id}
            List details of a particular device
        Returns: dict
        """

        if not tenant_is_user(request.headers):
            response.status = 401
            return dict(
                faultcode="Client",
                faultstring="Client not authorized to access this function"
            )

        with db_session() as session:
            # if there is no lb_id then we want a list of loadbalancers
            if not lb_id:
                loadbalancers = {'loadBalancers': []}

                lbs = session.query(
                    LoadBalancer.id, LoadBalancer.name, LoadBalancer.status,
                    LoadBalancer.tenant, Vip.id.label('vipid'),
                    Vip.ip.label('vip'),
                    Device.floatingIpAddr.label('ip'),
                    LoadBalancer.protocol, LoadBalancer.algorithm,
                    LoadBalancer.port, LoadBalancer.created,
                    LoadBalancer.updated)

                if status is not None:
                    if status not in ('ACTIVE', 'BUILD', 'DEGRADED', 'ERROR'):
                        response.status = 400
                        return dict(
                            faultcode="Client",
                            faultstring="Invalid status: " + status
                        )
                    lbs.filter(LoadBalancer.status == status)

                if tenant is not None:
                    lbs.filter(LoadBalancer.tenant == tenant)

                if name is not None:
                    lbs.filter(LoadBalancer.name == name)

                if ip is not None:
                    lbs.filter(Device.floatingIpAddr == ip)

                if vip is not None:
                    vip_num = int(ipaddress.IPv4Address(unicode(vip)))
                    lbs.filter(Vip.ip == vip_num)

                lbs.join(LoadBalancer.device).join(Device.vip).all()

                for item in lbs:
                    lb = item._asdict()
                    if lb['vip']:
                        lb['vip'] = [{
                            "id": lb['vipid'],
                            "address": str(ipaddress.IPv4Address(lb['vip']))
                        }]
                        del(lb['vip'])
                        del(lb['vipid'])
                    else:
                        lb['vip'] = [None]
                        del(lb['vipid'])
                    loadbalancers['loadBalancers'].append(lb)

            else:
                lbs = session.query(
                    LoadBalancer.name, LoadBalancer.id, LoadBalancer.protocol,
                    LoadBalancer.port, LoadBalancer.algorithm,
                    LoadBalancer.status, LoadBalancer.created,
                    LoadBalancer.updated, LoadBalancer.errmsg,
                    Vip.id.label('vipid'), Vip.ip.label('vip')
                ).join(LoadBalancer.devices).\
                    outerjoin(Device.vip).\
                    filter(LoadBalancer.id == lb_id).\
                    first()

                if not lbs:
                    response.status = 404
                    return dict(
                        faultcode="Client",
                        faultstring="Loadbalancer " + lb_id + " not found"
                    )
                loadbalancers = lbs._asdict()
                nodes = session.query(Node).\
                    filter(Node.lbid == lb_id).all()
                loadbalancers['nodes'] = []

                for item in nodes:
                    node = item._asdict()
                    if node['enabled'] == 1:
                        node['condition'] = 'ENABLED'
                    else:
                        node['condition'] = 'DISABLED'
                    del node['enabled']
                    node['port'] = str(node['port'])
                    node['id'] = str(node['id'])
                    if node['weight'] == 1:
                        del node['weight']
                    loadbalancers['nodes'].append(node)

                if loadbalancers['vip']:
                    loadbalancers['vip'] = [{
                        "id": loadbalancers['vipid'],
                        "address": str(
                            ipaddress.IPv4Address(loadbalancers['vip'])
                        )
                    }]
                    del(loadbalancers['vip'])
                    del(loadbalancers['vipid'])
                else:
                    loadbalancers['vip'] = [None]
                    del(loadbalancers['vipid'])
                if not loadbalancers['errmsg']:
                    loadbalancers['statusDescription'] = None
                else:
                    loadbalancers['statusDescription'] =\
                        loadbalancers['errmsg']
                del(loadbalancers['errmsg'])

                monitor = session.query(
                    HealthMonitor.type, HealthMonitor.delay,
                    HealthMonitor.timeout, HealthMonitor.attempts,
                    HealthMonitor.path
                ).join(LoadBalancer.monitors).\
                    filter(LoadBalancer.id == self.lbid).first()

                if monitor is None:
                    monitor_data = {}
                else:
                    monitor_data = {
                        'type': monitor.type,
                        'delay': monitor.delay,
                        'timeout': monitor.timeout,
                        'attemptsBeforeDeactivation': monitor.attempts
                    }
                if monitor.path:
                    monitor_data['path'] = monitor.path

                loadbalancers['monitor'] = monitor_data

                session.commit()

            return loadbalancers

# TODO: we should be able to delete loadbalancers, require lb_id, name,
# tenant and a confirm flag for verification
