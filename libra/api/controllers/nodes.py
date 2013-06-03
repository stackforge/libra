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

from pecan import expose, response, request
from pecan.rest import RestController
import wsmeext.pecan as wsme_pecan
from wsme.exc import ClientSideError
#default response objects
from libra.api.model.lbaas import LoadBalancer, Node, session, Limits, Device
from libra.api.acl import get_limited_to_project
from libra.api.model.validators import LBNodeResp, LBNodePost, NodeResp
from libra.api.library.gearman_client import submit_job


class NodesController(RestController):
    """Functions for /loadbalancers/{load_balancer_id}/nodes/* routing"""
    def __init__(self, lbid):
        self.lbid = lbid

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
                faultcode='Client',
                faultstring='Load Balancer ID not supplied'
            )

        if not node_id:
            nodes = session.query(
                Node.id, Node.address, Node.port, Node.status, Node.enabled
            ).join(LoadBalancer.nodes).\
                filter(LoadBalancer.tenantid == tenant_id).\
                filter(LoadBalancer.id == self.lbid).\
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
            node_response = session.query(
                Node.id, Node.address, Node.port, Node.status, Node.enabled
            ).join(LoadBalancer.nodes).\
                filter(LoadBalancer.tenantid == tenant_id).\
                filter(LoadBalancer.id == self.lbid).\
                filter(Node.id == node_id).\
                first()

        if node_response is None:
            session.rollback()
            response.status = 400
            return dict(faultcode='Client', faultstring='node not found')
        else:
            session.commit()
            response.status = 200
            return node_response

    @wsme_pecan.wsexpose(LBNodeResp, body=LBNodePost, status=202)
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
        # TODO: gearman message
        tenant_id = get_limited_to_project(request.headers)
        if self.lbid is None:
            raise ClientSideError('Load Balancer ID has not been supplied')

        if not len(body.nodes):
            raise ClientSideError('No nodes have been supplied')

        load_balancer = session.query(LoadBalancer).\
            filter(LoadBalancer.tenantid == tenant_id).\
            filter(LoadBalancer.id == self.lbid).\
            first()
        if load_balancer is None:
            raise ClientSideError('Load Balancer not found')

        load_balancer.status = 'PENDING_UPDATE'
        # check if we are over limit
        nodelimit = session.query(Limits.value).\
            filter(Limits.name == 'maxNodesPerLoadBalancer').scalar()
        nodecount = session.query(Node).\
            filter(Node.lbid == self.lbid).count()

        if (nodecount + len(body.nodes)) >= nodelimit:
            raise ClientSideError(
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
                enabled=enabled, status='ONLINE', weight=0
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

    @expose('json')
    def delete(self, node_id):
        """Remove a node from the load balancer.

        :param load_balancer_id: id of lb
        :param node_id: id of node

        Url:
           DELETE /loadbalancers/{load_balancer_id}/nodes/{node_id}

        Returns: None
        """
        # TODO: gearman message
        tenant_id = get_limited_to_project(request.headers)
        if self.lbid is None:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring='Load Balancer ID has not been supplied'
            )

        tenant_id = get_limited_to_project(request.headers)
        load_balancer = session.query(LoadBalancer).\
            filter(LoadBalancer.tenantid == tenant_id).\
            filter(LoadBalancer.id == self.lbid).\
            first()
        if load_balancer is None:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Load Balancer not found"
            )
        load_balancer.status = 'PENDING_UPDATE'
        nodecount = session.query(Node).\
            filter(Node.lbid == self.lbid).count()
        # Can't delete the last LB
        if nodecount <= 1:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Load Balancer not found"
            )
        node = session.query(Node).\
            filter(Node.lbid == self.lbid).\
            filter(Node.id == node_id).\
            first()
        if not node:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Node not found in supplied Load Balancer"
            )
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

        return None
