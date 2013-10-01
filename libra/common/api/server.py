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
import eventlet


def make_socket(args):
    sock = eventlet.listen((args.host, args.port))
    # TODO: set ca_certs and cert_reqs=CERT_REQUIRED
    if args.ssl_keyfile and args.ssl_certfile:
        sock = eventlet.wrap_ssl(sock, certfile=args.ssl_certfile,
                                 keyfile=args.ssl_keyfile,
                                 server_side=True)
    return sock
