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
from wsme.types import Base


class LBNode(Base):
    port = wsattr(int, mandatory=True)
    address = wsattr(wtypes.text, mandatory=True)
    condition = wtypes.text


class LBVip(Base):
    id = wsattr(int, mandatory=True)


class LBPost(Base):
    name = wsattr(wtypes.text, mandatory=True)
    nodes = wsattr(['LBNode'], mandatory=True)
    protocol = wtypes.text
    algorithm = wtypes.text
    port = int
    virtualIps = wsattr(['LBVip'])


class LBVipResp(Base):
    id = int
    address = wtypes.text
    type = wtypes.text
    ipVersion = wtypes.text


class LBResp(Base):
    id = int
    name = wtypes.text
    protocol = wtypes.text
    port = int
    algorithm = wtypes.text
    status = wtypes.text
    created = wtypes.text
    updated = wtypes.text
    virtualIps = wsattr(['LBVipResp'])
    nodes = wsattr(['LBNode'])
