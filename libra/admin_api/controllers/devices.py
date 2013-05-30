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
from pecan import expose  # , abort, response, request
from pecan.rest import RestController
import wsmeext.pecan as wsme_pecan
#from wsme.exc import ClientSideError
from libra.api_admin.model.validators import DeviceResp, DevicePost


class DevicesController(RestController):
    @expose('json')
    def get(self, device_id=None, marker=None, limit=None):
        """ Gets either a list of devices or a single device details
            device_id is supplied if we are getting details of a single device
            marker and limit are used to paginate when device_id is not
            supplied.  Currently this just supplies "LIMIT marker, limit" to
            MySQL which is fine.
        """
        pass

    @wsme_pecan.wsexpose(DeviceResp, body=DevicePost, status=202)
    def post(self, body=None):
        """ Post a new device, DeviceResp and DevicePost not complete yet
        """
        pass

    @wsme_pecan.wsexpose(DeviceResp, body=DevicePost, status=202)
    def put(self):
        """ Updates a device only accepts status and statusDescription """
        pass

    @expose('json')
    def delete(self, device_id):
        """ Deletes a given device """
        pass

    @expose('json')
    def usage(self):
        """ Returns usage stats """
        pass
