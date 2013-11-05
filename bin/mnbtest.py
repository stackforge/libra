#!/usr/bin/env python
##############################################################################
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################
import logging
import time

from libra import admin_api
from oslo.config import cfg
from libra.common.options import libra_logging, CONF
from libra.common.options import common_cli_opts, common_opts
from libra import __version__

admin_api.adminapi_group  # Needed for tox
CONF.register_cli_opts(common_opts)
CONF.register_cli_opts(common_cli_opts)
CONF.unregister_opt(cfg.BoolOpt('debug'))
CONF.unregister_opt(cfg.BoolOpt('verbose'))

from libra.common.api.mnb import update_mnb
CONF(project='mnbtest', version=__version__)


def main():
    logger = libra_logging('', 'admin_api')
    logger.setLevel(level=logging.INFO)
    logger.info('STARTING MNBTEST')

    for x in xrange(1, 11):
        try:
            #Notify billing of the LB creation
            update_mnb('lbaas.instance.test', 123, 456)
        except Exception:
            logger.exception('Uncaught exception during MnB exists')
            print "EXCEPTION"
            pass

    time.sleep(3)

if __name__ == "__main__":
    main()
