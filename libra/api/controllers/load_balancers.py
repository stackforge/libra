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

#import gearman.errors

# pecan imports
from pecan import expose, abort, response
from pecan.rest import RestController
import wsmeext.pecan as wsme_pecan
from wsme.exc import ClientSideError
# other controllers
from nodes import NodesController
from health_monitor import HealthMonitorController
from session_persistence import SessionPersistenceController
from connection_throttle import ConnectionThrottleController
#from sqlalchemy.orm import aliased
# default response objects
from libra.api.model.responses import Responses
# models
from libra.api.model.lbaas import LoadBalancer, Device, Node, session
from libra.api.model.lbaas import loadbalancers_devices
from libra.api.model.validators import LBPost, LBResp, LBVipResp, LBNode
from libra.api.library.gearman_client import gearman_client


class LoadBalancersController(RestController):
    """functions for /loadbalancer routing"""
    loadbalancer_status = (
        'ACTIVE',
        'BUILD',
        'PENDING_UPDATE',
        'PENDING_DELETE',
        'DELETED',
        'SUSPENDED',
        'ERROR'
    )

    """nodes subclass linking
    controller class for urls that look like
    /loadbalancers/{loadBalancerId}/nodes/*
    """
    nodes = NodesController()

    """healthmonitor instance
    controller class for urls that start with
    /loadbalancers/{loadBalancerId}/healthmonitor/*
    """
    healthmonitor = HealthMonitorController()

    """healthmonitor instance
    controller class for urls that start with
    /loadbalancers/{loadBalancerId}/sessionpersistence/*
    """
    sessionpersistence = SessionPersistenceController()

    """connectionthrottle instance
    controller class for urls that start with
    /loadbalancers/{loadBalancerId}/connectionthrottle/*
    """
    connectionthrottle = ConnectionThrottleController()

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
        # have not implimented the keystone middleware so we don't know the
        # tenantid
        tenant_id = 80074562416143

        # if we don't have an id then we want a list of them own by this tenent
        if not load_balancer_id:
            #return Responses.LoadBalancers.get
            load_balancers = {'loadBalancers': session.query(
                LoadBalancer.name, LoadBalancer.id, LoadBalancer.protocol,
                LoadBalancer.port, LoadBalancer.algorithm,
                LoadBalancer.status, LoadBalancer.created,
                LoadBalancer.updated
            ).filter_by(tenantid=tenant_id).all()}
        else:
            #return Responses.LoadBalancers.detail
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
                return dict(status=400, message="load balancer not found")

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

    @wsme_pecan.wsexpose(LBResp, int, body=LBPost, status=202)
    def post(self, load_balancer_id=None, body=None):
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
        # have not implimented the keystone middleware so we don't know the
        # tenantid
        tenant_id = 80074562416143

        # TODO: check if tenant is overlimit (return a 413 for that)
        # TODO: check if we have been supplied with too many nodes
        device = None
        # if we don't have an id then we want to create a new lb
        if not load_balancer_id:
            lb = LoadBalancer()

            # find free device
            device = session.query(Device).\
                filter(~Device.id.in_(
                    session.query(loadbalancers_devices.c.device)
                )).\
                filter(Device.status == "OFFLINE").\
                first()

            if device is None:
                response.status = 503
                return Responses.service_unavailable

            lb.tenantid = tenant_id
            lb.name = body.name
            if body.protocol and body.protocol.lower() == 'HTTP':
                lb.protocol = 'HTTP'
            else:
                lb.protocol = 'TCP'

            if body.port:
                lb.port = body['port']
            else:
                lb.port = 80

            lb.status = 'BUILD'

            if body.algorithm:
                lb.algorithm = body.algorithm.upper()
            else:
                lb.algorithm = 'ROUND_ROBIN'

            lb.devices.device = device.id

            # write to database
            session.add(lb)
            session.flush()
            #refresh the lb record so we get the id back
            session.refresh(lb)

            # now save the loadbalancer_id to the device and switch its status
            # to online
            device.status = "ONLINE"

        else:
            # TODO: not tested this bit yet
            # grab the lb
            lb = session.query(LoadBalancer)\
                .filter_by(id=load_balancer_id).first()

            if lb is None:
                response.status = 400
                return Responses.not_found

        session.flush()
            # TODO: write nodes to table too

        job_data = {
            'hpcs_action': 'UPDATE',
            'loadbalancers': []
        }
        for node in body.nodes:
            node_data = {'port': node.port, 'address': node.address}
            if node.condition:
                node_data['condition'] = node.condition
            job_data['loadbalancers'].append(node_data)
        try:
            # trigger gearman client to create new lb
            result = gearman_client.submit_job(device.name, job_data, background=True)
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
            return_data.nodes=[]
            for node in body.nodes:
                out_node = LBNode(
                    port=node.port, address=node.address,
                    condition=node.condition
                )
                return_data.nodes.append(out_node)
            # TODO: session.commit()
            return return_data
        except:
            errstr = 'Error communicating with load balancer pool'
            session.rollback()
            raise ClientSideError(errstr)

    @expose()
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
        # grab the lb
        lb = session.query(LoadBalancer)\
            .filter_by(id=load_balancer_id).first()

        if lb is None:
            response.status = 400
            return Responses.not_found

        try:
            session.flush()

            # trigger gearman client to create new lb
            result = gearman_client.submit_job('DELETE', lb.output_to_json())

            if result:
                pass

            response.status = 200

            session.delete(lb)
            session.commit()

            return self.get()
        except:
            response.status = 503
            return Responses.service_unavailable

    def virtualips(self, load_balancer_id):
        """Returns a list of virtual ips attached to a specific Load Balancer.

        :param load_balancer_id: id of lb

        Url:
           GET /loadbalancers/{load_balancer_id}/virtualips

        Returns: dict
        """
        return Responses.LoadBalancers.virtualips

    def usage(self, load_balancer_id):
        """List current and historical usage.

        :param load_balancer_id: id of lb

        Url:
           GET /loadbalancers/{load_balancer_id}/usage

        Returns: dict
        """
        response.status = 201
        return Responses.LoadBalancers.usage

    @expose('json')
    def _lookup(self, primary_key, *remainder):
        """Routes more complex url mapping.

        :param primary_key: value to look up or pass
        :param *remainder: remaining args

        Raises: 404
        """
        #student = get_student_by_primary_key(primary_key)
        #if student:
        #    return StudentController(student), remainder
        #else:
        abort(404)
