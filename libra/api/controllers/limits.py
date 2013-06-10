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

from pecan import expose
from pecan.rest import RestController
from libra.api.model.lbaas import Limits, get_session


class LimitsController(RestController):
    @expose('json')
    def get(self):
        resp = {}
        session = get_session()
        limits = session.query(Limits).all()
        for limit in limits:
            resp[limit.name] = limit.value

        resp = {"limits": {"absolute": {"values": resp}}}
        session.rollback()
        return resp
