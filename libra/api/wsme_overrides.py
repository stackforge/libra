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
import traceback
import functools
import inspect
import sys
import json

import wsme
import wsme.rest.args
import wsme.rest.json
import wsme.rest.xml
import wsmeext.pecan
import pecan
from libra.api.library.exp import OverLimit, NotFound
from wsme.rest.json import tojson
from sqlalchemy.exc import OperationalError, ResourceClosedError


def format_exception(excinfo, debug=False):
    """Extract informations that can be sent to the client."""
    error = excinfo[1]
    log = logging.getLogger(__name__)
    if isinstance(error, wsme.exc.ClientSideError):
        r = dict(message="Bad Request",
                 details=error.faultstring)
        log.warning("Client-side error: %s" % r['details'])
        return r
    else:
        faultstring = str(error)
        debuginfo = "\n".join(traceback.format_exception(*excinfo))

        log.error('Server-side error: "%s". Detail: \n%s' % (
            faultstring, debuginfo))

        if isinstance(error, ValueError):
            r = dict(message="Bad Request", details=faultstring)
        else:
            r = dict(message="Load Balancer Fault", details=faultstring)
        if debug:
            r['debuginfo'] = debuginfo
        return r

wsme.api.format_exception = format_exception


def encode_result(value, datatype, **options):
    jsondata = tojson(datatype, value)
    if options.get('nest_result', False):
        jsondata = {options.get('nested_result_attrname', 'result'): jsondata}
    if jsondata:
        return json.dumps(jsondata)
    else:
        return ''

wsme.rest.json.encode_result = encode_result


def wsexpose(*args, **kwargs):
    pecan_json_decorate = pecan.expose(
        template='wsmejson:',
        content_type='application/json',
        generic=False)
    pecan_xml_decorate = pecan.expose(
        template='wsmexml:',
        content_type='application/xml',
        generic=False
    )
    sig = wsme.signature(*args, **kwargs)

    def decorate(f):
        sig(f)
        funcdef = wsme.api.FunctionDefinition.get(f)
        funcdef.resolve_types(wsme.types.registry)

        @functools.wraps(f)
        def callfunction(self, *args, **kwargs):
            for x in xrange(5):
                old_args = args
                old_kwargs = kwargs
                try:
                    args, kwargs = wsme.rest.args.get_args(
                        funcdef, args, kwargs, pecan.request.params, None,
                        pecan.request.body, pecan.request.content_type
                    )
                    if funcdef.pass_request:
                        kwargs[funcdef.pass_request] = pecan.request
                    result = f(self, *args, **kwargs)

                    # NOTE: Support setting of status_code with default 201
                    pecan.response.status = funcdef.status_code
                    if isinstance(result, wsme.api.Response):
                        pecan.response.status = result.status_code
                        result = result.obj

                # ResourceClosedError happens on for_update deadlock
                except (OperationalError, ResourceClosedError):
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        "Galera deadlock, retry {0}".format(x+1)
                    )
                    args = old_args
                    kwargs = old_kwargs
                    continue
                except:
                    data = wsme.api.format_exception(
                        sys.exc_info(),
                        pecan.conf.get('wsme', {}).get('debug', False)
                    )
                    e = sys.exc_info()[1]
                    if isinstance(e, OverLimit):
                        pecan.response.status = 413
                    if isinstance(e, NotFound):
                        pecan.response.status = 404
                    elif data['message'] == 'Bad Request':
                        pecan.response.status = 400
                    else:
                        pecan.response.status = 500
                    return data

                return dict(
                    datatype=funcdef.return_type,
                    result=result
                )
            # After 5 retries of transaction, give up!
            data = wsme.api.format_exception(
                sys.exc_info(),
                pecan.conf.get('wsme', {}).get('debug', False)
            )
            pecan.response.status = 500
            return data

        pecan_xml_decorate(callfunction)
        pecan_json_decorate(callfunction)
        pecan.util._cfg(callfunction)['argspec'] = inspect.getargspec(f)
        callfunction._wsme_definition = funcdef
        return callfunction

    return decorate

wsmeext.pecan.wsexpose = wsexpose


class JSonRenderer(object):
    def __init__(self, path, extra_vars):
        pass

    def render(self, template_path, namespace):
        if 'message' in namespace:
            return wsme.rest.json.encode_error(None, namespace)
        return wsme.rest.json.encode_result(
            namespace['result'],
            namespace['datatype']
        )

pecan.templating._builtin_renderers['wsmejson'] = JSonRenderer
