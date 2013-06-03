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

import logging
# pecan imports
from pecan import expose, abort, response, request
from pecan.rest import RestController
import wsmeext.pecan as wsme_pecan
from wsme.exc import ClientSideError, InvalidInput
from wsme import Unset
# other controllers
from nodes import NodesController
from virtualips import VipsController
# models
from libra.api.model.lbaas import LoadBalancer, Device, Node, session
from libra.api.model.lbaas import loadbalancers_devices, Limits
from libra.api.model.validators import LBPost, LBResp, LBVipResp, LBNode
from libra.api.library.gearman_client import submit_job
from libra.api.acl import get_limited_to_project


class LoadBalancersController(RestController):
    @expose('json')
    def get(self, load_balancer_id=None):
        """Fetches a list of load balancers or the details of one balancer if
        load_balancer_id is not empty.

        :param load_balancer_id: id of lb we want to get, if none it returns a
        list of all

        Url:
           GET /loadbalancers
           List all load balancers configured for the account.

        Url:
           GET /loadbalancers/{load_balancer_id}
           List details of the specified load balancer.

        Returns: dict
        """

        tenant_id = get_limited_to_project(request.headers)

        # if we don't have an id then we want a list of them own by this tenent
        if not load_balancer_id:
            load_balancers = {'loadBalancers': session.query(
                LoadBalancer.name, LoadBalancer.id, LoadBalancer.protocol,
                LoadBalancer.port, LoadBalancer.algorithm,
                LoadBalancer.status, LoadBalancer.created,
                LoadBalancer.updated
            ).filter_by(tenantid=tenant_id).all()}
        else:
            load_balancers = session.query(
                LoadBalancer.name, LoadBalancer.id, LoadBalancer.protocol,
                LoadBalancer.port, LoadBalancer.algorithm,
                LoadBalancer.status, LoadBalancer.created,
                LoadBalancer.updated
            ).join(LoadBalancer.devices).\
                filter(LoadBalancer.tenantid == tenant_id).\
                filter(LoadBalancer.id == load_balancer_id).\
                first()

            if not load_balancers:
                response.status = 400
                session.rollback()
                return dict(
                    faultcode='Client',
                    faultstring="Load Balancer ID not found"
                )

            load_balancers = load_balancers._asdict()
            virtualIps = session.query(
                Device.id, Device.floatingIpAddr
            ).join(LoadBalancer.devices).\
                filter(LoadBalancer.tenantid == tenant_id).\
                filter(LoadBalancer.id == load_balancer_id).\
                all()

            load_balancers['virtualIps'] = []
            for item in virtualIps:
                vip = item._asdict()
                vip['type'] = 'PUBLIC'
                vip['ipVersion'] = 'IPV4'
                load_balancers['virtualIps'].append(vip)

            nodes = session.query(
                Node.id, Node.address, Node.port, Node.status, Node.enabled
            ).join(LoadBalancer.nodes).\
                filter(LoadBalancer.tenantid == tenant_id).\
                filter(LoadBalancer.id == load_balancer_id).\
                all()

            load_balancers['nodes'] = []
            for item in nodes:
                node = item._asdict()
                if node['enabled'] == 1:
                    node['condition'] = 'ENABLED'
                else:
                    node['condition'] = 'DISABLED'
                del node['enabled']
                load_balancers['nodes'].append(node)

        session.commit()
        response.status = 200
        return load_balancers

    @wsme_pecan.wsexpose(LBResp, body=LBPost, status=202)
    def post(self, body=None):
        """Accepts edit if load_balancer_id isn't blank or create load balancer
        posts.

        :param load_balancer_id: id of lb
        :param *args: holds the posted json or xml data

        Urls:
           POST /loadbalancers/{load_balancer_id}
           PUT  /loadbalancers

        Notes:
           curl -i -H "Accept: application/json" -X POST \
           -d "data={"name": "my_lb"}" \
           http://dev.server:8080/loadbalancers/100

        Returns: dict
        """
        tenant_id = get_limited_to_project(request.headers)
        if body.nodes == Unset:
            raise ClientSideError(
                'At least one backend node needs to be supplied'
            )

        lblimit = session.query(Limits.value).\
            filter(Limits.name == 'maxLoadBalancers').scalar()
        nodelimit = session.query(Limits.value).\
            filter(Limits.name == 'maxNodesPerLoadBalancer').scalar()
        count = session.query(LoadBalancer).\
            filter(LoadBalancer.tenantid == tenant_id).count()

        # TODO: this should probably be a 413, not sure how to do that yet
        if count >= lblimit:
            raise ClientSideError(
                'Account has hit limit of {0} Load Balancers'.
                format(lblimit)
            )
        if len(body.nodes) > nodelimit:
            raise ClientSideError(
                'Too many backend nodes supplied (limit is {0}'.
                format(nodelimit)
            )

        device = None
        old_lb = None
        # if we don't have an id then we want to create a new lb
        lb = LoadBalancer()
        if not body.virtualIps:
            # find free device
            device = session.query(Device).\
                filter(~Device.id.in_(
                    session.query(loadbalancers_devices.c.device)
                )).\
                filter(Device.status == "OFFLINE").\
                first()
        else:
            virtual_id = body.virtualIps[0].id
            # This is an additional load balancer
            device = session.query(
                Device
            ).filter(Device.id == virtual_id).\
                first()
            old_lb = session.query(
                LoadBalancer
            ).join(LoadBalancer.devices).\
                filter(LoadBalancer.tenantid == tenant_id).\
                filter(Device.id == virtual_id).\
                first()
            if old_lb is None:
                raise InvalidInput(
                    'virtualIps', virtual_id, 'Invalid virtual IP provided'
                )

            if body.protocol == Unset or body.protocol.lower() == 'HTTP':
                old_count = session.query(
                    LoadBalancer
                ).join(LoadBalancer.devices).\
                    filter(LoadBalancer.tenantid == tenant_id).\
                    filter(Device.id == virtual_id).\
                    filter(LoadBalancer.protocol == 'HTTP').\
                    count()
                if old_count:
                    # Error here, can have only one HTTP
                    raise ClientSideError(
                        'Only one HTTP load balancer allowed per device'
                    )
            elif body.protocol.lower() == 'TCP':
                old_count = session.query(
                    LoadBalancer
                ).join(LoadBalancer.devices).\
                    filter(LoadBalancer.tenantid == tenant_id).\
                    filter(Device.id == virtual_id).\
                    filter(LoadBalancer.protocol == 'TCP').\
                    count()
                if old_count:
                    # Error here, can have only one TCP
                    raise ClientSideError(
                        'Only one TCP load balancer allowed per device'
                    )

        if device is None:
            raise RuntimeError('No devices available')

        lb.tenantid = tenant_id
        lb.name = body.name
        if body.protocol and body.protocol.lower() == 'tcp':
            lb.protocol = 'TCP'
        else:
            lb.protocol = 'HTTP'

        if body.port:
            lb.port = body.port
        else:
            if lb.protocol == 'HTTP':
                lb.port = 80
            else:
                lb.port = 443

        lb.status = 'BUILD'
        lb.created = None

        if body.algorithm:
            lb.algorithm = body.algorithm.upper()
        else:
            lb.algorithm = 'ROUND_ROBIN'

        lb.devices = [device]
        # write to database
        session.add(lb)
        session.flush()
        #refresh the lb record so we get the id back
        session.refresh(lb)
        for node in body.nodes:
            if node.condition == 'DISABLED':
                enabled = 0
            else:
                enabled = 1
            out_node = Node(
                lbid=lb.id, port=node.port, address=node.address,
                enabled=enabled, status='ONLINE', weight=0
            )
            session.add(out_node)

        # now save the loadbalancer_id to the device and switch its status
        # to online
        device.status = "ONLINE"

        session.flush()

        job_data = {
            'hpcs_action': 'UPDATE',
            'loadBalancers': [{
                'name': lb.name,
                'protocol': lb.protocol,
                'port': lb.port,
                'nodes': []
            }]
        }
        for node in body.nodes:
            node_data = {
                'port': node.port, 'address': node.address, 'weight': '1'
            }
            if node.condition:
                node_data['condition'] = node.condition
            job_data['loadBalancers'][0]['nodes'].append(node_data)

        if old_lb:
            old_nodes = session.query(Node).\
                filter(Node.lbid == old_lb.id).all()
            old_lb_data = {
                'name': old_lb.name,
                'protocol': old_lb.protocol,
                'port': old_lb.port,
                'nodes': []
            }
            for node in old_nodes:
                if node.enabled:
                    condition = 'ENABLED'
                else:
                    condition = 'DISABLED'
                old_lb_data['nodes'].append({
                    'port': node.port, 'address': node.address,
                    'weight': node.weight, 'condition': condition
                })
            job_data['loadBalancers'].append(old_lb_data)
        try:
            # trigger gearman client to create new lb
            result = submit_job(
                'UPDATE', device.name, job_data, lb.id
            )
            # do something with result
            if result:
                pass
            return_data = LBResp()
            return_data.id = lb.id
            return_data.name = lb.name
            return_data.protocol = lb.protocol
            return_data.port = lb.port
            return_data.algorithm = lb.algorithm
            return_data.status = lb.status
            return_data.created = lb.created
            return_data.updated = lb.updated
            vip_resp = LBVipResp(
                address=device.floatingIpAddr, id=device.id,
                type='PUBLIC', ipVersion='IPV4'
            )
            return_data.virtualIps = [vip_resp]
            return_data.nodes = []
            for node in body.nodes:
                out_node = LBNode(
                    port=node.port, address=node.address,
                    condition=node.condition
                )
                return_data.nodes.append(out_node)
            session.commit()
            return return_data
        except:
            logger = logging.getLogger(__name__)
            logger.exception('Error communicating with load balancer pool')
            errstr = 'Error communicating with load balancer pool'
            session.rollback()
            raise ClientSideError(errstr)

    @expose('json')
    def delete(self, load_balancer_id):
        """Remove a load balancer from the account.

        :param load_balancer_id: id of lb

        Urls:
           DELETE   /loadbalancers/{load_balancer_id}

        Notes:
           curl -i -H "Accept: application/json" -X DELETE
           http://dev.server:8080/loadbalancers/1

        Returns: None
        """
        # TODO: send gearman message (use PENDING_DELETE), make it an update
        # message when more than one device per LB
        tenant_id = get_limited_to_project(request.headers)
        # grab the lb
        lb = session.query(LoadBalancer).\
            filter(LoadBalancer.id == load_balancer_id).\
            filter(LoadBalancer.tenantid == tenant_id).first()

        if lb is None:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Load Balancer ID is not valid"
            )
        try:
            session.query(Node).filter(Node.lbid == load_balancer_id).delete()
            lb.status = 'DELETED'
            device = session.query(
                Device.id, Device.status
            ).join(LoadBalancer.devices).\
                filter(LoadBalancer.id == load_balancer_id).\
                first()
            session.execute(loadbalancers_devices.delete().where(
                loadbalancers_devices.c.loadbalancer == load_balancer_id
            ))
            if device:
                device.status = 'OFFLINE'
            session.flush()
            # trigger gearman client to create new lb
            #result = gearman_client.submit_job('DELETE', lb.output_to_json())

            response.status = 202

            session.commit()

            return None
        except:
            logger = logging.getLogger(__name__)
            logger.exception('Error communicating with load balancer pool')
            response.status = 500
            return dict(
                faultcode="Server",
                faultstring="Error communication with load balancer pool"
            )

    def virtualips(self, load_balancer_id):
        """Returns a list of virtual ips attached to a specific Load Balancer.

        :param load_balancer_id: id of lb

        Url:
           GET /loadbalancers/{load_balancer_id}/virtualips

        Returns: dict
        """
        tenant_id = get_limited_to_project(request.headers)
        if not load_balancer_id:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Load Balancer ID not provided"
            )
        device = session.query(
            Device.id, Device.floatingIpAddr
        ).join(LoadBalancer.devices).\
            filter(LoadBalancer.id == load_balancer_id).\
            filter(LoadBalancer.tenantid == tenant_id).first()

        if not device:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Load Balancer ID not valid"
            )
        resp = {
            "virtualIps": [{
                "id": device.id,
                "address": device.floatingIpAddr,
                "type": "PUBLIC",
                "ipVersion": "IPV4"
            }]
        }

        return resp

    def usage(self, load_balancer_id):
        """List current and historical usage.

        :param load_balancer_id: id of lb

        Url:
           GET /loadbalancers/{load_balancer_id}/usage

        Returns: dict
        """
        response.status = 201
        return None

    @expose('json')
    def _lookup(self, lbid, *remainder):
        """Routes more complex url mapping.

        Most things are /loadbalancer/{id}/function/... so this routes that

        Raises: 404
        """
        if len(remainder):
            if remainder[0] == 'nodes':
                return NodesController(lbid), remainder[1:]
            if remainder[0] == 'virtualips':
                return VipsController(lbid), remainder[1:]

        abort(404)
