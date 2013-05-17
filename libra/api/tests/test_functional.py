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

#from unittest import TestCase
#from webtest import TestApp
from libra.api.tests import FunctionalTest


class TestRootController(FunctionalTest):

    def test_get(self):
        response = self.app.get('/', expect_errors=True)
        assert response.status_int == 404

    def test_search(self):
#       Lets get post sorted before enabling this
#        response = self.app.post('/', params={'q': 'RestController'})
#        assert response.status_int == 201
#        assert response.headers['Location'] == (
#            'http://pecan.readthedocs.org/en/latest/search.html'
#            '?q=RestController'
#        )
        pass

    def test_get_not_found(self):
        response = self.app.get('/a/bogus/url', expect_errors=True)
        assert response.status_int == 404
