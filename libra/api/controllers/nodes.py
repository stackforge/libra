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

import socket
from pecan import expose, response, request, abort
from pecan.rest import RestController
import wsmeext.pecan as wsme_pecan
from wsme.exc import ClientSideError
from wsme import Unset
#default response objects
from libra.api.model.lbaas import LoadBalancer, Node, db_session, Limits
from libra.api.model.lbaas import Device
from libra.api.acl import get_limited_to_project
from libra.api.model.validators import LBNodeResp, LBNodePost, NodeResp
from libra.api.model.validators import LBNodePut
from libra.api.library.gearman_client import submit_job
from libra.api.library.exp import OverLimit


class NodesController(RestController):
    """Functions for /loadbalancers/{load_balancer_id}/nodes/* routing"""
    def __init__(self, lbid, nodeid=None):
        self.lbid = lbid
        self.nodeid = nodeid

    @expose('json')
    def get(self, node_id=None):
        """List node(s) configured for the load balancer OR if
        node_id == None .. Retrieve the configuration of node {node_id} of
        loadbalancer {load_balancer_id}.
        :param load_balancer_id: id of lb
        :param node_id: id of node (optional)

        Urls:
           GET /loadbalancers/{load_balancer_id}/nodes
           GET /loadbalancers/{load_balancer_id}/nodes/{node_id}

        Returns: dict
        """
        tenant_id = get_limited_to_project(request.headers)

        if not self.lbid:
            response.status = 400
            return dict(
                message='Bad Request',
                details='Load Balancer ID not supplied'
            )
        with db_session() as session:
            if not node_id:
                nodes = session.query(
                    Node.id, Node.address, Node.port, Node.status, Node.enabled
                ).join(LoadBalancer.nodes).\
                    filter(LoadBalancer.tenantid == tenant_id).\
                    filter(LoadBalancer.id == self.lbid).\
                    filter(LoadBalancer.status != 'DELETED').\
                    all()

                node_response = {'nodes': []}
                for item in nodes:
                    node = item._asdict()
                    if node['enabled'] == 1:
                        node['condition'] = 'ENABLED'
                    else:
                        node['condition'] = 'DISABLED'
                    del node['enabled']
                    node_response['nodes'].append(node)

            else:
                node = session.query(
                    Node.id, Node.address, Node.port, Node.status, Node.enabled
                ).join(LoadBalancer.nodes).\
                    filter(LoadBalancer.tenantid == tenant_id).\
                    filter(LoadBalancer.id == self.lbid).\
                    filter(Node.id == node_id).\
                    first()

                if node is None:
                    session.rollback()
                    response.status = 400
                    return dict(
                        message='Bad Request', details='node not found'
                    )

                node_response = node._asdict()
                if node_response['enabled'] == 1:
                    node_response['condition'] = 'ENABLED'
                else:
                    node_response['condition'] = 'DISABLED'
                del node_response['enabled']

            session.commit()
            response.status = 200
            return node_response

    @wsme_pecan.wsexpose(LBNodeResp, body=LBNodePost, status_code=202)
    def post(self, body=None):
        """Adds a new node to the load balancer OR Modify the configuration
        of a node on the load balancer.

        :param load_balancer_id: id of lb
        :param node_id: id of node (optional) when missing a new node is added.
        :param *args: holds the posted json or xml data

        Urls:
           POST	 /loadbalancers/{load_balancer_id}/nodes
           PUT	 /loadbalancers/{load_balancer_id}/nodes/{node_id}

        Returns: dict of the full list of nodes or the details of the single
        node
        """
        tenant_id = get_limited_to_project(request.headers)
        if self.lbid is None:
            raise ClientSideError('Load Balancer ID has not been supplied')

        if body.nodes == Unset or not len(body.nodes):
            raise ClientSideError('No nodes have been supplied')

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
            load_balancer = session.query(LoadBalancer).\
                filter(LoadBalancer.tenantid == tenant_id).\
                filter(LoadBalancer.id == self.lbid).\
                filter(LoadBalancer.status != 'DELETED').\
                first()
            if load_balancer is None:
                session.rollback()
                raise ClientSideError('Load Balancer not found')

            load_balancer.status = 'PENDING_UPDATE'
            # check if we are over limit
            nodelimit = session.query(Limits.value).\
                filter(Limits.name == 'maxNodesPerLoadBalancer').scalar()
            nodecount = session.query(Node).\
                filter(Node.lbid == self.lbid).count()

            if (nodecount + len(body.nodes)) > nodelimit:
                session.rollback()
                raise OverLimit(
                    'Command would exceed Load Balancer node limit'
                )
            return_data = LBNodeResp()
            return_data.nodes = []
            for node in body.nodes:
                if node.condition == 'DISABLED':
                    enabled = 0
                else:
                    enabled = 1
                new_node = Node(
                    lbid=self.lbid, port=node.port, address=node.address,
                    enabled=enabled, status='ONLINE', weight=1
                )
                session.add(new_node)
                session.flush()
                if new_node.enabled:
                    condition = 'ENABLED'
                else:
                    condition = 'DISABLED'
                return_data.nodes.append(
                    NodeResp(
                        id=new_node.id, port=new_node.port,
                        address=new_node.address, condition=condition,
                        status='ONLINE'
                    )
                )
            device = session.query(
                Device.id, Device.name
            ).join(LoadBalancer.devices).\
                filter(LoadBalancer.id == self.lbid).\
                first()
            session.commit()
            submit_job(
                'UPDATE', device.name, device.id, self.lbid
            )
            return return_data

    @wsme_pecan.wsexpose(None, body=LBNodePut, status_code=202)
    def put(self, body=None):
        if not self.lbid:
            raise ClientSideError('Load Balancer ID has not been supplied')
        if not self.nodeid:
            raise ClientSideError('Node ID has not been supplied')

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

            node = session.query(Node).\
                filter(Node.lbid == self.lbid).\
                filter(Node.id == self.nodeid).first()

            if node is None:
                session.rollback()
                raise ClientSideError('Node ID is not valid')

            if body.condition != Unset:
                if body.condition == 'DISABLED':
                    node.enabled = 0
                else:
                    node.enabled = 1

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
        """Remove a node from the load balancer.

        :param load_balancer_id: id of lb
        :param node_id: id of node

        Url:
           DELETE /loadbalancers/{load_balancer_id}/nodes/{node_id}

        Returns: None
        """
        node_id = self.nodeid
        tenant_id = get_limited_to_project(request.headers)
        if self.lbid is None:
            response.status = 400
            return dict(
                message="Bad Request",
                details='Load Balancer ID has not been supplied'
            )

        tenant_id = get_limited_to_project(request.headers)
        with db_session() as session:
            load_balancer = session.query(LoadBalancer).\
                filter(LoadBalancer.tenantid == tenant_id).\
                filter(LoadBalancer.id == self.lbid).\
                filter(LoadBalancer.status != 'DELETED').\
                first()
            if load_balancer is None:
                session.rollback()
                ClientSideError("Load Balancer not found")
            load_balancer.status = 'PENDING_UPDATE'
            nodecount = session.query(Node).\
                filter(Node.lbid == self.lbid).count()
            # Can't delete the last LB
            if nodecount <= 1:
                session.rollback()
                ClientSideError(
                    "Cannot delete the last node in a load balancer"
                )
            node = session.query(Node).\
                filter(Node.lbid == self.lbid).\
                filter(Node.id == node_id).\
                first()
            if not node:
                session.rollback()
                ClientSideError("Node not found in supplied Load Balancer")
            session.delete(node)
            device = session.query(
                Device.id, Device.name
            ).join(LoadBalancer.devices).\
                filter(LoadBalancer.id == self.lbid).\
                first()
            session.commit()
            submit_job(
                'UPDATE', device.name, device.id, self.lbid
            )
            response.status = 202
            return None

    @expose('json')
    def _lookup(self, nodeid, *remainder):
        """Routes more complex url mapping.

        Raises: 404
        """
        # Kludgy fix for PUT since WSME doesn't like IDs on the path
        if nodeid:
            return NodesController(self.lbid, nodeid), remainder
        abort(404)
