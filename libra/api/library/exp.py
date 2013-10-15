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

import six
from wsme.exc import ClientSideError
from wsme.utils import _


class IPOutOfRange(Exception):
    pass


class NotFound(ClientSideError):
    def __init__(self, msg=''):
        self.msg = msg
        super(NotFound, self).__init__()

    @property
    def faultstring(self):
        return _(six.u("NotFound: %s")) % (self.msg)


class OverLimit(ClientSideError):
    def __init__(self, msg=''):
        self.msg = msg
        super(OverLimit, self).__init__()

    @property
    def faultstring(self):
        return _(six.u("OverLimit: %s")) % (self.msg)


class NotAuthorized(ClientSideError):
    def __init__(self, msg=''):
        self.msg = msg
        super(NotAuthorized, self).__init__()

    @property
    def faultstring(self):
        return _(six.u("NotAuthorized: %s")) % (self.msg)


class ImmutableEntity(ClientSideError):
    def __init__(self, msg=''):
        self.msg = msg
        super(ImmutableEntity, self).__init__()

    @property
    def faultstring(self):
        return _(six.u("ImmutableEntity: %s")) % (self.msg)

ImmutableStates = [
    'ERROR', 'PENDING_UPDATE', 'PENDING_DELETE', 'BUILD', 'ERROR(REBUILDING)'
]
