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

# pecan imports
import logging
from pecan import expose, response, abort
from pecan.rest import RestController
import wsmeext.pecan as wsme_pecan
from wsme.exc import ClientSideError
from libra.admin_api.model.validators import DeviceResp, DevicePost, DevicePut
from libra.admin_api.model.lbaas import LoadBalancer, Device, session
from libra.admin_api.model.lbaas import loadbalancers_devices


class DevicesController(RestController):
    def __init__(self, devid=None):
        #  Required for PUT requests. See _lookup() below
        self.devid = devid

    @expose('json')
    def get(self, device_id=None, marker=None, limit=None):
        """
        Gets either a list of all devices or a single device details.
        device_id is supplied if we are getting details of a single device
        marker and limit are used to paginate when device_id is not
        supplied.  Currently this just supplies "LIMIT marker, limit" to
        MySQL which is fine.

        :param device_id: id of device (unless getall)
        Url:
            GET /devices
            List all configured devices
        Url:
            GET /devices/{device_id}
            List details of a particular device
        Returns: dict
        """

        # if we don't have an id then we want a list of all devices
        if not device_id:
            #  return all devices
            device = {'devices': []}

            if marker is None:
                marker = 0
            if limit is None:
                limit = 100

            devices = session.query(
                Device.id, Device.az, Device.updated, Device.created,
                Device.status, Device.publicIpAddr, Device.name,
                Device.type, Device.floatingIpAddr).offset(marker).limit(limit)

            for item in devices:
                dev = item._asdict()
                dev['loadBalancers'] = []
                if dev['status'] != "OFFLINE":
                    #  Find loadbalancers using device
                    lbids = session.query(
                        loadbalancers_devices.c.loadbalancer).\
                        filter(loadbalancers_devices.c.device == dev['id']).\
                        all()

                    lblist = [i[0] for i in lbids]
                    lbs = session.query(
                        LoadBalancer.id, LoadBalancer.tenantid).\
                        filter(LoadBalancer.id.in_(lblist)).all()

                    if lbs:
                        for item in lbs:
                            lb = item._asdict()
                            lb['hpcs_tenantid'] = lb['tenantid']
                            del(lb['tenantid'])
                            dev['loadBalancers'].append(lb)

                device['devices'].append(dev)

        elif device_id == 'usage':
            return self.usage()
        else:
            #  return device detail
            device = session.query(
                Device.id, Device.az, Device.updated, Device.created,
                Device.status, Device.publicIpAddr, Device.name,
                Device.type, Device.floatingIpAddr
            ).filter(Device.id == device_id).first()

            if not device:
                response.status = 404
                session.rollback()
                return dict(
                    status=404,
                    message="device id " + device_id + "not found"
                )

            device = device._asdict()
            device['loadBalancers'] = []

            if device['status'] != "OFFLINE":
                lbids = session.query(
                    loadbalancers_devices.c.loadbalancer).\
                    filter(loadbalancers_devices.c.device == device['id']).\
                    all()

                lblist = [i[0] for i in lbids]
                lbs = session.query(
                    LoadBalancer.id, LoadBalancer.tenantid).\
                    filter(LoadBalancer.id.in_(lblist)).all()

                if lbs:
                    for item in lbs:
                        lb = item._asdict()
                        device['loadBalancers'].append(lb)

        session.commit()
        response.status = 200
        return device

    @wsme_pecan.wsexpose(DeviceResp, body=DevicePost)
    def post(self, body=None):
        """ Creates a new device entry in devices table.
        :param None
        Url:
            POST /devices
        JSON Request Body
        {
            "name":"device name",
            "publicIpAddr":"15.x.x.x",
            "floatingIpAddr":"15.x.x.x",
            "az":2,
            "type":"type descr"
        }

        Returns: dict
        {
            "status": "OFFLINE",
            "updated": "2013-06-06T10:17:19",
            "name": "device name",
            "created": "2013-06-06T10:17:19",
            "loadBalancers": [],
            "floatingIpAddr": "192.1678.98.99",
            "publicIpAddr": "192.1678.98.99",
            "az": 2,
            "type": "type descr",
            "id": 67
        }
        """

        #  Get a new device object
        device = Device()
        device.name = body.name
        device.publicIpAddr = body.publicIpAddr
        device.floatingIpAddr = body.floatingIpAddr
        device.az = body.az
        device.type = body.type
        device.status = 'OFFLINE'
        device.created = None

        # write to database
        session.add(device)
        session.flush()

        #refresh the device record so we get the id back
        session.refresh(device)

        try:
            return_data = DeviceResp()
            return_data.id = device.id
            return_data.name = device.name
            return_data.floatingIpAddr = device.floatingIpAddr
            return_data.publicIpAddr = device.publicIpAddr
            return_data.az = device.az
            return_data.type = device.type
            return_data.created = device.created
            return_data.updated = device.updated
            return_data.status = device.status
            return_data.loadBalancers = []
            session.commit()
            return return_data
        except:
            logger = logging.getLogger(__name__)
            logger.exception('Error communicating with load balancer pool')
            errstr = 'Error communicating with load balancer pool'
            session.rollback()
            raise ClientSideError(errstr)

    @wsme_pecan.wsexpose(None, body=DevicePut)
    def put(self, body=None):
        """ Updates a device entry in devices table with new status.
            Also, updates status of loadbalancers using this device
            with ERROR or ACTIVE and the errmsg field
        :param - NOTE the _lookup() hack used to get the device id
        Url:
            PUT /devices/<device ID>
        JSON Request Body
        {
            "status": <ERROR | ONLINE>
            "statusDescription": "Error Description"
        }

        Returns: None
        """

        if not self.devid:
            raise ClientSideError('Device ID is required')

        device = session.query(Device).\
            filter(Device.id == self.devid).first()

        if not device:
            raise ClientSideError('Device ID is not valid')

        device.status = body.status
        session.flush()

        lb_status = 'ACTIVE' if body.status == 'ONLINE' else body.status
        lb_descr = body.statusDescription

        #  Now find LB's associated with this Device and update their status
        lbs = session.query(
            loadbalancers_devices.c.loadbalancer).\
            filter(loadbalancers_devices.c.device == self.devid).\
            all()

        for lb in lbs:
            session.query(LoadBalancer).\
                filter(LoadBalancer.id == lb[0]).\
                update({"status": lb_status, "errmsg": lb_descr},
                       synchronize_session='fetch')

            session.flush()

        session.commit()
        return

    @expose('json')
    def delete(self, device_id):
        """ Deletes a given device
        :param device_id: id of device to delete
        Urls:
           DELETE   /devices/{device_id}
        Returns: None
        """
        # check for the device
        device = session.query(Device.id).\
            filter(Device.id == device_id).first()

        if device is None:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Device ID is not valid"
            )

        # Is the device is attached to a LB
        lb = session.query(
            loadbalancers_devices.c.loadbalancer).\
            filter(loadbalancers_devices.c.device == device_id).\
            all()

        if lb:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Device belongs to a loadbalancer"
            )
        try:
            session.query(Device).filter(Device.id == device_id).delete()
            session.flush()
            session.commit()
            return None
        except:
            logger = logging.getLogger(__name__)
            logger.exception('Error deleting device from pool')
            response.status = 500
            return dict(
                faultcode="Server",
                faultstring="Error deleting device from pool"
            )

    # Kludge to get to here because Pecan has a hard time with URL params
    # and paths
    def usage(self):
        """Reports the device usage statistics for total, taken, and free
            :param None
            Url:
                GET /devices/usage
            Returns: dict
        """
        total = session.query(Device).count()
        free = session.query(Device).filter(Device.status == 'OFFLINE').\
            count()
        session.commit()
        response.status = 200

        return dict(
            total=total,
            free=free,
            taken=total - free
        )

    @expose('json')
    def _lookup(self, devid, *remainder):
        """Routes more complex url mapping for PUT
        Raises: 404
        """
        #  Kludgy fix for PUT since WSME doesn't like IDs on the path
        if devid:
            return DevicesController(devid), remainder
        abort(404)
