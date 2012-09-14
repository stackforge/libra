# Copyright 2012 Hewlett-Packard Development Company, L.P.
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

from json import dumps


class ServiceFault(object):
    def __init__(self, code, message, details):
        self.code = code
        self.message = message
        self.details = details

    def to_json(self):
        data = {
            "serviceFault": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }
        return data

    def __str__(self):
        return json.dumps(self.to_json(), indent=4)


class BadRequest(ServiceFault):
    def __init__(self,
                 validation_errors,
                 code="400",
                 message="Validation fault",
                 details="The object is not valid"):
        ServiceFault.__init__(self, code, message, details)
        self.validation_errors = validation_errors

    def to_json(self):
        data = {
            "badRequest": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "validationErrors": {
                    "message": self.validation_errors
                }
            }
        }
        return data

    def __str__(self):
        return json.dumps(self.to_json(), indent=4)
