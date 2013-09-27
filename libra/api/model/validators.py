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


class LBNode(Base):
    port = wsattr(int, mandatory=True)
    address = wsattr(wtypes.text, mandatory=True)
    condition = Enum(wtypes.text, 'ENABLED', 'DISABLED')
    backup = Enum(wtypes.text, 'TRUE', 'FALSE')


class LBRespNode(Base):
    port = wtypes.text
    address = wtypes.text
    condition = wtypes.text


class LBNodePut(Base):
    condition = Enum(wtypes.text, 'ENABLED', 'DISABLED', mandatory=True)


class NodeResp(Base):
    id = int
    address = wtypes.text
    port = int
    condition = wtypes.text
    status = wtypes.text


class LBNodePost(Base):
    nodes = wsattr(['LBNode'], mandatory=True)


class LBNodeResp(Base):
    nodes = wsattr(['NodeResp'])


class LBVip(Base):
    id = wsattr(int, mandatory=True)


class LBPost(Base):
    name = wsattr(wtypes.text, mandatory=True)
    nodes = wsattr(['LBNode'], mandatory=True)
    protocol = wtypes.text
    algorithm = Enum(wtypes.text, 'ROUND_ROBIN', 'LEAST_CONNECTIONS')
    port = int
    virtualIps = wsattr(['LBVip'])


class LBPut(Base):
    name = wtypes.text
    algorithm = Enum(wtypes.text, 'ROUND_ROBIN', 'LEAST_CONNECTIONS')


class LBVipResp(Base):
    id = wtypes.text
    address = wtypes.text
    type = wtypes.text
    ipVersion = wtypes.text


class LBLogsPost(Base):
    objectStoreType = Enum(wtypes.text, 'Swift')
    objectStoreEndpoint = wtypes.text
    objectStoreBasePath = wtypes.text
    authToken = wtypes.text


class LBResp(Base):
    id = wtypes.text
    name = wtypes.text
    protocol = wtypes.text
    port = wtypes.text
    algorithm = wtypes.text
    status = wtypes.text
    created = wtypes.text
    updated = wtypes.text
    virtualIps = wsattr(['LBVipResp'])
    nodes = wsattr(['LBRespNode'])


class LBMonitorPut(Base):
    type = Enum(wtypes.text, 'CONNECT', 'HTTP')
    delay = int
    timeout = int
    attemptsBeforeDeactivation = int
    path = wtypes.text


class LBMonitorResp(Base):
    type = wtypes.text
    delay = wtypes.text
    timeout = wtypes.text
    attemptsBeforeDeactivation = wtypes.text
    path = wtypes.text
