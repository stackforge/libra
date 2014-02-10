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

from pecan import expose
from pecan.rest import RestController
from libra.common.api.lbaas import Ports, db_session


class ProtocolsController(RestController):
    @expose('json')
    def get(self):
        protocols = []
        with db_session() as session:
            ports = session.query(Ports.protocol, Ports.portnum).\
                filter(Ports.enabled == 1).all()
            for item in ports:
                data = {}
                item = item._asdict()
                data["name"] = item["protocol"]
                data["port"] = item["portnum"]
                protocols.append(data)

            resp = {"protocols": protocols}
            session.rollback()
            return resp
