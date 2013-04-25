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

from pecan import expose, redirect, abort, response
from pecan.rest import RestController
#default response objects
from api.model.lbaas import Device, LoadBalancer, Node, Version, session
from api.model.responses import Responses

class NodesController(RestController):   
    """Functions for /loadbalancers/{load_balancer_id}/nodes/* routing"""

    @expose('json')
    def get(self, load_balancer_id, node_id = None ):
        """List node(s) configured for the load balancer OR if node_id == None .. Retrieve
        the configuration of node {node_id} of loadbalancer {load_balancer_id}.

        :param load_balancer_id: id of lb
        :param node_id: id of node (optional)

        Urls:
           GET /loadbalancers/{load_balancer_id}/nodes 
           GET /loadbalancers/{load_balancer_id}/nodes/{node_id} 

        Returns: dict
        """
        response.status = 201
        return Responses.LoadBalancers.Nodes.get

    @expose('json')
    def post(self, load_balancer_id, node_id = None, *args):
        """Adds a new node to the load balancer OR Modify the configuration of a
        node on the load balancer.

        :param load_balancer_id: id of lb
        :param node_id: id of node (optional) when missing a new node is added.
        :param *args: holds the posted json or xml data

        Urls:
           POST	 /loadbalancers/{load_balancer_id}/nodes
           PUT	 /loadbalancers/{load_balancer_id}/nodes/{node_id}

        Returns: dict of the full list of nodes or the details of the single node
        """
        response.status = 201
        return Responses.LoadBalancers.Nodes.get

    @expose()
    def delete(self, load_balancer_id, node_id):
        """Remove a node from the load balancer.

        :param load_balancer_id: id of lb
        :param node_id: id of node

        Url:
           DELETE /loadbalancers/{load_balancer_id}/nodes/{node_id}

        Returns: None
        """
        response.status = 201
