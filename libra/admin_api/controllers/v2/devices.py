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
from libra.admin_api.library.rebuild import rebuild_device
from libra.common.api.lbaas import LoadBalancer, Device, db_session
from libra.common.api.lbaas import loadbalancers_devices, Vip
from libra.openstack.common import log
from libra.admin_api.stats.stats_gearman import GearJobs
from libra.admin_api.acl import tenant_is_admin, tenant_is_user

LOG = log.getLogger(__name__)


class DevicesController(RestController):
    @expose('json')
    def get(
            self, device_id=None, status=None, name=None, ip=None, vip=None
    ):
        """
        Gets either a list of all devices or a single device details.

        :param device_id: id of device (unless getall)
        Url:
            GET /devices
            List all configured devices
        Url:
            GET /devices/{device_id}
            List details of a particular device
        Returns: dict
        """

        # Work around routing issue in Pecan, doesn't work as a separate class
        # due to this get accepting more than one parameter
        if status == 'discover':
            return self.discover(device_id)

        if not tenant_is_user(request.headers):
            response.status = 401
            return dict(
                faultcode="Client",
                faultstring="Client not authorized to access this function"
            )

        with db_session() as session:
            # if we don't have an id then we want a list of all devices
            if not device_id:
                #  return all devices
                device = {'devices': []}

                devices = session.query(
                    Device.id, Device.az, Device.updated, Device.created,
                    Device.status, Device.name, Device.type,
                    Device.floatingIpAddr.label('ip'), Vip.id.label('vipid'),
                    Vip.ip.label('vip')).outerjoin(Device.vip)

                if vip is not None:
                    # Search devices by vip, should only return one
                    vip_num = int(ipaddress.IPv4Address(unicode(vip)))
                    devices = devices.filter(Vip.ip == vip_num)

                if status is not None:
                    # Search devices by status
                    status = status.upper()
                    if status not in ['OFFLINE', 'ONLINE', 'ERROR']:
                        # Invalid status specified
                        response.status = 400
                        return dict(
                            faultcode="Client",
                            faultstring="Invalid status: " + status
                        )
                    devices = devices.filter(Device.status == status)
                if name is not None:
                    # Search devices by name, should only return one
                    devices = devices.filter(Device.name == name)
                if ip is not None:
                    # Search devices by IP, should only return one
                    devices = devices.filter(Device.floatingIpAddr == ip)

                devices.all()

                for item in devices:
                    dev = item._asdict()
                    if dev['vip']:
                        dev['vip'] = [{
                            "id": dev['vipid'],
                            "address": str(ipaddress.IPv4Address(dev['vip']))
                        }]
                    else:
                        dev['vip'] = []
                    del(dev['vipid'])
                    device['devices'].append(dev)
            else:
                #  return device detail
                device = session.query(
                    Device.id, Device.az, Device.updated, Device.created,
                    Device.status, Device.floatingIpAddr.label('ip'),
                    Device.name, Device.type, Vip.id.label('vipid'),
                    Vip.ip.label('vip')
                ).outerjoin(Device.vip).filter(Device.id == device_id).first()

                if not device:
                    response.status = 404
                    session.rollback()
                    return dict(
                        faultcode="Client",
                        faultstring="device id " + device_id + "not found"
                    )

                device = device._asdict()
                if device['vip']:
                    device['vip'] = [{
                    "id": device['vipid'],
                        "address": str(ipaddress.IPv4Address(device['vip']))
                    }]
                else:
                    device['vip'] = []
                del(device['vipid'])

                device['loadBalancers'] = []

                if device['status'] != "OFFLINE":
                    lbids = session.query(
                        loadbalancers_devices.c.loadbalancer).\
                        filter(
                            loadbalancers_devices.c.device == device['id']
                        ).\
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

    @expose('json')
    def delete(self, device_id):
        """ Deletes a given device
        :param device_id: id of device to delete
        Urls:
           DELETE   /devices/{device_id}
        Returns: None
        """

        if not tenant_is_admin(request.headers):
            response.status = 401
            return dict(
                faultcode="Client",
                faultstring="Client not authorized to access this function"
            )

        with db_session() as session:
            # check for the device
            device = session.query(Device.id).\
                filter(Device.id == device_id).first()

            if device is None:
                session.rollback()
                response.status = 404
                return dict(
                    faultcode="Client",
                    faultstring="Device " + device_id + " not found"
                )

            # Is the device is attached to a LB
            lb = session.query(
                loadbalancers_devices.c.loadbalancer).\
                filter(loadbalancers_devices.c.device == device_id).\
                all()

            if lb:
                # Rebuild device
                resp = rebuild_device(device_id)
                response.status = resp[0]
                return resp[1]
            # If we get here there are no load balancers so delete device
            response.status = 204
            try:
                device = session.query(Device).\
                    filter(Device.id == device_id).first()
                device.status = 'DELETED'
                session.commit()
                return None
            except:
                session.rollback()
                LOG.exception('Error deleting device from pool')
                response.status = 500
                return dict(
                    faultcode="Server",
                    faultstring="Error deleting device from pool"
                )
            return None

    def discover(self, device_id):
        """
        Discovers information about a given libra worker based on device ID
        """

        if not tenant_is_user(request.headers):
            response.status = 401
            return dict(
                faultcode="Client",
                faultstring="Client not authorized to access this function"
            )

        with db_session() as session:
            device = session.query(Device.name).\
                filter(Device.id == device_id).scalar()
            device_name = str(device)
            session.commit()
        if device_name is None:
            response.status = 404
            return dict(
                faultcode="Client",
                faultstring="Device " + device_id + " not found"
            )
        gearman = GearJobs()
        discover = gearman.get_discover(device_name)
        if discover is None:
            response.status = 500
            return dict(
                faultcode="Server",
                faultstring="Could not discover device"
            )
        return dict(
            id=device_id, version=discover['version'],
            release=discover['release']
        )
