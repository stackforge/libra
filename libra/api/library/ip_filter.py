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

import ipaddress
from libra.api.library.exp import IPOutOfRange


def ipfilter(address, masks):
    address = ipaddress.IPv4Address(address)
    if masks and len(masks) > 0:
        in_mask = False
        for mask in masks:
            if address in ipaddress.IPv4Network(unicode(mask), True):
                in_mask = True
                break
        if not in_mask:
            raise IPOutOfRange('IP Address not in mask')
    return str(address)
