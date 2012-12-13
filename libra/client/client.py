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

from libraapi import LibraAPI
from clientoptions import ClientOptions
from novaclient import exceptions


def main():
    options = ClientOptions()
    args = options.run()

    api = LibraAPI(args.os_username, args.os_password, args.os_tenant_name,
                   args.os_auth_url, args.os_region_name, args.insecure,
                   args.debug, args.bypass_url)

    cmd = args.command.replace('-', '_')
    method = getattr(api, '{cmd}_lb'.format(cmd=cmd))

    try:
        method(args)
    except exceptions.ClientException as exc:
        print exc

    return 0
