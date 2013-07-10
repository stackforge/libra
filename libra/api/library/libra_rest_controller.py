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

import logging
from pecan.rest import RestController
from pecan.core import request, abort
from pecan.decorators import expose
from inspect import getargspec
from webob import exc
from sqlalchemy.exc import OperationalError


class LibraController(RestController):
    routing_calls = 0

    @expose()
    def _route(self, args):
        '''
        Routes a request to the appropriate controller and returns its result.

        Performs a bit of validation - refuses to route delete and put actions
        via a GET request).
        '''
        # convention uses "_method" to handle browser-unsupported methods
        if request.environ.get('pecan.validation_redirected', False) is True:
            #
            # If the request has been internally redirected due to a validation
            # exception, we want the request method to be enforced as GET, not
            # the `_method` param which may have been passed for REST support.
            #
            method = request.method.lower()
        else:
            method = request.params.get('_method', request.method).lower()

        # make sure DELETE/PUT requests don't use GET
        if request.method == 'GET' and method in ('delete', 'put'):
            abort(405)

        # check for nested controllers
        result = self._find_sub_controllers(args)
        if result:
            return result

        # handle the request
        handler = getattr(self, '_handle_%s' % method, self._handle_custom)

        try:
            result = handler(method, args)

            #
            # If the signature of the handler does not match the number
            # of remaining positional arguments, attempt to handle
            # a _lookup method (if it exists)
            #
            argspec = getargspec(result[0])
            num_args = len(argspec[0][1:])
            if num_args < len(args):
                _lookup_result = self._handle_lookup(args)
                if _lookup_result:
                    return _lookup_result
        except exc.HTTPNotFound:
            #
            # If the matching handler results in a 404, attempt to handle
            # a _lookup method (if it exists)
            #
            _lookup_result = self._handle_lookup(args)
            if _lookup_result:
                return _lookup_result
        except OperationalError as sqlexc:
            logger = logging.getLogger(__name__)
            # if a galera transaction fails due to locking, retry the call
            if sqlexc.args[0] == 1213 and LibraController.routing_calls < 5:
                LibraController.routing_calls += 1
                logger.warning("Galera deadlock, retry: {0}".format(
                    LibraController.routing_calls)
                )
                result = self._route(args)
            else:
                raise

        LibraController.routing_calls = 0
        # return the result
        return result
