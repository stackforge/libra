#!/usr/bin/env python
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

import json
from gearman import GearmanWorker, DataEncoder


class JSONDataEncoder(DataEncoder):
    """ Class to transform data that the worker either receives or sends. """

    @classmethod
    def encode(cls, encodable_object):
        """ Encode JSON object as string """
        return json.dumps(encodable_object)

    @classmethod
    def decode(cls, decodable_string):
        """ Decode string to JSON object """
        return json.loads(decodable_string)


class JSONGearmanWorker(GearmanWorker):
    """ Overload the Gearman worker class so we can set the data encoder. """
    data_encoder = JSONDataEncoder
