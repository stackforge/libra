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

from wsme import types as wtypes
from wsme import wsattr
from wsme.types import Base, Enum


class LB(Base):
    id = wsattr(int, mandatory=True)
    tenantid = wsattr(wtypes.text, mandatory=True)


class DevicePost(Base):
    name = wsattr(wtypes.text, mandatory=True)
    publicIpAddr = wsattr(wtypes.text, mandatory=True)
    floatingIpAddr = wsattr(wtypes.text, mandatory=True)
    az = wsattr(int, mandatory=True)
    type = wsattr(wtypes.text, mandatory=True)


class DeviceResp(Base):
    id = int
    name = wtypes.text
    floatingIpAddr = wtypes.text
    publicIpAddr = wtypes.text
    az = int
    type = wtypes.text
    created = wtypes.text
    updated = wtypes.text
    status = wtypes.text
    loadBalancers = wsattr(['LB'])


class DevicePut(Base):
    status = Enum(wtypes.text, 'ONLINE', 'ERROR')
    statusDescription = wsattr(wtypes.text, mandatory=True)
