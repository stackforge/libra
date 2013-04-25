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

import gearman.errors

import json
import socket
import time
# pecan imports
from pecan import expose, redirect, abort, response
from pecan.rest import RestController
# other controllers
from nodes import NodesController
from health_monitor import HealthMonitorController
from session_persistence import SessionPersistenceController
from connection_throttle import ConnectionThrottleController
# default response objects
from libra.api.model.responses import Responses
# models
from libra.api.model.lbaas import Device, LoadBalancer, Node, session
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
    def get(self, load_balancer_id = None):
        """Fetches a list of load balancers or the details of one balancer if
        load_balancer_id is not empty.

        :param load_balancer_id: id of lb we want to get, if none it returns a list of all

        Url:
           GET /loadbalancers
           List all load balancers configured for the account.

        Url:
           GET /loadbalancers/{load_balancer_id}
           List details of the specified load balancer.

        Returns: dict
        """
        # have not implimented the keystone middleware so we don't know the tenantid
        tenant_id = 80074562416143

        # if we don't have an id then we want a list of them own by this tenent
        if not load_balancer_id:
            #return Responses.LoadBalancers.get
            load_balancers = {'loadBalancers': session.query(
                LoadBalancer.name, LoadBalancer.id, LoadBalancer.protocol,
                LoadBalancer.port, LoadBalancer.algorithm,
				LoadBalancer.status, LoadBalancer.created, LoadBalancer.updated
            ).filter_by(tenantid=tenant_id).all()}
        else:
            #return Responses.LoadBalancers.detail
            load_balancers = session.query(LoadBalancer).\
                filter_by(tenantid=tenant_id,id=load_balancer_id).first()

        if load_balancers == None:
            return Responses.not_found
        else:
            return load_balancers

    @expose('json')
    def post(self, load_balancer_id = None, **kwargs):
        """Accepts edit if load_balancer_id isn't blank or create load balancer posts.

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
        # have not implimented the keystone middleware so we don't know the tenantid
        tenant_id = 80074562416143

        # load input
        data = json.loads(kwargs['data'])
        # TODO validate input data

        # if we don't have an id then we want to create a new lb
        if not load_balancer_id:
            lb = LoadBalancer()

            # find free device
            device = Device.find_free_device()

            if device == None:
                response.status = 503
                return Responses.service_unavailable

            lb.device = device.id
            lb.tenantid = tenant_id

            lb.update_from_json(data)

            # write to database
            session.add(lb)
            session.flush()
            #refresh the lb record so we get the id back
            session.refresh(lb)

            # now save the loadbalancer_id to the device and switch its status to online
            device.loadbalancers = lb.id
            device.status = "ONLINE"

        else:
            # grab the lb
            lb = session.query(LoadBalancer)\
                .filter_by(id=load_balancer_id).first()

            if lb == None:
                response.status = 400
                return Responses.not_found

            lb.update_from_json(data)

        try:
            session.flush()

            # trigger gearman client to create new lb
            result = gearman_client.submit_job('UPDATE',lb.output_to_json() )

            response.status = 200
            return self.get()
        except:
            response.status = 503
            return Responses.service_unavailable

    @expose()
    def delete(self,load_balancer_id):
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

        if lb == None:
            response.status = 400
            return Responses.not_found

        try:
            session.flush()

            # trigger gearman client to create new lb
            result = gearman_client.submit_job('DELETE',lb.output_to_json() )

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
