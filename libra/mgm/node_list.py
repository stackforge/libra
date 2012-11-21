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

import pickle
import os


class AccessDenied(Exception):
    pass


class NodeList(object):
    def __init__(self, path):
        if not os.access(path, os.W_OK):
            msg = 'Do not have permission to write to {0}'.format(path)
            raise AccessDenied(msg)

        self.file_name = '{0}/node_log.dat'.format(path)

    def add(self, item):
        data = self.get()
        data.append(item)
        self.put(data)

    def delete(self, item):
        data = self.get()
        data.remove(item)
        self.put(data)

    def get(self):
        # Attribute error is thrown if file is non-existent
        try:
            return pickle.load(open(self.file_name, "rb"))
        except IOError:
            return []

    def put(self, data):
        pickle.dump(data, open(self.file_name, "wb"))
