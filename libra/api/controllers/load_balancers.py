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
import socket
# pecan imports
from pecan import expose, abort, response, request
from pecan.rest import RestController
import wsmeext.pecan as wsme_pecan
from wsme.exc import ClientSideError, InvalidInput
from wsme import Unset
# other controllers
from nodes import NodesController
from virtualips import VipsController
from logs import LogsController
# models
from libra.api.model.lbaas import LoadBalancer, Device, Node, db_session
from libra.api.model.lbaas import loadbalancers_devices, Limits
from libra.api.model.validators import LBPut, LBPost, LBResp, LBVipResp
from libra.api.model.validators import LBRespNode
from libra.api.library.gearman_client import submit_job
from libra.api.acl import get_limited_to_project
from libra.api.library.exp import OverLimit


class LoadBalancersController(RestController):
    def __init__(self, lbid=None):
        self.lbid = lbid

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
        with db_session() as session:
            # if we don't have an id then we want a list of them own by this
            # tenent
            if not load_balancer_id:
                lbs = session.query(
                    LoadBalancer.name, LoadBalancer.id, LoadBalancer.protocol,
                    LoadBalancer.port, LoadBalancer.algorithm,
                    LoadBalancer.status, LoadBalancer.created,
                    LoadBalancer.updated
                ).filter(LoadBalancer.tenantid == tenant_id).\
                    filter(LoadBalancer.status != 'DELETED').all()

                load_balancers = {'loadBalancers': []}

                for lb in lbs:
                    lb = lb._asdict()
                    lb['id'] = str(lb['id'])
                    load_balancers['loadBalancers'].append(lb)
            else:
                load_balancers = session.query(
                    LoadBalancer.name, LoadBalancer.id, LoadBalancer.protocol,
                    LoadBalancer.port, LoadBalancer.algorithm,
                    LoadBalancer.status, LoadBalancer.created,
                    LoadBalancer.updated, LoadBalancer.statusDescription
                ).join(LoadBalancer.devices).\
                    filter(LoadBalancer.tenantid == tenant_id).\
                    filter(LoadBalancer.id == load_balancer_id).\
                    first()

                if not load_balancers:
                    response.status = 400
                    session.rollback()
                    return dict(
                        message='Bad Request',
                        details="Load Balancer ID not found"
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
                    vip['address'] = vip['floatingIpAddr']
                    del(vip['floatingIpAddr'])
                    load_balancers['virtualIps'].append(vip)

                nodes = session.query(
                    Node.id, Node.address, Node.port, Node.status, Node.enabled
                ).join(LoadBalancer.nodes).\
                    filter(LoadBalancer.tenantid == tenant_id).\
                    filter(LoadBalancer.id == load_balancer_id).\
                    all()

                load_balancers['id'] = str(load_balancers['id'])
                if not load_balancers['statusDescription']:
                    load_balancers['statusDescription'] = ''

                load_balancers['nodes'] = []
                for item in nodes:
                    node = item._asdict()
                    if node['enabled'] == 1:
                        node['condition'] = 'ENABLED'
                    else:
                        node['condition'] = 'DISABLED'
                    del node['enabled']
                    node['port'] = str(node['port'])
                    node['id'] = str(node['id'])
                    load_balancers['nodes'].append(node)

            session.rollback()
            response.status = 200
            return load_balancers

    @wsme_pecan.wsexpose(LBResp, body=LBPost, status_code=202)
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
        if body.nodes == Unset or not len(body.nodes):
            raise ClientSideError(
                'At least one backend node needs to be supplied'
            )
        for node in body.nodes:
            if node.address == Unset:
                raise ClientSideError(
                    'A supplied node has no address'
                )
            if node.port == Unset:
                raise ClientSideError(
                    'Node {0} is missing a port'.format(node.address)
                )
            try:
                socket.inet_aton(node.address)
            except socket.error:
                raise ClientSideError(
                    'IP Address {0} not valid'.format(node.address)
                )
        with db_session() as session:
            lblimit = session.query(Limits.value).\
                filter(Limits.name == 'maxLoadBalancers').scalar()
            nodelimit = session.query(Limits.value).\
                filter(Limits.name == 'maxNodesPerLoadBalancer').scalar()
            namelimit = session.query(Limits.value).\
                filter(Limits.name == 'maxLoadBalancerNameLength').scalar()
            count = session.query(LoadBalancer).\
                filter(LoadBalancer.tenantid == tenant_id).\
                filter(LoadBalancer.status != 'DELETED').count()

            if len(body.name) > namelimit:
                session.rollback()
                raise ClientSideError(
                    'Length of Load Balancer name too long'
                )
            # TODO: this should probably be a 413, not sure how to do that yet
            if count >= lblimit:
                session.rollback()
                raise OverLimit(
                    'Account has hit limit of {0} Load Balancers'.
                    format(lblimit)
                )
            if len(body.nodes) > nodelimit:
                session.rollback()
                raise OverLimit(
                    'Too many backend nodes supplied (limit is {0}'.
                    format(nodelimit)
                )

            device = None
            old_lb = None
            # if we don't have an id then we want to create a new lb
            lb = LoadBalancer()
            if body.virtualIps == Unset:
                # find free device
                # lock with "for update" so multiple APIs don't grab the same
                # LB
                device = session.query(Device).\
                    filter(~Device.id.in_(
                        session.query(loadbalancers_devices.c.device)
                    )).\
                    filter(Device.status == "OFFLINE").\
                    with_lockmode('update').\
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
                    session.rollback()
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
                        session.rollback()
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
                        session.rollback()
                        # Error here, can have only one TCP
                        raise ClientSideError(
                            'Only one TCP load balancer allowed per device'
                        )

            if device is None:
                session.rollback()
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
                    enabled=enabled, status='ONLINE', weight=1
                )
                session.add(out_node)

            # now save the loadbalancer_id to the device and switch its status
            # to online
            device.status = "ONLINE"

            session.flush()

            try:
                return_data = LBResp()
                return_data.id = str(lb.id)
                return_data.name = lb.name
                return_data.protocol = lb.protocol
                return_data.port = str(lb.port)
                return_data.algorithm = lb.algorithm
                return_data.status = lb.status
                return_data.created = lb.created
                return_data.updated = lb.updated
                vip_resp = LBVipResp(
                    address=device.floatingIpAddr, id=str(device.id),
                    type='PUBLIC', ipVersion='IPV4'
                )
                return_data.virtualIps = [vip_resp]
                return_data.nodes = []
                for node in body.nodes:
                    out_node = LBRespNode(
                        port=str(node.port), address=node.address,
                        condition=node.condition
                    )
                    return_data.nodes.append(out_node)
                session.commit()
                # trigger gearman client to create new lb
                result = submit_job(
                    'UPDATE', device.name, device.id, lb.id
                )
                # do something with result
                if result:
                    pass
                return return_data
            except:
                logger = logging.getLogger(__name__)
                logger.exception('Error communicating with load balancer pool')
                errstr = 'Error communicating with load balancer pool'
                session.rollback()
                raise ClientSideError(errstr)

    @wsme_pecan.wsexpose(None, body=LBPut, status_code=202)
    def put(self, body=None):
        if not self.lbid:
            raise ClientSideError('Load Balancer ID is required')

        tenant_id = get_limited_to_project(request.headers)
        with db_session() as session:
            # grab the lb
            lb = session.query(LoadBalancer).\
                filter(LoadBalancer.id == self.lbid).\
                filter(LoadBalancer.tenantid == tenant_id).\
                filter(LoadBalancer.status != 'DELETED').first()

            if lb is None:
                session.rollback()
                raise ClientSideError('Load Balancer ID is not valid')

            if body.name != Unset:
                namelimit = session.query(Limits.value).\
                    filter(Limits.name == 'maxLoadBalancerNameLength').scalar()
                if len(body.name) > namelimit:
                    session.rollback()
                    raise ClientSideError(
                        'Length of Load Balancer name too long'
                    )
                lb.name = body.name

            if body.algorithm != Unset:
                lb.algorithm = body.algorithm

            lb.status = 'PENDING_UPDATE'
            device = session.query(
                Device.id, Device.name
            ).join(LoadBalancer.devices).\
                filter(LoadBalancer.id == self.lbid).\
                first()
            session.commit()
            submit_job(
                'UPDATE', device.name, device.id, lb.id
            )
            return ''

    @wsme_pecan.wsexpose(None)
    def delete(self):
        """Remove a load balancer from the account.

        :param load_balancer_id: id of lb

        Urls:
           DELETE   /loadbalancers/{load_balancer_id}

        Notes:
           curl -i -H "Accept: application/json" -X DELETE
           http://dev.server:8080/loadbalancers/1

        Returns: None
        """
        load_balancer_id = self.lbid
        tenant_id = get_limited_to_project(request.headers)
        # grab the lb
        with db_session() as session:
            lb = session.query(LoadBalancer).\
                filter(LoadBalancer.id == load_balancer_id).\
                filter(LoadBalancer.tenantid == tenant_id).\
                filter(LoadBalancer.status != 'DELETED').first()

            if lb is None:
                session.rollback()
                raise ClientSideError("Load Balancer ID is not valid")
            try:
                session.query(Node).\
                    filter(Node.lbid == load_balancer_id).delete()
                lb.status = 'PENDING_DELETE'
                device = session.query(
                    Device.id, Device.name
                ).join(LoadBalancer.devices).\
                    filter(LoadBalancer.id == load_balancer_id).\
                    first()
                session.flush()
                session.commit()
                submit_job(
                    'DELETE', device.name, device.id, lb.id
                )
                response.status = 202
                return None
            except:
                session.rollback()
                logger = logging.getLogger(__name__)
                logger.exception('Error communicating with load balancer pool')
                raise RuntimeError(
                    "Error communication with load balancer pool"
                )

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
            if remainder[0] == 'logs':
                return LogsController(lbid), remainder[1:]

        # Kludgy fix for PUT since WSME doesn't like IDs on the path
        elif lbid:
            return LoadBalancersController(lbid), remainder
        abort(404)
